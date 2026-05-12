import os

from dotenv import load_dotenv
from tortoise import Tortoise

load_dotenv()
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
port = os.getenv("DB_PORT")
name = os.getenv("DB_NAME")
host = os.getenv("DB_HOST", "localhost")

DATABASE_URL = f"postgres://{user}:{password}@{host}:{port}/{name}"

TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": ["app.models"],
            "default_connection": "default",
        }
    },
}


async def create_db_and_tables():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def close_db():
    await Tortoise.close_connections()
