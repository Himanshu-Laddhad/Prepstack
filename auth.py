"""
No-auth shim.

All requests share a single default user so the rest of the app
(DB foreign keys, etc.) keeps working with zero login ceremony.
"""

from dataclasses import dataclass

DEFAULT_USER_ID = "default-user-000000000000000"
DEFAULT_USER_EMAIL = "user@prepstack.local"


@dataclass
class MockUser:
    id: str = DEFAULT_USER_ID
    email: str = DEFAULT_USER_EMAIL


def get_current_user() -> MockUser:
    """FastAPI dependency — always returns the default user, no token required."""
    return MockUser()
