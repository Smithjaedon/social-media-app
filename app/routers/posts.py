import uuid

from fastapi import APIRouter, HTTPException
from tortoise.functions import Count

from app.auth import TokenDep
from app.models import Like, Post
from app.schemas import PostCreate, PostsRead

router = APIRouter()


@router.get("/posts")
async def get_posts(token: TokenDep) -> list[PostsRead]:

    posts = (
        await Post.all()
        .prefetch_related("author")
        .annotate(
            like_count=Count("likes"),
            comment_count=Count("comments"),
        )
    )
    return [PostsRead.model_validate(post) for post in posts]


@router.get("/posts/by-username")
async def get_posts_by_username(username: str, token: TokenDep) -> list[PostsRead]:
    return await Post.filter(author__username=username).prefetch_related(
        "author", "comments"
    )


@router.get("/posts/by-user-id")
async def get_posts_by_user_id(user_id: uuid.UUID, token: TokenDep) -> list[PostsRead]:
    return await Post.filter(author__id=user_id).prefetch_related("author")


@router.post("/posts")
async def create_post(payload: PostCreate, token: TokenDep) -> PostsRead:
    post = await Post.create(
        author_id=token.id,
        title=payload.title,
        content=payload.content,
    )
    await post.fetch_related("author")
    return post


@router.delete("/posts/{post_id}")
async def delete_post(post_id: uuid.UUID, token: TokenDep) -> PostsRead:
    post = await Post.get_or_none(id=post_id).prefetch_related("author")
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != token.id:
        raise HTTPException(status_code=403, detail="Not your post")
    await post.delete()
    return post


@router.post("/posts/{post_id}/like")
async def like_post(post_id: uuid.UUID, token: TokenDep):
    post = await Post.get_or_none(id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = await Like.get_or_none(user_id=token.id, post_id=post_id)
    if existing:
        raise HTTPException(status_code=400, detail="Already liked")

    await Like.create(user_id=token.id, post_id=post_id)

    like_count = await Like.filter(post_id=post_id).count()
    return {"message": "liked", "like_count": like_count}


@router.delete("/posts/{post_id}/like")
async def unlike_post(post_id: uuid.UUID, token: TokenDep):
    like = await Like.get_or_none(user_id=token.id, post_id=post_id)
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    await like.delete()

    like_count = await Like.filter(post_id=post_id).count()
    return {"message": "unliked", "like_count": like_count}
