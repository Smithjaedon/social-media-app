import asyncio
import random
import uuid

from faker import Faker
from tortoise import Tortoise

from app.database import DATABASE_URL
from app.models import Post, User

fake = Faker()


async def seed():
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={"models": ["app.models"]},
    )
    await Tortoise.generate_schemas()

    users = await User.all()
    posts = []
    for _ in range(50):
        post = await Post.create(
            id=uuid.uuid4(),
            title=fake.sentence(nb_words=6),
            content=fake.paragraph(nb_sentences=4),
            author=random.choice(users),
        )
        posts.append(post)

    print(f"Done. {len(posts)} posts created.")
    await Tortoise.close_connections()


asyncio.run(seed())
