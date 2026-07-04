"""Aggregated v1 API router.

Feature routers (auth, organizations, cameras, ...) are registered here as
they are implemented in later phases. Health/readiness probes are mounted at
the application root (see app.main), not under the versioned prefix.
"""

from fastapi import APIRouter

api_router = APIRouter()

# Phase 3+: api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
