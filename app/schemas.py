import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str
    email: str
    display_name: str
    password: str


class UserRead(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    display_name: str | None = None
    model_config = ConfigDict(from_attributes=True)


class UserDisplayNameRead(BaseModel):
    id: uuid.UUID
    username: str
    display_name: str


class ProfileRead(BaseModel):
    display_name: str
    username: str


class PostsRead(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    like_count: int = Field(default=0)
    comments_count: int = Field(default=0)
    created_at: datetime
    author: UserRead


class PostCreate(BaseModel):
    author_id: uuid.UUID
    title: str
    content: str
    author: UserRead
