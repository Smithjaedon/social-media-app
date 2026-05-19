import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
import redis.asyncio as aioredis
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.models import User
from app.schemas import UserCreate, UserRead

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

password_hash = PasswordHash.recommended()

redis = aioredis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True
)
router = APIRouter()


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
        algorithm=ALGORITHM,
    )


def create_refresh_token_str() -> str:
    return str(uuid.uuid4())


# --- DB Helpers ---
# No session needed — just call the model directly


async def get_user(username: str) -> User | None:
    return await User.get_or_none(username=username)


async def get_user_by_id(user_id: uuid.UUID) -> User | None:
    return await User.get_or_none(id=user_id)


async def authenticate_user(username: str, password: str) -> User:
    user = await get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    return user


# --- Current User Dependency ---


async def get_current_user(request: Request) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = uuid.UUID(payload.get("sub"))
        jti = payload.get("jti")
    except InvalidTokenError, ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    if await redis.get(f"blacklist:{jti}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked"
        )

    user = await get_user_by_id(user_id)
    if not user or user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


TokenDep = Annotated[User, Depends(get_current_user)]


# --- Routes ---


@router.post("/register", response_model=UserRead)
async def register(user_data: UserCreate):
    existing = await get_user(user_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    user = await User.create(
        username=user_data.username,
        email=user_data.email,
        display_name=user_data.display_name,
        hashed_password=get_password_hash(user_data.password),
    )
    return user


@router.post("/token")
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials"
        )

    access_token = create_access_token(user.id)
    refresh_token_str = create_refresh_token_str()

    await redis.setex(
        f"refresh:{refresh_token_str}", REFRESH_TOKEN_EXPIRE_DAYS * 86400, str(user.id)
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_str,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    return {"message": "logged in"}


@router.post("/token/refresh")
async def refresh(request: Request, response: Response):
    refresh_token_str = request.cookies.get("refresh_token")
    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token"
        )

    user_id = await redis.get(f"refresh:{refresh_token_str}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = await get_user_by_id(uuid.UUID(user_id))
    if not user or user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    await redis.delete(f"refresh:{refresh_token_str}")

    new_refresh_str = create_refresh_token_str()
    await redis.setex(
        f"refresh:{new_refresh_str}", REFRESH_TOKEN_EXPIRE_DAYS * 86400, str(user.id)
    )

    response.set_cookie(
        key="access_token",
        value=create_access_token(user.id),
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_str,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    return {"message": "token refreshed"}


@router.post("/logout")
async def logout(request: Request, response: Response):
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
