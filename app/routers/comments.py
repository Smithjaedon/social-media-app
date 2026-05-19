import uuid

from fastapi import APIRouter, HTTPException
from tortoise.expressions import F, Q, Subquery
from tortoise.functions import Count

from app import auth
from app.auth import TokenDep
from app.models import Comment, Like
from app.schemas import AuthorRead, CommentCreate, CommentRead

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
    comments = (
        await Comment.filter(post__id=id)
        .prefetch_related("author")
        .annotate(like_count=Count("likes", distinct=True))
        .all()
    )

    liked_ids = set(
        await Like.filter(user_id=token.id, comment__post__id=id).values_list(
            "comment_id", flat=True
        )
    )

    for comment in comments:
        comment.has_liked = comment.id in liked_ids

    return comments


@router.get("/comments", response_model=list[CommentRead])
async def get_comments(token: TokenDep):
    return list(
        await Comment.all()
        .prefetch_related("author")
        .annotate(like_count=Count("likes", distinct=True))
    )


@router.post("/comments/{id}/like", response_model=CommentRead)
async def like_comment(id: uuid.UUID, token: TokenDep):
    comment = await Comment.get_or_none(id=id).annotate(like_count=Count("likes"))
    if not comment:
        raise HTTPException(status_code=404, detail="comment does not exist")

    existing = await Like.get_or_none(user=token, comment=comment)
    if existing:
        raise HTTPException(status_code=400, detail="already liked")

    await Like.create(user=token, comment=comment)
    await comment.fetch_related("author")

    result = CommentRead.model_validate(comment, from_attributes=True)
    result.author = AuthorRead.model_validate(comment.author, from_attributes=True)
    result.like_count = (comment.like_count or 0) + 1
    result.has_liked = True
    return result


@router.delete("/comments/{id}/unlike", response_model=CommentRead)
async def unlike_comment(id: uuid.UUID, token: TokenDep):
    comment = await Comment.get_or_none(id=id).annotate(like_count=Count("likes"))
    if not comment:
        raise HTTPException(status_code=404, detail="comment does not exist")

    like = await Like.get_or_none(user=token, comment=comment)
    if not like:
        raise HTTPException(status_code=400, detail="you have not liked this comment")

    await like.delete()
    await comment.fetch_related("author")

    result = CommentRead.model_validate(comment, from_attributes=True)
    result.author = AuthorRead.model_validate(comment.author, from_attributes=True)
    result.like_count = max((comment.like_count or 1) - 1, 0)
    result.has_liked = False
    return result


@router.delete("/comment/{id}")
async def delete_comment(id: uuid.UUID, token: TokenDep):
    comment = await Comment.get_or_none(id=id)
    if not comment:
        raise HTTPException(status_code=404, detail="comment not found")
    await comment.delete()
