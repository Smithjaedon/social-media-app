import uuid

from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page, paginate
from tortoise.expressions import Q
from tortoise.functions import Count

from app.auth import TokenDep
from app.models import Like, Post
from app.schemas import PostCreate, PostDetailRead, PostsRead

router = APIRouter()


@router.get("/posts", response_model=list[PostsRead])
async def get_posts(token: TokenDep):
    posts = (
        await Post.all()
        .prefetch_related("author")
        .annotate(
            like_count=Count("likes", distinct=True),
            comments_count=Count("comments", distinct=True),
        )
    )
    return list(posts)


@router.get("/posts/by-username", response_model=Page[PostsRead])
async def get_posts_by_username(username: str, token: TokenDep):
    posts = (
        await Post.filter(author__username=username)
        .prefetch_related("author", "comments")
        .annotate(
            like_count=Count("likes", distinct=True),
            comments_count=Count("comments", distinct=True),
        )
    )
    return paginate(posts)


@router.get("/posts/by-user-id", response_model=Page[PostsRead])
async def get_posts_by_user_id(user_id: uuid.UUID, token: TokenDep):
    posts = await Post.filter(author__id=user_id).prefetch_related("author")
    return paginate(posts)


@router.post("/posts", response_model=PostsRead)
async def create_post(payload: PostCreate, token: TokenDep):
    post = await Post.create(
        author_id=token.id,
        title=payload.title,
        content=payload.content,
    )
    await post.fetch_related("author")
    return post


@router.get("/post/{id}", response_model=PostDetailRead)
async def get_post(id: uuid.UUID, token: TokenDep):
    post = (
        await Post.get(id=id)
        .prefetch_related("author", "comments__author")
        .annotate(
            like_count=Count("likes", distinct=True),
            comments_count=Count("comments", distinct=True),
        )
    )
    return post


@router.delete("/posts/{post_id}", response_model=PostsRead)
async def delete_post(post_id: uuid.UUID, token: TokenDep):
    post = await Post.get_or_none(id=post_id).prefetch_related("author")
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if str(post.author.id) != str(token.id):
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


@router.delete("/posts/{post_id}/unlike")
async def unlike_post(post_id: uuid.UUID, token: TokenDep):
    like = await Like.get_or_none(user_id=token.id, post_id=post_id)
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    await like.delete()

    like_count = await Like.filter(post_id=post_id).count()
    return {"message": "unliked", "like_count": like_count}


@router.get("/feed", response_model=Page[PostDetailRead])
async def get_feed(token: TokenDep):
    posts = (
        await Post.all()
        .prefetch_related("author", "comments__author")
        .exclude(author__id=str(token.id))
        .annotate(
            like_count=Count("likes", distinct=True),
            comments_count=Count("comments", distinct=True),
            is_liked=Count(
                "likes", distinct=True, _filter=Q(likes__user_id=str(token.id))
            ),
        )
        .order_by("-like_count")
    )
    return paginate(posts)
