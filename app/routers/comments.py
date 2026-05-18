import uuid

from fastapi import APIRouter, HTTPException
from tortoise.expressions import Q
from tortoise.functions import Count

from app.auth import TokenDep
from app.models import Comment, Like
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
        .annotate(
            like_count=Count("likes"),
            is_liked=Count(
                "likes", distinct=True, _filter=Q(likes__user_id=str(token.id))
            ),
        )
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


@router.post("/comments/{id}/like", response_model=CommentRead)
async def like_comment(id: uuid.UUID, token: TokenDep):
    comment = await Comment.get_or_none(id=id)
    if not comment:
        raise HTTPException(status_code=404, detail="comment does not exist")
    like = await Like.create(user=token, comment=comment)


@router.delete("/comments/{id}/unlike", response_model=CommentRead)
async def unlike_comment(id: uuid.UUID, token: TokenDep):
    comment = await Comment.get_or_none(id=id)
    if not comment:
        raise HTTPException(status_code=404, detail="comment does not exist")
    like = await Like.filter(comment=comment).first()
    if not like:
        raise HTTPException(status_code=404, detail="there are no likes")
    await like.delete()
    return CommentRead.model_validate(
        await Comment.get(id=id).prefetch_related("author")
    )


@router.delete("/comment/{id}")
async def delete_comment(id: uuid.UUID, token: TokenDep):
    comment = await Comment.get_or_none(id=id)
    if not comment:
        raise HTTPException(status_code=404, detail="comment not found")
    await comment.delete()
