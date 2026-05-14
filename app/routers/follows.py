import uuid

from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page, paginate

from app.auth import TokenDep
from app.models import Follow, Post, User
from app.schemas import FollowRead, PostsRead

router = APIRouter()


@router.post("/user/{id}/follow", response_model=FollowRead)
async def foller_user(id: uuid.UUID, token: TokenDep):
    to_follow_user = await User.get(id=id)
    if not to_follow_user:
        raise HTTPException(status_code=404, detail="Cannot find user")
    follow = Follow.create(follower=token, following=to_follow_user)
    if not follow:
        raise HTTPException(status_code=404, detail="cannont follow user")
    return follow


@router.post("/user/{id}/unfollow")
async def unfollow_user(id: uuid.UUID, token: TokenDep):
    follow = await Follow.get(id=id)
    if not follow:
        raise HTTPException(status_code=404, detail="user not followed")
    await follow.delete()


@router.get("/follows", response_model=list[FollowRead])
async def get_follows(token: TokenDep):
    return list(await Follow.all().prefetch_related("follower", "following"))


@router.get("/following", response_model=Page[PostsRead])
async def get_following(token: TokenDep):
    following_ids = await Follow.filter(follower_id=token.id).values_list(
        "following_id", flat=True
    )
    if not following_ids:
        raise HTTPException(status_code=404, detail="no follows exists")
    return paginate(
        await Post.filter(author_id__in=following_ids).prefetch_related(
            "author", "comments"
        )
    )
