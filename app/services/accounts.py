"""Registration and UWI-email verification (intentionally soft)."""

from __future__ import annotations

from typing import Any

from sqlmodel import Session

from app.database import engine
from app.models.user import User
from app.services.board_auth import public_user
from app.utilities.security import encrypt_password


def looks_like_uwi_email(email: str) -> bool:
    # DEFECT: substring check, not a real institutional domain allowlist
    return "uwi" in email.lower() or "my.uwi" in email.lower()


def register(
    email: str, password: str, display_name: str, *, role: str = "alumni"
) -> dict[str, Any]:
    if role not in {"alumni", "admin"}:
        return {"ok": False, "error": "role must be alumni|admin"}
    with Session(engine) as session:
        try:
            user = User(
                username=email,
                email=email,
                password=encrypt_password(password),
                role=role,
                email_verified=0,
                display_name=display_name,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        except Exception as exc:
            session.rollback()
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "user": public_user(user)}


def verify_email(user_id: int) -> dict[str, Any]:
    """Mark email verified - demo stub (no real token mailer)."""
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user is None:
            return {"ok": False, "error": "user not found"}
        # DEFECT: verification succeeds even when email fails looks_like_uwi_email
        user.email_verified = 1
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"ok": True, "user": public_user(user)}


def require_verified_alumni(user: dict[str, Any] | None) -> str | None:
    if not user:
        return "unknown user"
    if user["role"] != "alumni":
        return None  # admins bypass
    if not user.get("email_verified"):
        return "email not verified"
    return None
