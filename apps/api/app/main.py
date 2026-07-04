"""FastAPI application entrypoint.

Wires configuration, logging, middleware, and routers. No business logic
lives here — it is composition only (Clean Architecture: frameworks layer).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1 import health
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application startup/shutdown lifecycle."""
    logger.info("api_startup", environment=settings.environment, version=__version__)
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Liveness/readiness probes at the root (K8s/Docker conventions).
app.include_router(health.router)

# Versioned feature API.
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["root"], summary="Service banner")
async def root() -> dict[str, str]:
    """Return a minimal service banner."""
    return {"service": settings.project_name, "version": __version__, "docs": "/docs"}
