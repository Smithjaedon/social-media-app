from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from fastapi import Depends
from typing import Annotated
from sqlmodel import SQLModel
import os

load_dotenv()
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
port = os.getenv("DB_PORT")
name = os.getenv("DB_NAME")
host = os.getenv("DB_HOST","localhost")


DATABASE_URL = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"

engine = create_async_engine(DATABASE_URL)


async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    async with async_session_maker() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]

