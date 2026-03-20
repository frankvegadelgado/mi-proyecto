from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.partner import BulkPartnerImport, BulkImportResponse, PartnerCreate, PartnerListResponse, PartnerRead, PartnerTagCreate, PartnerTagRead, PartnerUpdate
from app.services import partner_service
from sqlalchemy import select
from app.models.partner import PartnerTag

router = APIRouter(prefix="/partners", tags=["partners"])

@router.post("/", response_model=PartnerRead, status_code=201)
async def create(payload: PartnerCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await partner_service.create_partner(db, payload)

@router.get("/", response_model=PartnerListResponse)
async def list_partners(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200),
    search: Optional[str] = None, is_company: Optional[bool] = None,
    active: Optional[bool] = True, country_id: Optional[int] = None, tag_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db), _u=Depends(get_current_user),
):
    return await partner_service.list_partners(db, page=page, page_size=page_size, search=search, is_company=is_company, active=active, country_id=country_id, tag_id=tag_id)

@router.get("/{pid}", response_model=PartnerRead)
async def get(pid: uuid.UUID, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await partner_service.get_partner(db, pid)
    if not obj:
        raise HTTPException(404, "Partner not found")
    return obj

@router.patch("/{pid}", response_model=PartnerRead)
async def update(pid: uuid.UUID, payload: PartnerUpdate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await partner_service.update_partner(db, pid, payload)
    if not obj:
        raise HTTPException(404, "Partner not found")
    return obj

@router.delete("/{pid}", status_code=204)
async def delete(pid: uuid.UUID, hard: bool = False, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    if not await partner_service.delete_partner(db, pid, hard=hard):
        raise HTTPException(404, "Partner not found")

@router.post("/import/bulk", response_model=BulkImportResponse)
async def bulk_import(payload: BulkPartnerImport, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await partner_service.bulk_upsert_partners(db, payload)

# ── Partner Tags ──────────────────────────────────────────────────────────────
@router.post("/tags", response_model=PartnerTagRead, status_code=201)
async def create_tag(payload: PartnerTagCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = PartnerTag(**payload.model_dump())
    db.add(obj)
    await db.flush()
    return obj

@router.get("/tags", response_model=list[PartnerTagRead])
async def list_tags(db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    r = await db.execute(select(PartnerTag).order_by(PartnerTag.name))
    return r.scalars().all()
