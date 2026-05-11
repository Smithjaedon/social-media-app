import os
import uuid
from datetime import timedelta, timezone, datetime
from typing import Annotated

import jwt
import redis.asyncio as aioredis
from fastapi import Depends, APIRouter, HTTPException, status, Response, Request
from jwt import InvalidTokenError
from dotenv import load_dotenv
from pwdlib import PasswordHash
from sqlalchemy import select

from app.database import SessionDep
from fastapi.security import OAuth2PasswordRequestForm

from app.models import User
from app.schemas import UserCreate, UserRead

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")


redis = aioredis.from_url("redis://localhost:6379", decode_responses=True)
router = APIRouter()
# --- Models ---
# class User(SQLModel, table=True):
#     id: uuid.UUID | None = Field(default_factory=uuid.uuid7, primary_key=True)
#     username: str = Field(index=True, unique=True)
#     email: str
#     hashed_password: str
#     disabled: bool = False
#

# class UserCreate(BaseModel):
#     username: str
#     email: str
#     password: str
#
# class UserRead(BaseModel):
#     id: uuid.UUID
#     username: str
#     email: str
#     disabled: bool

# class UserDeleteById(BaseModel):
#     id: uuid.UUID
#
# class UserDeleteByUsername(BaseModel):
#     username: str


# --- Helpers ---

def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def create_access_token(user_id: uuid.UUID) -> str:
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "jti": jti},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def create_refresh_token_str() -> str:
    return str(uuid.uuid4())


# --- DB Helpers ---

async def get_user(session: SessionDep, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalars().first()

async def get_user_by_id(session: SessionDep, user_id: uuid.UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

async def authenticate_user(session: SessionDep, username: str, password: str) -> User | bool:
    user = await get_user(session, username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# --- Current User Dependency ---

async def get_current_user(request: Request, session: SessionDep) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = uuid.UUID(payload.get("sub"))
        jti = payload.get("jti")
    except (InvalidTokenError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


    if await redis.get(f"blacklist:{jti}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    user = await get_user_by_id(session, user_id)
    if not user or user.disabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

TokenDep = Annotated[User, Depends(get_current_user)]
# --- Routes ---

@router.post("/register", response_model=UserRead)
async def register(user_data: UserCreate, session: SessionDep):
    existing = await get_user(session, user_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/token")
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
):
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")

    access_token = create_access_token(user.id)
    refresh_token_str = create_refresh_token_str()

    await redis.setex(f"refresh:{refresh_token_str}", REFRESH_TOKEN_EXPIRE_DAYS * 86400, str(user.id))

    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="lax", max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie(key="refresh_token", value=refresh_token_str, httponly=True, secure=True, samesite="lax", max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    return {"message": "logged in"}


@router.post("/token/refresh")
async def refresh(request: Request, response: Response, session: SessionDep):
    refresh_token_str = request.cookies.get("refresh_token")
    if not refresh_token_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    user_id = await redis.get(f"refresh:{refresh_token_str}")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    user = await get_user_by_id(session, uuid.UUID(user_id))
    if not user or user.disabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    await redis.delete(f"refresh:{refresh_token_str}")

    new_refresh_str = create_refresh_token_str()
    await redis.setex(f"refresh:{new_refresh_str}", REFRESH_TOKEN_EXPIRE_DAYS * 86400, str(user.id))

    response.set_cookie(key="access_token", value=create_access_token(user.id), httponly=True, secure=True, samesite="lax", max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie(key="refresh_token", value=new_refresh_str, httponly=True, secure=True, samesite="lax", max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    return {"message": "token refreshed"}


@router.post("/logout")
async def logout(request: Request, response: Response, session: SessionDep):
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                ttl = exp - int(datetime.now(timezone.utc).timestamp())
                if ttl > 0:
                    await redis.setex(f"blacklist:{jti}", ttl, "1")
        except InvalidTokenError:
            pass

    refresh_token_str = request.cookies.get("refresh_token")
    if refresh_token_str:
        await redis.delete(f"refresh:{refresh_token_str}")

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "logged out"}


@router.get("/users/me/", response_model=UserRead)
async def read_me(current_user: TokenDep):
    return current_user
