import asyncio
import random
import uuid

from faker import Faker
from tortoise import Tortoise

from app.database import DATABASE_URL
from app.models import Follow, User

fake = Faker()


async def seed():
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={"models": ["app.models"]},
    )
    await Tortoise.generate_schemas()

    users = await User.all()
    bios = []
    for _ in range(80):
        user = random.choice(users)
        user.bio = fake.sentence(nb_words=12)
        await user.save()
        bios.append(user)

    print(f"Done. {len(bios)} bios modified.")
    await Tortoise.close_connections()


asyncio.run(seed())
