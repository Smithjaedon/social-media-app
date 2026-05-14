import random
import uuid

from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page, paginate
from tortoise.functions import Count

from app.auth import TokenDep
from app.models import User
from app.schemas import AuthorRead, ProfileRead, UserDisplayNameRead, UserRead

router = APIRouter()


@router.get("/users", response_model=list[UserRead])
async def get_users():
    return await User.all()


@router.get("/users/by-username", response_model=ProfileRead)
async def get_user_by_username(username: str, token: TokenDep):
    user = (
        await User.get_or_none(username=username)
        .prefetch_related("posts")
        .annotate(
            posts_count=Count("posts", distinct=True),
            following_count=Count("following", distinct=True),
            follower_count=Count("followers", distinct=True),
        )
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users/by-id", response_model=UserRead)
async def get_user_by_id(user_id: uuid.UUID, token: TokenDep):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/display-name", response_model=AuthorRead)
async def update_display_name(display_name: str, token: TokenDep):
    token.display_name = display_name
    await token.save()
    return token


@router.get("/recommend", response_model=Page[UserDisplayNameRead])
async def get_recommened(token: TokenDep):
    users = await User.all()
    random.shuffle(users)
    return paginate(users)
