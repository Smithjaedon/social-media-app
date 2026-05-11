from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import Column, DateTime, func
import uuid

class User(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid7, primary_key=True)
    display_name: str | None = None
    username: str = Field(index=True, unique=True)
    email: str
    hashed_password: str
    disabled: bool = False

class Profile(SQLModel, table=True):
  id: uuid.UUID | None = Field(default_factory=uuid.uuid7, primary_key=True)
  display_name: str | None = None
  username: str | None = None
  
class Post(SQLModel, table=True):
  id: uuid.UUID | None = Field(default_factory=uuid.uuid7, primary_key=True)
  title: str | None = None
  context: str
  created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
  updated_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    )