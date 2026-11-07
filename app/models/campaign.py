from typing import Optional

from sqlmodel import Field, SQLModel


class Campaign(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    admin_id: int = Field(index=True)
    subject: str
    body: str
    status: str
    created_at: str
    sent_at: Optional[str] = None
