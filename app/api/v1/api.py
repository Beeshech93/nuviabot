from fastapi import APIRouter
from app.api.v1.ai import router as ai_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.auth import router as auth_router
from app.api.v1.billing import router as billing_router
from app.api.v1.clients import router as clients_router
from app.api.v1.media import router as media_router
from app.api.v1.posts import router as posts_router
from app.api.v1.settings import router as settings_router
from app.api.v1.social import router as social_router
from app.api.v1.team import router as team_router
from app.api.v1.webhooks import router as webhooks_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(social_router)
api_router.include_router(webhooks_router)
api_router.include_router(posts_router)
api_router.include_router(approvals_router)
api_router.include_router(ai_router)
api_router.include_router(media_router)
api_router.include_router(analytics_router)
api_router.include_router(clients_router)
api_router.include_router(team_router)
api_router.include_router(billing_router)
api_router.include_router(settings_router)

