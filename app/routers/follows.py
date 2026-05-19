import uuid

from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page, paginate
from tortoise.functions import Count

from app.auth import TokenDep
from app.models import Follow, Like, Post, User
from app.schemas import FollowRead, PostDetailRead, PostsRead

router = APIRouter()


@router.post("/user/{id}/follow", response_model=FollowRead)
async def follow_user(id: uuid.UUID, token: TokenDep):
    to_follow_user = await User.get(id=id)
    if not to_follow_user:
        raise HTTPException(status_code=404, detail="Cannot find user")
    follow = await Follow.create(follower=token, following=to_follow_user)
    if not follow:
        raise HTTPException(status_code=404, detail="cannont follow user")
    return follow


@router.delete("/user/{id}/unfollow")
async def unfollow_user(id: uuid.UUID, token: TokenDep):
    user = await User.get_or_none(id=id)
    if not user:
        raise HTTPException(status_code=404, detail="Cannot find user")
    follow = await Follow.filter(following=user, follower=token).first()
    if not follow:
        raise HTTPException(status_code=404, detail="user not followed")
    await follow.delete()


@router.get("/follows", response_model=list[FollowRead])
async def get_follows(token: TokenDep):
    return list(await Follow.all().prefetch_related("follower", "following"))


@router.get("/following", response_model=Page[PostDetailRead])
async def get_following(token: TokenDep):
    following_ids = await Follow.filter(follower_id=token.id).values_list(
        "following_id", flat=True
    )
    posts = (
        await Post.filter(author_id__in=following_ids)
        .prefetch_related("author", "comments__author")
        .annotate(
            like_count=Count("likes", distinct=True),
            comments_count=Count("comments", distinct=True),
        )
    )

    result = []
    for post in posts:
        post.has_liked = await Like.filter(user_id=token.id, post_id=post.id).exists()
        result.append(post)
    return paginate(result)
