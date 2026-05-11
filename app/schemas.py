from pydantic import BaseModel
import uuid

class UserCreate(BaseModel):
    username: str
    email: str
    display_name: str
    password: str

class UserRead(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    display_name: str
    disabled: bool

class UserDeleteById(BaseModel):
    id: uuid.UUID

class UserDeleteByUsername(BaseModel):
    username: str