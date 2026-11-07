from typing import Optional

from sqlmodel import Field, SQLModel


class Listing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(index=True)
    kind: str = Field(index=True)
    title: str
    body: str
    status: str
    created_at: str
