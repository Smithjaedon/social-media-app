from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.auth import router as auth
from app.database import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(auth)
