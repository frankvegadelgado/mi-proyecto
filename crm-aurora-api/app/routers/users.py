from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import SalesTeam, User
from app.schemas.user import SalesTeamCreate, SalesTeamRead, UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead, status_code=201)
async def create(payload: UserCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = User(**payload.model_dump()); db.add(obj); await db.flush(); return obj

@router.get("/", response_model=list[UserRead])
async def list_users(
    search: Optional[str] = None, active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db), _u=Depends(get_current_user),
):
    q = select(User)
    if search:
        q = q.where(User.name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%"))
    if active is not None:
        q = q.where(User.active == active)
    return (await db.execute(q.order_by(User.name))).scalars().all()

@router.get("/{uid}", response_model=UserRead)
async def get(uid: uuid.UUID, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await db.get(User, uid)
    if not obj:
        raise HTTPException(404, "User not found")
    return obj

@router.patch("/{uid}", response_model=UserRead)
async def update(uid: uuid.UUID, payload: UserUpdate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await db.get(User, uid)
    if not obj:
        raise HTTPException(404, "User not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    await db.flush()
    return obj

# ── Sales Teams ───────────────────────────────────────────────────────────────
@router.post("/teams", response_model=SalesTeamRead, status_code=201)
async def create_team(payload: SalesTeamCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = SalesTeam(**payload.model_dump()); db.add(obj); await db.flush(); return obj

@router.get("/teams", response_model=list[SalesTeamRead])
async def list_teams(db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return (await db.execute(select(SalesTeam).order_by(SalesTeam.name))).scalars().all()
