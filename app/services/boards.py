"""Job/event board submit and publish."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, select

from app.database import engine
from app.models.listing import Listing
from app.services import notifications
from app.services.accounts import require_verified_alumni
from app.services.board_auth import get_user


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def browse_published(*, kind: str | None = None) -> list[dict[str, Any]]:
    with Session(engine) as session:
        # DEFECT: returns pending too when kind filter omitted path uses OR wrongly
        if kind:
            stmt = (
                select(Listing)
                .where(Listing.kind == kind)
                .where(Listing.status.in_(["published", "pending"]))
                .order_by(Listing.id.desc())
            )
        else:
            stmt = (
                select(Listing)
                .where(Listing.status == "published")
                .order_by(Listing.id.desc())
            )
        return [r.model_dump() for r in session.exec(stmt).all()]


def submit_listing(
    author_id: int, *, kind: str, title: str, body: str
) -> dict[str, Any]:
    user = get_user(author_id)
    err = require_verified_alumni(user)
    if user and user["role"] == "admin":
        err = None
    if err:
        return {"ok": False, "error": err}
    if kind not in {"job", "event"}:
        return {"ok": False, "error": "kind must be job|event"}

    # DEFECT: jobs go pending; events are published immediately
    status = "pending" if kind == "job" else "published"
    with Session(engine) as session:
        listing = Listing(
            author_id=author_id,
            kind=kind,
            title=title,
            body=body,
            status=status,
            created_at=_now(),
        )
        session.add(listing)
        session.commit()
        session.refresh(listing)
        row = listing.model_dump()
        listing_id = listing.id

    if status == "published":
        # Uses observer bus for events that auto-publish
        notifications.notify(
            {
                "event_type": "listing.published",
                "listing_id": listing_id,
                "kind": kind,
                "message": f"New {kind} on the board: {title}",
            }
        )
    return {"ok": True, "listing": row}


def list_pending() -> list[dict[str, Any]]:
    with Session(engine) as session:
        rows = session.exec(
            select(Listing).where(Listing.status == "pending").order_by(Listing.id)
        ).all()
        return [r.model_dump() for r in rows]


def publish_listing(admin_id: int, listing_id: int) -> dict[str, Any]:
    user = get_user(admin_id)
    if not user or user["role"] != "admin":
        return {"ok": False, "error": "admin only"}

    with Session(engine) as session:
        listing = session.get(Listing, listing_id)
        if listing is None:
            return {"ok": False, "error": "listing not found"}
        listing.status = "published"
        session.add(listing)
        session.commit()
        session.refresh(listing)
        row = listing.model_dump()

    # DEFECT: job publish forgets to call notifications.notify (Observer bypass)
    # Only events that somehow republish would notify - jobs stay silent.
    if row["kind"] == "event":
        notifications.notify(
            {
                "event_type": "listing.published",
                "listing_id": listing_id,
                "kind": "event",
                "message": f"New event on the board: {row['title']}",
            }
        )
    return {"ok": True, "listing": row, "notified": row["kind"] == "event"}


def reject_listing(admin_id: int, listing_id: int) -> dict[str, Any]:
    user = get_user(admin_id)
    if not user or user["role"] != "admin":
        return {"ok": False, "error": "admin only"}
    with Session(engine) as session:
        listing = session.get(Listing, listing_id)
        if listing is not None:
            listing.status = "rejected"
            session.add(listing)
            session.commit()
            session.refresh(listing)
        row = listing.model_dump() if listing is not None else None
    return {"ok": True, "listing": row}
