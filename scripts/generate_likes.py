import asyncio
import random

from tortoise import Tortoise

from app.database import DATABASE_URL
from app.models import Like, Post, User


async def seed():
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={"models": ["app.models"]},
    )
    await Tortoise.generate_schemas()

    users = await User.all()
    posts = await Post.all()
    likes = []
    liked_pairs = set()
    for _ in range(100):
        user = random.choice(users)
        post = random.choice(posts)
        if (user.id, post.id) not in liked_pairs:
            like = await Like.create(user=user, post=post)
            likes.append(like)
            liked_pairs.add((user.id, post.id))

    print(f"Done. {len(likes)} likes created.")
    await Tortoise.close_connections()


asyncio.run(seed())
