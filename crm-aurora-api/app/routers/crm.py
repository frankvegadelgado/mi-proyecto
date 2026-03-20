from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.crm import BulkCrmLeadImport, CrmLeadCreate, CrmLeadListResponse, CrmLeadRead, CrmLeadUpdate, CrmStageCreate, CrmStageRead, CrmTagCreate, CrmTagRead
from app.schemas.partner import BulkImportResponse
from app.services import crm_service
from sqlalchemy import select
from app.models.crm import CrmStage, CrmTag

router = APIRouter(prefix="/crm", tags=["crm"])

# ── Stages ────────────────────────────────────────────────────────────────────
@router.post("/stages", response_model=CrmStageRead, status_code=201)
async def create_stage(payload: CrmStageCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = CrmStage(**payload.model_dump())
    db.add(obj)
    await db.flush()
    return obj

@router.get("/stages", response_model=list[CrmStageRead])
async def list_stages(db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    r = await db.execute(select(CrmStage).order_by(CrmStage.sequence))
    return r.scalars().all()

# ── Tags ──────────────────────────────────────────────────────────────────────
@router.post("/tags", response_model=CrmTagRead, status_code=201)
async def create_tag(payload: CrmTagCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = CrmTag(**payload.model_dump())
    db.add(obj)
    await db.flush()
    return obj

@router.get("/tags", response_model=list[CrmTagRead])
async def list_tags(db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    r = await db.execute(select(CrmTag).order_by(CrmTag.name))
    return r.scalars().all()

# ── Leads / Opportunities ─────────────────────────────────────────────────────
@router.post("/leads", response_model=CrmLeadRead, status_code=201)
async def create(payload: CrmLeadCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await crm_service.create_lead(db, payload)

@router.get("/leads", response_model=CrmLeadListResponse)
async def list_leads(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200),
    search: Optional[str] = None, type: Optional[str] = None,
    stage_id: Optional[int] = None, user_id: Optional[uuid.UUID] = None,
    team_id: Optional[int] = None, active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db), _u=Depends(get_current_user),
):
    return await crm_service.list_leads(db, page=page, page_size=page_size, search=search, lead_type=type, stage_id=stage_id, user_id=user_id, team_id=team_id, active=active)

@router.get("/leads/{lid}", response_model=CrmLeadRead)
async def get(lid: uuid.UUID, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await crm_service.get_lead(db, lid)
    if not obj:
        raise HTTPException(404, "Lead not found")
    return obj

@router.patch("/leads/{lid}", response_model=CrmLeadRead)
async def update(lid: uuid.UUID, payload: CrmLeadUpdate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await crm_service.update_lead(db, lid, payload)
    if not obj:
        raise HTTPException(404, "Lead not found")
    return obj

@router.delete("/leads/{lid}", status_code=204)
async def delete(lid: uuid.UUID, hard: bool = False, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    if not await crm_service.delete_lead(db, lid, hard=hard):
        raise HTTPException(404, "Lead not found")

@router.post("/leads/import/bulk", response_model=BulkImportResponse)
async def bulk_import(payload: BulkCrmLeadImport, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await crm_service.bulk_upsert_leads(db, payload)
