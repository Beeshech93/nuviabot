import time
from collections import defaultdict
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings


class InMemoryRateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Store IP -> list of timestamps
        self.requests_per_ip = defaultdict(list)
        self.limit = settings.RATE_LIMIT_PER_MINUTE
        self.window = 60  # seconds

    async def dispatch(self, request: Request, call_next):
        # Exclude static files and health check from strict rate limits
        path = request.url.path
        if path.startswith("/static") or path == "/health" or not path.startswith("/api/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        window_start = now - self.window

        # Filter out timestamps older than window
        timestamps = [ts for ts in self.requests_per_ip[client_ip] if ts > window_start]
        timestamps.append(now)
        self.requests_per_ip[client_ip] = timestamps

        if len(timestamps) > self.limit:
            return Response(
                content='{"detail": "Too many requests. Please slow down."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        # Attach security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

