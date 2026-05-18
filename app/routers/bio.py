from fastapi import APIRouter, HTTPException

from app.auth import TokenDep
from app.models import User
from app.schemas import BioRead, BioUpdate

router = APIRouter()


@router.get("/bio", response_model=BioRead)
async def get_current_user_bio(token: TokenDep):
    """Get current user's bio"""
    user = await User.get(id=token.id)
    return user


@router.patch("/bio", response_model=BioRead)
async def update_bio(bio_update: BioUpdate, token: TokenDep):
    """Update current user's bio (PATCH only, since POST creates with null default)"""
    user = await User.get(id=token.id)

    if bio_update.bio is not None:
        user.bio = bio_update.bio

    await user.save()
    return user


@router.get("/bio/by-username/{username}", response_model=BioRead)
async def get_user_bio_by_username(username: str):
    """Get another user's bio by username"""
    user = await User.get_or_none(username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/bio/by-username/{username}", response_model=BioRead)
async def update_user_bio_by_username(username: str, bio_update: BioUpdate):
    """Update another user's bio by username (no authentication required)"""
    user = await User.get_or_none(username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if bio_update.bio is not None:
        user.bio = bio_update.bio

    await user.save()
    return user
