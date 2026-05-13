import asyncio
import random
import uuid

from tortoise import Tortoise

from app.database import DATABASE_URL
from app.models import Follow, User


async def seed():
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={"models": ["app.models"]},
    )
    await Tortoise.generate_schemas()

    users = await User.all()
    follows = []
    follow_pairs = set()
    for _ in range(60):
        follower = random.choice(users)
        following = random.choice(users)
        if (
            follower.id != following.id
            and (follower.id, following.id) not in follow_pairs
        ):
            follow = await Follow.create(
                id=uuid.uuid4(),
                follower=follower,
                following=following,
            )
            follows.append(follow)
            follow_pairs.add((follower.id, following.id))

    print(f"Done. {len(follows)} follows created.")
    await Tortoise.close_connections()


asyncio.run(seed())
