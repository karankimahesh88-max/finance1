"""
Mock auth service — NO real authentication.
Auto-signs in a fixed demo user so app.py's login screen is skipped entirely.
Swap this out for a real Firebase-backed version later if needed.
"""

DEMO_USER = {"uid": "demo-user-1", "email": "demo@localhost"}


def is_authenticated() -> bool:
    return True


def current_user() -> dict:
    return DEMO_USER


def sign_in(email: str, password: str) -> dict:
    # Not used since is_authenticated() is always True, but kept for interface parity.
    return DEMO_USER


def sign_up(email: str, password: str, name: str) -> dict:
    return DEMO_USER


def start_session(data: dict) -> None:
    pass


def logout() -> None:
    # No-op: there is no real session to clear in mock mode.
    pass
