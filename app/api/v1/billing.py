from typing import List
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.config import settings
from app.core.dependencies import get_current_organization, get_current_user, require_admin
from app.db.models import Organization, Plan, User
from app.db.session import get_db
from app.schemas.billing import (
    CheckoutSessionResponse,
    CreateCheckoutSessionRequest,
    PlanResponse,
    SubscriptionStatusResponse,
)
from app.services.billing_service import BillingService

router = APIRouter(prefix="/billing", tags=["Billing & Plans"])


@router.get("/plans", response_model=List[PlanResponse])
def get_plans(db: Session = Depends(get_db)):
    return BillingService.get_plans(db)


@router.get("/status", response_model=SubscriptionStatusResponse)
def get_subscription_status(
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    return BillingService.get_subscription_status(db, org)


@router.post("/checkout", response_model=CheckoutSessionResponse)
def create_checkout_session(
    req: CreateCheckoutSessionRequest,
    current_user: User = Depends(require_admin),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    return BillingService.create_checkout_session(
        db=db,
        org=org,
        plan_code=req.plan_code,
        billing_cycle=req.billing_cycle,
        success_url=req.success_url,
        cancel_url=req.cancel_url,
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db),
):
    """Handle Stripe asynchronous webhook events (subscription changes, payments)."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        return {"received": True, "notice": "Stripe webhook secret not configured"}

    import stripe

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Webhook error: {str(e)}"
        )

    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type == "checkout.session.completed":
        org_id = data_object.get("metadata", {}).get("organization_id")
        plan_code = data_object.get("metadata", {}).get("plan_code")
        if org_id and plan_code:
            org = db.query(Organization).filter(Organization.id == int(org_id)).first()
            plan = db.query(Plan).filter(Plan.code == plan_code).first()
            if org and plan:
                org.plan_id = plan.id
                org.subscription_status = "active"
                org.stripe_customer_id = data_object.get("customer")
                org.stripe_subscription_id = data_object.get("subscription")
                db.commit()

    elif event_type == "customer.subscription.deleted":
        sub_id = data_object.get("id")
        org = (
            db.query(Organization)
            .filter(Organization.stripe_subscription_id == sub_id)
            .first()
        )
        if org:
            free_plan = db.query(Plan).filter(Plan.code == "free").first()
            if free_plan:
                org.plan_id = free_plan.id
            org.subscription_status = "canceled"
            db.commit()

    return {"status": "success", "event": event_type}

