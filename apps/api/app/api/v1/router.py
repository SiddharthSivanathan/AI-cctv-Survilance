"""Aggregated v1 API router.

Feature routers are registered here. Health/readiness probes are mounted at
the application root (see app.main), not under the versioned prefix.
"""

from fastapi import APIRouter

from app.api.v1 import auth, organizations, stores

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(stores.router)
