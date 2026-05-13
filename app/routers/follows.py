import uuid

from fastapi import APIRouter, HTTPException
from tortoise.functions import Count

from app.auth import TokenDep
from app.models import Follow, Like, Post, User
from app.schemas import FollowRead, PostCreate, PostsRead

router = APIRouter()


@router.post("/user/{id}/follow")
async def foller_user(id: uuid.UUID, token: TokenDep) -> FollowRead:
    to_follow_user = await User.get(id=id)
    follow = Follow.create(follower=token, following=to_follow_user)
    return FollowRead.model_validate(follow)


@router.get("/follows")
async def get_follows(token: TokenDep) -> FollowRead:
    return FollowRead.model_validate(await Follow.all())
