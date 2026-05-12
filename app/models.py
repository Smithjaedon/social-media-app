import uuid
from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    display_name = fields.CharField(max_length=255, null=True)
    username = fields.CharField(max_length=255, unique=True, index=True)
    email = fields.CharField(max_length=255)
    hashed_password = fields.CharField(max_length=255)
    disabled = fields.BooleanField(default=False)

    posts: fields.ReverseRelation["Post"]

    class Meta:
        table = "users"


class Post(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    title = fields.CharField(max_length=255, null=True)
    content = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    author: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="posts"
    )
    comments: fields.ReverseRelation["Comment"]
    likes: fields.ReverseRelation["Like"]

    class Meta:
        table = "posts"


class Comment(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    content = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    post: fields.ForeignKeyRelation[Post] = fields.ForeignKeyField(
        "models.Post", related_name="comments"
    )
    author: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="comments"
    )
    replies: fields.ReverseRelation["Reply"]
    likes: fields.ReverseRelation["Like"]

    class Meta:
        table = "comments"


class Reply(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    content = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    comment: fields.ForeignKeyRelation[Comment] = fields.ForeignKeyField(
        "models.Comment", related_name="replies"
    )
    author: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="replies"
    )
    parent_reply: fields.ForeignKeyRelation["Reply"] = fields.ForeignKeyField(
        "models.Reply", related_name="child_replies", null=True
    )
    likes: fields.ReverseRelation["Like"]

    class Meta:
        table = "replies"


class Like(Model):
    id = fields.IntField(pk=True)

    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="likes"
    )
    post: fields.ForeignKeyRelation[Post] = fields.ForeignKeyField(
        "models.Post", related_name="likes", null=True
    )
    comment: fields.ForeignKeyRelation[Comment] = fields.ForeignKeyField(
        "models.Comment", related_name="likes", null=True
    )

    class Meta:
        table = "likes"