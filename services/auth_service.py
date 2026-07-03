"""
Supabase-backed auth service.

Same function names/signatures as the old mock version on purpose — app.py
calls these and doesn't know or care what's behind them. Session state
(current user + Supabase session tokens) lives in st.session_state, since
that's what persists across Streamlit reruns within a browser tab.
"""
import streamlit as st

from .supabase_config import get_client

SESSION_KEY = "auth_user"


def is_authenticated() -> bool:
    return SESSION_KEY in st.session_state


def current_user() -> dict:
    return st.session_state.get(SESSION_KEY)


def sign_in(email: str, password: str) -> dict:
    """Raises ValueError with a friendly message on bad credentials."""
    client = get_client()
    try:
        result = client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception:
        raise ValueError("Invalid email or password.")

    if not result.user or not result.session:
        raise ValueError("Invalid email or password.")

    return {
        "uid": result.user.id,
        "email": result.user.email,
        "name": (result.user.user_metadata or {}).get("name", ""),
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
    }


def sign_up(email: str, password: str, name: str) -> dict:
    """Raises ValueError with a friendly message if signup fails."""
    client = get_client()
    try:
        result = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"name": name}},
        })
    except Exception as e:
        raise ValueError(str(e))

    if not result.user:
        raise ValueError("Could not create account. Try a different email.")

    # If email confirmations are OFF in Supabase Auth settings, sign_up already
    # returns a session and we can log the user straight in. If confirmations
    # are ON, there's no session yet — the caller (app.py) should tell the
    # user to check their email, then use the login tab once confirmed.
    if result.session:
        return {
            "uid": result.user.id,
            "email": result.user.email,
            "name": name,
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
        }

    raise ValueError("Account created — check your email to confirm, then log in.")


def start_session(data: dict) -> None:
    st.session_state[SESSION_KEY] = data
    # Also point the Supabase client at this user's tokens so subsequent
    # table queries run as them (required for Row Level Security policies
    # that check auth.uid() to actually scope data to this user).
    get_client().auth.set_session(data["access_token"], data["refresh_token"])


def logout() -> None:
    try:
        get_client().auth.sign_out()
    except Exception:
        pass
    st.session_state.pop(SESSION_KEY, None)
