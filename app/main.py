from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from app.auth import router as auth
from app.database import TORTOISE_ORM
from app.routers import follows, posts, users

app = FastAPI()

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)

app.include_router(auth)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(follows.router)
