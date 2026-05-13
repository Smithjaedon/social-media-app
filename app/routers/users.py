import uuid

from fastapi import APIRouter, HTTPException

from app.auth import TokenDep
from app.models import User
from app.schemas import UserDisplayNameRead, UserRead

router = APIRouter()


@router.get("/users")
async def get_users() -> list[UserRead]:
    return await User.all()


@router.get("/users/by-username")
async def get_user_by_username(username: str, token: TokenDep) -> UserRead:
    user = await User.get_or_none(username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users/by-id")
async def get_user_by_id(user_id: uuid.UUID, token: TokenDep) -> UserRead:
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/display-name")
async def update_display_name(
    display_name: str, token: TokenDep
) -> UserDisplayNameRead:
    token.display_name = display_name
    await token.save()
    return token
