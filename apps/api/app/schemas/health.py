"""Health check response schemas."""

from pydantic import BaseModel


class DependencyStatus(BaseModel):
    """Status of an external dependency."""

    name: str
    status: str  # "up" | "down"


class HealthResponse(BaseModel):
    """Overall service health."""

    status: str
    service: str = "api"
    version: str


class ReadinessResponse(BaseModel):
    """Readiness including dependency checks."""

    status: str
    service: str = "api"
    version: str
    dependencies: list[DependencyStatus]
