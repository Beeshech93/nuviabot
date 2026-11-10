from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.security import encrypt_token, hash_password
from app.db.models import (
    AnalyticsMetric,
    ApprovalLog,
    ClientWorkspace,
    MediaAsset,
    Organization,
    Plan,
    Post,
    SocialAccount,
    User,
)
from app.db.session import SessionLocal, engine
from app.services.billing_service import BillingService


def seed_database(db: Session):
    print("🌱 Seeding database with production initial state and demo fixtures...")

    # 1. Seed Plans
    BillingService.seed_plans(db)
    pro_plan = db.query(Plan).filter(Plan.code == "pro").first()
    free_plan = db.query(Plan).filter(Plan.code == "free").first()

    # 2. Check if primary organization exists
    org = db.query(Organization).filter(Organization.slug == "nuvio-growth-hq").first()
    if not org:
        org = Organization(
            name="Nuvio Growth Agency",
            slug="nuvio-growth-hq",
            industry="Marketing & Media",
            logo_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200",
            timezone="America/New_York",
            default_language="es",
            plan_id=pro_plan.id if pro_plan else None,
            subscription_status="active",
            auto_publish_enabled=False,
            ai_credits_used_this_month=14,
            posts_published_this_month=28,
        )
        db.add(org)
        db.commit()
        db.refresh(org)

    # 3. Seed Users
    admin_user = db.query(User).filter(User.email == "admin@nuviogrowth.com").first()
    if not admin_user:
        admin_user = User(
            organization_id=org.id,
            email="admin@nuviogrowth.com",
            hashed_password=hash_password("NuvioGrowth2026!"),
            full_name="Alex Rivera",
            role="agency_admin",
            is_active=True,
            language="es",
            timezone="America/New_York",
            avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100",
        )
        db.add(admin_user)

    editor_user = db.query(User).filter(User.email == "editor@nuviogrowth.com").first()
    if not editor_user:
        editor_user = User(
            organization_id=org.id,
            email="editor@nuviogrowth.com",
            hashed_password=hash_password("NuvioGrowth2026!"),
            full_name="Sophia Chen",
            role="editor",
            is_active=True,
            language="es",
            timezone="America/New_York",
            avatar_url="https://images.unsplash.com/photo-1517841905240-472988babdf9?w=100",
        )
        db.add(editor_user)

    db.commit()
    db.refresh(admin_user)
    db.refresh(editor_user)

    # 4. Seed Clients Workspaces
    client_1 = db.query(ClientWorkspace).filter(ClientWorkspace.name == "Aura Luxe Cosmetics").first()
    if not client_1:
        client_1 = ClientWorkspace(
            organization_id=org.id,
            name="Aura Luxe Cosmetics",
            industry="Beauty & Fashion",
            logo_url="https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=100",
            notes="Global organic skincare brand. Focus on TikTok and Instagram Reels.",
            is_active=True,
        )
        db.add(client_1)

    client_2 = db.query(ClientWorkspace).filter(ClientWorkspace.name == "HyperTech SaaS").first()
    if not client_2:
        client_2 = ClientWorkspace(
            organization_id=org.id,
            name="HyperTech SaaS",
            industry="Technology & Software",
            logo_url="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=100",
            notes="B2B AI analytics platform. Focus on YouTube educational tutorials & Facebook.",
            is_active=True,
        )
        db.add(client_2)

    db.commit()

    # 5. Seed Connected Social Accounts
    social_accounts_data = [
        {
            "platform": "instagram",
            "account_id": "17841405829102931",
            "username": "nuviogrowth_official",
            "display_name": "Nuvio Growth | AI Social Media",
            "picture": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150",
            "followers": 14850,
            "following": 320,
            "posts": 142,
        },
        {
            "platform": "facebook",
            "account_id": "100982348123456",
            "username": "nuviogrowth_page",
            "display_name": "Nuvio Growth Platform",
            "picture": "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=150",
            "followers": 9240,
            "following": 45,
            "posts": 88,
        },
        {
            "platform": "tiktok",
            "account_id": "tt_creator_9812",
            "username": "nuviogrowth_tips",
            "display_name": "Nuvio Growth Hacks",
            "picture": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
            "followers": 48200,
            "following": 112,
            "posts": 210,
        },
        {
            "platform": "youtube",
            "account_id": "UC_nuvio_growth_channel_id",
            "username": "NuvioOfficial",
            "display_name": "Nuvio AI Growth Academy",
            "picture": "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150",
            "followers": 22400,
            "following": 14,
            "posts": 65,
        },
    ]

    created_accounts = []
    for s_data in social_accounts_data:
        acc = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.organization_id == org.id,
                SocialAccount.platform == s_data["platform"],
            )
            .first()
        )
        if not acc:
            acc = SocialAccount(
                organization_id=org.id,
                platform=s_data["platform"],
                platform_account_id=s_data["account_id"],
                username=s_data["username"],
                display_name=s_data["display_name"],
                profile_picture_url=s_data["picture"],
                encrypted_access_token=encrypt_token("mock_demo_verified_token"),
                encrypted_refresh_token=encrypt_token("mock_demo_refresh_token"),
                status="connected",
                followers_count=s_data["followers"],
                following_count=s_data["following"],
                posts_count=s_data["posts"],
                last_synced_at=datetime.now(timezone.utc),
            )
            db.add(acc)
            created_accounts.append(acc)
        else:
            created_accounts.append(acc)

    db.commit()

    # 6. Seed Analytics Metrics for past 14 days
    today = date.today()
    for acc in created_accounts:
        for i in range(14):
            m_date = today - timedelta(days=14 - i)
            existing_m = (
                db.query(AnalyticsMetric)
                .filter(
                    AnalyticsMetric.social_account_id == acc.id,
                    AnalyticsMetric.metric_date == m_date,
                )
                .first()
            )
            if not existing_m:
                base_views = 800 + (i * 120)
                base_imp = base_views + 450
                likes = int(base_imp * 0.05)
                comments = int(likes * 0.15)
                shares = int(likes * 0.08)
                metric = AnalyticsMetric(
                    organization_id=org.id,
                    social_account_id=acc.id,
                    platform=acc.platform,
                    metric_date=m_date,
                    followers=acc.followers_count + (i * 25),
                    impressions=base_imp,
                    reach=int(base_imp * 0.78),
                    views=base_views,
                    likes=likes,
                    comments=comments,
                    shares=shares,
                    engagement_rate=round(((likes + comments + shares) / base_imp) * 100, 2),
                )
                db.add(metric)

    db.commit()

    # 7. Seed Sample Posts
    p1 = db.query(Post).filter(Post.title == "Lanzamiento de Campaña AI 2026").first()
    if not p1:
        p1 = Post(
            organization_id=org.id,
            author_id=admin_user.id,
            title="Lanzamiento de Campaña AI 2026",
            content="🚀 Automatiza y escala tu presencia digital con Nuvio Growth Bot.\n\nContenido inteligente, aprobaciones en 1 clic y estadísticas reales.\n\n#SaaS #GrowthMarketing #AI #Nuvio",
            target_platforms=["instagram", "facebook"],
            status="published",
            published_at=datetime.now(timezone.utc) - timedelta(days=2),
            platform_post_ids={"instagram": "ig_182930491", "facebook": "fb_94820194"},
        )
        db.add(p1)

    p2 = db.query(Post).filter(Post.title == "3 Estrategias de Retención Orgánica").first()
    if not p2:
        future_date = datetime.now(timezone.utc) + timedelta(days=2, hours=3)
        p2 = Post(
            organization_id=org.id,
            author_id=editor_user.id,
            title="3 Estrategias de Retención Orgánica",
            content="💡 El crecimiento real no viene de seguidores falsos, viene de valor continuo.\n\n1. Responde a cada comentario en menos de 1 hora.\n2. Analiza tus mejores publicaciones.\n3. Mantén un calendario de contenido constante.\n\n#SocialMediaStrategy #MarketingTips",
            target_platforms=["tiktok", "instagram"],
            status="scheduled",
            scheduled_at=future_date,
        )
        db.add(p2)

    p3 = db.query(Post).filter(Post.title == "Reel: Detrás de Cámaras Nuvio").first()
    if not p3:
        p3 = Post(
            organization_id=org.id,
            author_id=editor_user.id,
            title="Reel: Detrás de Cámaras Nuvio",
            content="🔥 Un vistazo exclusivo a cómo nuestro equipo entrena modelos para generar copy viral en Español, Inglés y Kreyòl.\n\n¿Qué red social te genera mejores clientes hoy?",
            target_platforms=["instagram", "tiktok"],
            status="pending_approval",
        )
        db.add(p3)
        db.flush()

        # Add approval log
        log = ApprovalLog(
            post_id=p3.id,
            user_id=editor_user.id,
            action="submitted",
            comments="Por favor revisar hooks y formato antes de programar para el viernes.",
        )
        db.add(log)

    p4 = db.query(Post).filter(Post.title == "Tutorial YouTube: Configuración OAuth 2.0").first()
    if not p4:
        p4 = Post(
            organization_id=org.id,
            author_id=editor_user.id,
            title="Tutorial YouTube: Configuración OAuth 2.0",
            content="Aprende a conectar las APIs oficiales de Instagram, TikTok y YouTube sin intermediarios inseguros.",
            target_platforms=["youtube"],
            status="draft",
        )
        db.add(p4)

    db.commit()
    print("✅ Database seeding successfully finished!")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

