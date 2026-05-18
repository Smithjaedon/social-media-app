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
    bio: str | None = None
    display_name: str | None = None
    has_followed: bool = Field(default=False)
    model_config = ConfigDict(from_attributes=True)


class UserDisplayNameRead(BaseModel):
    id: uuid.UUID
    username: str
    display_name: str


class ProfileRead(UserRead):
    following_count: int = Field(default=0)
    follower_count: int = Field(default=0)
    posts_count: int = Field(default=0)


class PostsRead(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    like_count: int = Field(default=0)
    comments_count: int = Field(default=0)
    created_at: datetime
    author: UserRead
    model_config = ConfigDict(from_attributes=True)


class PostDetailRead(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    like_count: int = Field(default=0)
    comments_count: int = Field(default=0)
    created_at: datetime
    author: UserRead
    comments: list[CommentRead]
    is_liked: bool = Field(default=False)
    model_config = ConfigDict(from_attributes=True)


class PostCreate(BaseModel):
    title: str
    content: str


class FollowRead(BaseModel):
    follower: UserRead
    following: UserRead


class AuthorRead(BaseModel):
    id: uuid.UUID
    display_name: str | None
    username: str


class CommentCreate(BaseModel):
    content: str


class CommentRead(BaseModel):
    id: uuid.UUID
    content: str
    created_at: datetime
    post_id: uuid.UUID
    author: AuthorRead
    like_count: int = Field(default=0)
    has_liked: bool = Field(default=False)
    model_config = ConfigDict(from_attributes=True)


class BioRead(BaseModel):
    id: uuid.UUID
    username: str
    bio: str | None = None
    model_config = ConfigDict(from_attributes=True)


class BioUpdate(BaseModel):
    bio: str | None = None
