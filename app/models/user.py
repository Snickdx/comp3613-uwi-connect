from typing import Optional

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    password: str
    role: str = ""
    email_verified: int = 0
    display_name: str = ""


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
