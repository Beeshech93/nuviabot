from typing import Any, Dict, List, Optional
import stripe
from sqlalchemy.orm import Session
from app.config import settings
from app.core.exceptions import PlanLimitExceededException
from app.db.models import ClientWorkspace, Organization, Plan, Post, SocialAccount, User
from app.schemas.billing import (
    CheckoutSessionResponse,
    PlanResponse,
    SubscriptionStatusResponse,
)


class BillingService:
    DEFAULT_PLANS = [
        {
            "name": "Free",
            "code": "free",
            "price_monthly": 0.0,
            "price_annual": 0.0,
            "max_social_accounts": 1,
            "max_posts_per_month": 15,
            "max_ai_credits": 25,
            "max_clients": 1,
            "max_team_members": 1,
            "features": [
                "1 Social Account",
                "15 Posts per Month",
                "Basic AI Caption Generator",
                "Draft & Manual Publishing",
                "Community Support",
            ],
        },
        {
            "name": "Starter",
            "code": "starter",
            "price_monthly": 29.0,
            "price_annual": 290.0,
            "max_social_accounts": 3,
            "max_posts_per_month": 75,
            "max_ai_credits": 150,
            "max_clients": 1,
            "max_team_members": 2,
            "features": [
                "3 Social Accounts",
                "75 Posts per Month",
                "Full AI Content Studio (ES, EN, HT)",
                "Content Calendar & Scheduling",
                "Human Approval Flow",
                "Standard Analytics",
            ],
        },
        {
            "name": "Pro",
            "code": "pro",
            "price_monthly": 79.0,
            "price_annual": 790.0,
            "max_social_accounts": 10,
            "max_posts_per_month": 300,
            "max_ai_credits": 600,
            "max_clients": 3,
            "max_team_members": 5,
            "features": [
                "10 Social Accounts",
                "300 Posts per Month",
                "Advanced AI Studio & Strategy",
                "Cross-Platform Analytics & CSV Export",
                "Automated Publishing Engine",
                "Multi-Client Workspaces (Up to 3)",
                "Priority Support",
            ],
        },
        {
            "name": "Agency",
            "code": "agency",
            "price_monthly": 199.0,
            "price_annual": 1990.0,
            "max_social_accounts": 35,
            "max_posts_per_month": 1500,
            "max_ai_credits": 2500,
            "max_clients": 20,
            "max_team_members": 15,
            "features": [
                "35 Social Accounts",
                "1,500 Posts per Month",
                "Unlimited Client Workspaces (Up to 20)",
                "Full Team RBAC & Approvals",
                "White-label Branding & Logo",
                "Dedicated Account Manager",
                "Custom Integrations",
            ],
        },
    ]

    @staticmethod
    def seed_plans(db: Session):
        """Seed default plans if not already present."""
        for p_data in BillingService.DEFAULT_PLANS:
            existing = db.query(Plan).filter(Plan.code == p_data["code"]).first()
            if not existing:
                plan = Plan(
                    name=p_data["name"],
                    code=p_data["code"],
                    price_monthly=p_data["price_monthly"],
                    price_annual=p_data["price_annual"],
                    max_social_accounts=p_data["max_social_accounts"],
                    max_posts_per_month=p_data["max_posts_per_month"],
                    max_ai_credits=p_data["max_ai_credits"],
                    max_clients=p_data["max_clients"],
                    max_team_members=p_data["max_team_members"],
                    features=p_data["features"],
                )
                db.add(plan)
        db.commit()

    @staticmethod
    def get_plans(db: Session) -> List[PlanResponse]:
        plans = db.query(Plan).all()
        if not plans:
            BillingService.seed_plans(db)
            plans = db.query(Plan).all()
        return [PlanResponse.model_validate(p) for p in plans]

    @staticmethod
    def get_subscription_status(db: Session, org: Organization) -> SubscriptionStatusResponse:
        plan = org.plan
        if not plan:
            plan = db.query(Plan).filter(Plan.code == "free").first()
            if not plan:
                BillingService.seed_plans(db)
                plan = db.query(Plan).filter(Plan.code == "free").first()

        # Count active accounts
        acc_count = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.organization_id == org.id,
                SocialAccount.status == "connected",
            )
            .count()
        )
        team_count = db.query(User).filter(User.organization_id == org.id).count()
        client_count = (
            db.query(ClientWorkspace).filter(ClientWorkspace.organization_id == org.id).count()
        )

        stripe_ready = bool(settings.STRIPE_SECRET_KEY)

        return SubscriptionStatusResponse(
            plan_name=plan.name,
            plan_code=plan.code,
            status=org.subscription_status,
            is_active=org.subscription_status in ["active", "trialing"],
            current_period_end=None,
            social_accounts_used=acc_count,
            social_accounts_limit=plan.max_social_accounts,
            posts_published_this_month=org.posts_published_this_month or 0,
            posts_limit=plan.max_posts_per_month,
            ai_credits_used=org.ai_credits_used_this_month or 0,
            ai_credits_limit=plan.max_ai_credits,
            team_members_count=team_count,
            team_members_limit=plan.max_team_members,
            clients_count=client_count,
            clients_limit=plan.max_clients,
            stripe_configured=stripe_ready,
        )

    @staticmethod
    def check_can_add_social_account(db: Session, org: Organization):
        plan = org.plan or db.query(Plan).filter(Plan.code == "free").first()
        current_count = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.organization_id == org.id,
                SocialAccount.status == "connected",
            )
            .count()
        )
        if current_count >= plan.max_social_accounts:
            raise PlanLimitExceededException(
                "Social Accounts", plan.max_social_accounts
            )

    @staticmethod
    def check_can_publish_post(db: Session, org: Organization):
        plan = org.plan or db.query(Plan).filter(Plan.code == "free").first()
        if (org.posts_published_this_month or 0) >= plan.max_posts_per_month:
            raise PlanLimitExceededException("Monthly Posts", plan.max_posts_per_month)

    @staticmethod
    def check_can_use_ai_credits(db: Session, org: Organization, credits: int = 1):
        plan = org.plan or db.query(Plan).filter(Plan.code == "free").first()
        if (org.ai_credits_used_this_month or 0) + credits > plan.max_ai_credits:
            raise PlanLimitExceededException("AI Studio Credits", plan.max_ai_credits)

    @staticmethod
    def check_can_add_client(db: Session, org: Organization):
        plan = org.plan or db.query(Plan).filter(Plan.code == "free").first()
        current_count = (
            db.query(ClientWorkspace).filter(ClientWorkspace.organization_id == org.id).count()
        )
        if current_count >= plan.max_clients:
            raise PlanLimitExceededException("Client Workspaces", plan.max_clients)

    @staticmethod
    def check_can_add_team_member(db: Session, org: Organization):
        plan = org.plan or db.query(Plan).filter(Plan.code == "free").first()
        current_count = db.query(User).filter(User.organization_id == org.id).count()
        if current_count >= plan.max_team_members:
            raise PlanLimitExceededException("Team Seats", plan.max_team_members)

    @staticmethod
    def create_checkout_session(
        db: Session,
        org: Organization,
        plan_code: str,
        billing_cycle: str = "monthly",
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> CheckoutSessionResponse:
        plan = db.query(Plan).filter(Plan.code == plan_code).first()
        if not plan:
            raise ValueError(f"Plan with code '{plan_code}' not found.")

        # If Stripe is not configured or in sandbox testing:
        if not settings.STRIPE_SECRET_KEY:
            # Provide mock sandbox activation url
            return CheckoutSessionResponse(
                checkout_url=f"/#billing?checkout_success={plan_code}",
                session_id=f"mock_cs_{plan_code}_{org.id}",
                is_mock=True,
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY
        price = plan.price_annual if billing_cycle == "annual" else plan.price_monthly

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Nuvio Growth Bot - {plan.name} Plan",
                            "description": f"{plan.name} Tier ({billing_cycle})",
                        },
                        "unit_amount": int(price * 100),
                        "recurring": {
                            "interval": "year" if billing_cycle == "annual" else "month"
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=success_url or "http://localhost:8000/#billing?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url or "http://localhost:8000/#billing?canceled=true",
            metadata={"organization_id": str(org.id), "plan_code": plan_code},
        )

        return CheckoutSessionResponse(
            checkout_url=session.url,
            session_id=session.id,
            is_mock=False,
        )

