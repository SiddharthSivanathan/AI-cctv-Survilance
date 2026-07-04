"""Organization roles.

V1 only assigns OWNER. The remaining roles are reserved so the enum, the
`role` column, and the `require_role` dependency extend without a schema or
API refactor when richer RBAC is introduced.
"""

from enum import Enum


class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"


# Simple privilege ordering for future `require_role` comparisons.
ROLE_RANK: dict[str, int] = {
    Role.VIEWER.value: 10,
    Role.ANALYST.value: 20,
    Role.MANAGER.value: 30,
    Role.ADMIN.value: 40,
    Role.OWNER.value: 50,
}
