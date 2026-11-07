"""Seed demo users and sample listings for the uwi-connect scenario."""

from __future__ import annotations

from sqlmodel import Session, select

from app.database import drop_all, ensure_db_and_tables, engine
from app.models.listing import Listing
from app.models.user import User
from app.services import notifications
from app.utilities.security import encrypt_password

USERS = [
    # email, password, role, email_verified, display_name
    ("admin@uwi.edu", "admin-dev", "admin", 1, "Alumni Admin"),
    ("alumni.verified@my.uwi.edu", "alumni-dev", "alumni", 1, "Verified Alum"),
    ("alumni.pending@gmail.com", "alumni-dev", "alumni", 0, "Unverified Alum"),
    ("alumni.fakeuwi@example.com", "alumni-dev", "alumni", 0, "Substring Trap"),
]


def seed(*, reset: bool = False) -> None:
    import app.models  # noqa: F401

    if reset:
        try:
            drop_all()
        except Exception:
            pass
        notifications.clear_observers()
    ensure_db_and_tables()
    notifications.ensure_default_observers()

    with Session(engine) as session:
        existing = session.exec(select(User)).first()
        if existing and not reset:
            return

        for email, password, role, verified, name in USERS:
            session.add(
                User(
                    username=email,
                    email=email,
                    password=encrypt_password(password),
                    role=role,
                    email_verified=verified,
                    display_name=name,
                )
            )
        session.commit()

        admin = session.exec(select(User).where(User.email == "admin@uwi.edu")).one()
        alum = session.exec(
            select(User).where(User.email == "alumni.verified@my.uwi.edu")
        ).one()

        session.add_all(
            [
                Listing(
                    author_id=admin.id,
                    kind="job",
                    title="Seed Software Role",
                    body="Published seed job.",
                    status="published",
                    created_at="2099-01-01T12:00:00+00:00",
                ),
                Listing(
                    author_id=alum.id,
                    kind="job",
                    title="Pending Alumni Job",
                    body="Awaiting admin publish.",
                    status="pending",
                    created_at="2099-01-02T12:00:00+00:00",
                ),
            ]
        )
        session.commit()


if __name__ == "__main__":
    seed(reset=True)
    print("Seeded uwi-connect scenario data")
