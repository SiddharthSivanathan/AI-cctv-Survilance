"""FastAPI application entrypoint.

Wires configuration, logging, middleware, error handlers, and routers. No
business logic lives here — composition only (Clean Architecture: frameworks
layer).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app import __version__
from app.api.v1 import health, ws
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.error_handlers import register_error_handlers
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging()
logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach baseline security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "0"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("api_startup", environment=settings.environment, version=__version__)
    # Ensure the media bucket exists (non-fatal if storage is unreachable).
    try:
        from app.core.storage import ensure_bucket

        ensure_bucket()
    except Exception as exc:  # noqa: BLE001 - never block startup on storage
        logger.warning("storage_init_skipped", error=str(exc))
    yield
    logger.info("api_shutdown")


app = FastAPI(
    title=settings.project_name,
    version=__version__,
    description="AI-powered Video Intelligence SaaS Platform — Control Plane API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

# Liveness/readiness probes at the root (K8s/Docker conventions).
app.include_router(health.router)

# Real-time WebSocket hub (root path /ws/events).
app.include_router(ws.router)

# Versioned feature API.
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["root"], summary="Service banner")
async def root() -> dict[str, str]:
    """Return a minimal service banner."""
    return {"service": settings.project_name, "version": __version__, "docs": "/docs"}
