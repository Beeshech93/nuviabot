import asyncio
from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.v1.api import api_router
from app.config import settings
from app.core.rate_limiter import InMemoryRateLimiterMiddleware
from app.db.seed import seed_database
from app.db.session import Base, SessionLocal, engine
from app.services.media_service import MediaService
from app.services.publisher_service import PublisherService

# Background task reference
scheduler_task = None


async def background_scheduler():
    """Lightweight built-in async worker for scheduled publications."""
    while True:
        try:
            db = SessionLocal()
            try:
                await PublisherService.process_scheduled_queue(db)
            finally:
                db.close()
        except Exception:
            pass
        await asyncio.sleep(20)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB schema, directories, seed data, and start scheduler
    Base.metadata.create_all(bind=engine)
    MediaService.ensure_upload_dir()

    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    # Start background scheduler
    global scheduler_task
    scheduler_task = asyncio.create_task(background_scheduler())

    yield

    # Shutdown
    if scheduler_task:
        scheduler_task.cancel()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Professional AI-Powered Social Media Growth & Management SaaS Platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach Security & Rate Limiting Middleware
app.add_middleware(InMemoryRateLimiterMiddleware)

# Attach CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Assets & Templates
static_dir = os.path.join(os.path.dirname(__file__), "static")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "version": settings.VERSION,
        },
    )


@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy():
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
        <head><title>Privacy Policy - Nuvio Growth Bot</title><style>body{font-family:sans-serif;line-height:1.6;max-width:800px;margin:40px auto;padding:20px;background:#0d1117;color:#c9d1d9;}</style></head>
        <body>
        <h1>Privacy Policy</h1>
        <p>Last updated: November 2026</p>
        <p>NUVIO GROWTH BOT prioritizes user data protection and complies strictly with the official Meta, TikTok, and Google developer policies. We do not sell data to third parties. Tokens are encrypted using AES-256 standard encryption and used solely for user-authorized social media publishing and analytics.</p>
        <p><a href="/" style="color:#58a6ff;">Back to Dashboard</a></p>
        </body>
        </html>
        """
    )


@app.get("/terms-of-service", response_class=HTMLResponse)
async def terms_of_service():
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
        <head><title>Terms of Service - Nuvio Growth Bot</title><style>body{font-family:sans-serif;line-height:1.6;max-width:800px;margin:40px auto;padding:20px;background:#0d1117;color:#c9d1d9;}</style></head>
        <body>
        <h1>Terms of Service</h1>
        <p>Last updated: November 2026</p>
        <p>NUVIO GROWTH BOT is an enterprise-grade AI social media management platform. Users agree not to use this service for spam, fake follower generation, artificial views, deceptive comments, or any activities violating official platform APIs and community guidelines.</p>
        <p><a href="/" style="color:#58a6ff;">Back to Dashboard</a></p>
        </body>
        </html>
        """
    )

