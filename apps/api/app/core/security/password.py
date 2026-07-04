"""Password hashing using Argon2id.

Argon2id is the current best-practice memory-hard password hash. The
`argon2-cffi` defaults are secure; we expose a thin wrapper so call sites
never touch the library directly.
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return an Argon2id hash for the given plaintext password."""
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored hash.

    Returns False on mismatch or malformed hash rather than raising, so call
    sites can treat it as a simple boolean check.
    """
    try:
        return _hasher.verify(hashed, password)
    except (VerifyMismatchError, InvalidHashError, ValueError):
        return False


def needs_rehash(hashed: str) -> bool:
    """Return True if the hash should be upgraded (params changed)."""
    try:
        return _hasher.check_needs_rehash(hashed)
    except (InvalidHashError, ValueError):
        return False
