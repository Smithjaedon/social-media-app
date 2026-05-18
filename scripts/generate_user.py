import asyncio
import random
import uuid

from faker import Faker
from pwdlib import PasswordHash
from tortoise import Tortoise

from app.database import DATABASE_URL
from app.models import User

fake = Faker()
pwd_hash = PasswordHash.recommended()


async def seed():
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={"models": ["app.models"]},
    )
    await Tortoise.generate_schemas()

    users = []
    for _ in range(100):
        user = await User.create(
            id=uuid.uuid4(),
            display_name=fake.name(),
            username=fake.unique.user_name(),
            email=fake.unique.email(),
            hashed_password=pwd_hash.hash("password123"),
        )
        users.append(user)
    print(f"Done. {len(users)} users created.")
    await Tortoise.close_connections()


asyncio.run(seed())
