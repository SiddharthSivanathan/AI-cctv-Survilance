"""Application exceptions mapped to HTTP responses in app.main.

Services raise these domain errors; the API layer never constructs HTTP
errors from business logic directly. Each carries a stable machine-readable
``code`` for the frontend to branch on.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base application error."""

    status_code: int = 400
    code: str = "app_error"

    def __init__(
        self, message: str, *, code: str | None = None, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.details = details or {}


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"


class AuthenticationError(AppError):
    status_code = 401
    code = "authentication_error"


class InvalidCredentialsError(AuthenticationError):
    code = "invalid_credentials"


class EmailNotVerifiedError(AuthenticationError):
    status_code = 403
    code = "email_not_verified"


class InvalidTokenError(AuthenticationError):
    code = "invalid_token"


class PermissionDeniedError(AppError):
    status_code = 403
    code = "permission_denied"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class RateLimitedError(AppError):
    status_code = 429
    code = "rate_limited"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class EmailAlreadyExistsError(ConflictError):
    code = "email_already_exists"


class OrganizationExistsError(ConflictError):
    code = "organization_exists"
