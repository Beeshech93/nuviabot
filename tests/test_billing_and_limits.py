import pytest
from app.core.exceptions import PlanLimitExceededException
from app.db.models import Organization, Plan
from app.services.billing_service import BillingService


def test_get_plans_endpoint(client):
    res = client.get("/api/v1/billing/plans")
    assert res.status_code == 200
    plans = res.json()
    assert len(plans) >= 4
    codes = [p["code"] for p in plans]
    assert "free" in codes
    assert "starter" in codes
    assert "pro" in codes
    assert "agency" in codes


def test_subscription_status(client, auth_headers):
    res = client.get("/api/v1/billing/status", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["plan_code"] == "pro"
    assert data["is_active"] is True
    assert data["social_accounts_limit"] >= 10


def test_plan_limits_enforcement(db):
    free_plan = db.query(Plan).filter(Plan.code == "free").first()
    test_org = Organization(
        name="Limited Org",
        slug="limited-org",
        plan_id=free_plan.id,
        subscription_status="active",
        posts_published_this_month=15,  # Free limit is 15
        ai_credits_used_this_month=25,  # Free limit is 25
    )
    db.add(test_org)
    db.commit()

    # Post limit should trigger exception
    with pytest.raises(PlanLimitExceededException):
        BillingService.check_can_publish_post(db, test_org)

    # AI credit limit should trigger exception
    with pytest.raises(PlanLimitExceededException):
        BillingService.check_can_use_ai_credits(db, test_org, credits=1)

