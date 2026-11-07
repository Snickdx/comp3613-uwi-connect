"""UWI Connect scenario JSON API (OpenAPI /docs)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.services import accounts, boards, campaigns, notifications
from app.services import board_auth as auth

router = APIRouter(tags=["uwi-connect"])


class LoginBody(BaseModel):
    email: str
    password: str


class RegisterBody(BaseModel):
    email: str
    password: str
    display_name: str = "Alumni"


class ListingBody(BaseModel):
    kind: str = Field(description="job | event")
    title: str
    body: str


class CampaignBody(BaseModel):
    subject: str
    body: str


def _actor_id(x_user_id: str | None) -> int:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header required")
    try:
        return int(x_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="X-User-Id must be int") from exc


@router.post("/auth/login")
def login(body: LoginBody) -> dict[str, Any]:
    user = auth.login(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {"user": user}


@router.post("/auth/register")
def register(body: RegisterBody) -> dict[str, Any]:
    result = accounts.register(body.email, body.password, body.display_name)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/auth/verify-email")
def verify_email(x_user_id: str | None = Header(default=None)) -> dict[str, Any]:
    result = accounts.verify_email(_actor_id(x_user_id))
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/boards")
def browse(kind: str | None = None) -> dict[str, Any]:
    return {"listings": boards.browse_published(kind=kind)}


@router.post("/boards/listings")
def submit(
    body: ListingBody, x_user_id: str | None = Header(default=None)
) -> dict[str, Any]:
    result = boards.submit_listing(
        _actor_id(x_user_id), kind=body.kind, title=body.title, body=body.body
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/admin/listings/pending")
def pending(x_user_id: str | None = Header(default=None)) -> dict[str, Any]:
    actor = auth.get_user(_actor_id(x_user_id))
    if not actor or actor["role"] != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    return {"listings": boards.list_pending()}


@router.post("/admin/listings/{listing_id}/publish")
def publish(
    listing_id: int, x_user_id: str | None = Header(default=None)
) -> dict[str, Any]:
    result = boards.publish_listing(_actor_id(x_user_id), listing_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/admin/listings/{listing_id}/reject")
def reject(
    listing_id: int, x_user_id: str | None = Header(default=None)
) -> dict[str, Any]:
    result = boards.reject_listing(_actor_id(x_user_id), listing_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/admin/campaigns")
def create_campaign(
    body: CampaignBody, x_user_id: str | None = Header(default=None)
) -> dict[str, Any]:
    result = campaigns.create_draft(
        _actor_id(x_user_id), subject=body.subject, body=body.body
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/admin/campaigns")
def list_campaigns(x_user_id: str | None = Header(default=None)) -> dict[str, Any]:
    actor = auth.get_user(_actor_id(x_user_id))
    if not actor or actor["role"] != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    return {"campaigns": campaigns.list_campaigns()}


@router.post("/admin/campaigns/{campaign_id}/send")
def send_campaign(
    campaign_id: int, x_user_id: str | None = Header(default=None)
) -> dict[str, Any]:
    result = campaigns.send_campaign(_actor_id(x_user_id), campaign_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/notifications")
def my_notifications(x_user_id: str | None = Header(default=None)) -> dict[str, Any]:
    return {"notifications": notifications.inbox(_actor_id(x_user_id))}
