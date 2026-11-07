"""
Notification "bus" - intended Observer seam, implemented poorly.

Publish/campaign flows should notify interested alumni through a real
subject/observer design. This module instead keeps a mutable global list of
callables, mixes persistence into observers, and is easy to bypass.

Students: replace with a proper Observer (or event bus) so listing publish and
campaign send fan out consistently to verified alumni only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from sqlmodel import Session, select

from app.database import engine
from app.models.notification import Notification
from app.models.user import User

# Module-level registry - not a subject; order and duplicates are uncontrolled.
_OBSERVERS: list[Callable[[dict[str, Any]], None]] = []


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def subscribe(observer: Callable[[dict[str, Any]], None]) -> None:
    # DEFECT: no de-dupe; re-import / double-register stacks duplicates
    _OBSERVERS.append(observer)


def clear_observers() -> None:
    _OBSERVERS.clear()


def notify(event: dict[str, Any]) -> None:
    """Fan-out to registered observers (if anyone remembered to call this)."""
    # DEFECT: swallows observer errors so silent failure looks like success
    for obs in list(_OBSERVERS):
        try:
            obs(event)
        except Exception:
            pass


def inbox(user_id: int) -> list[dict[str, Any]]:
    with Session(engine) as session:
        rows = session.exec(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.id.desc())
        ).all()
        return [r.model_dump() for r in rows]


def _persist_to_all_users(event: dict[str, Any]) -> None:
    """Default observer - writes a row per user."""
    message = event.get("message") or event.get("event_type") or "update"
    with Session(engine) as session:
        # DEFECT: includes unverified alumni and even admins as campaign targets
        users = session.exec(select(User)).all()
        for user in users:
            # DEFECT: job events skip unverified; campaign events do not (inconsistent)
            if event.get("event_type") == "listing.published":
                if not user.email_verified and user.role == "alumni":
                    continue
            session.add(
                Notification(
                    user_id=user.id,
                    event_type=event.get("event_type", "unknown"),
                    message=message,
                    created_at=_now(),
                )
            )
        session.commit()


def _log_only(event: dict[str, Any]) -> None:
    # Second observer that does nothing useful - looks like logging
    _ = event


def ensure_default_observers() -> None:
    """Called at startup - registers the messy defaults."""
    if not _OBSERVERS:
        subscribe(_persist_to_all_users)
        subscribe(_log_only)
