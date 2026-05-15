import uuid

from fastapi import APIRouter, HTTPException
from tortoise.functions import Count

from app.auth import TokenDep
from app.models import Comment
from app.schemas import CommentCreate, CommentRead

router = APIRouter()


@router.post("/posts/{post_id}/comments", response_model=CommentRead)
async def post_comments(
    post_id: uuid.UUID,
    payload: CommentCreate,
    token: TokenDep,
):
    comment = await Comment.create(
        content=payload.content,
        post_id=post_id,
        author_id=token.id,
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Invalid Information")
    await comment.fetch_related("author")
    return comment


@router.get("/posts/{id}/comments", response_model=list[CommentRead])
async def get_comments_from_posts(id: uuid.UUID, token: TokenDep):
    return (
        await Comment.filter(post__id=id)
        .prefetch_related("author")
        .annotate(like_count=Count("likes"))
        .distinct()
        .all()
    )


@router.get("/comments", response_model=list[CommentRead])
async def get_comments(token: TokenDep):
    return list(
        await Comment.all()
        .prefetch_related("author")
        .annotate(like_count=Count("likes", distinct=True))
    )


@router.delete("/comment/{id}")
async def delete_comment(id: uuid.UUID, token: TokenDep):
    comment = await Comment.get(id=id)
    await comment.delete()
