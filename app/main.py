from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from tortoise.contrib.fastapi import register_tortoise

from app.auth import router as auth
from app.database import TORTOISE_ORM
from app.routers import bio, comments, follows, posts, users

app = FastAPI()

origins = ["http://localhost:5173", "http://localhost:5174"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)

app.include_router(auth)
app.include_router(bio.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(follows.router)
app.include_router(comments.router)

add_pagination(app)
