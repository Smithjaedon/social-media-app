import asyncio
import random

from faker import Faker
from tortoise import Tortoise

from app.database import DATABASE_URL
from app.models import Comment, Post, User

fake = Faker()


async def seed():
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={"models": ["app.models"]},
    )
    await Tortoise.generate_schemas()

    users = await User.all()
    posts = await Post.all()
    comments = []
    for _ in range(400):
        user = random.choice(users)
        post = random.choice(posts)
        content = " ".join(fake.sentences(2))
        comment = await Comment.create(content=content, author=user, post=post)
        comments.append(comment)

    print(f"Done. {len(comments)} comments created.")
    await Tortoise.close_connections()


asyncio.run(seed())
