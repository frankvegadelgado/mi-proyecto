from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.communication import (
    ActivityCreate, ActivityListResponse, ActivityRead, ActivityUpdate,
    BulkActivityImport, BulkMeetingImport, BulkMessageImport,
    MeetingCreate, MeetingListResponse, MeetingRead, MeetingUpdate,
    MessageCreate, MessageListResponse, MessageRead,
)
from app.schemas.partner import BulkImportResponse
from app.services import communication_service

router = APIRouter(prefix="/communication", tags=["communication"])

# ── Activities ────────────────────────────────────────────────────────────────
@router.post("/activities", response_model=ActivityRead, status_code=201)
async def create_activity(payload: ActivityCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await communication_service.create_activity(db, payload)

@router.get("/activities", response_model=ActivityListResponse)
async def list_activities(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200),
    res_model: Optional[str] = None, res_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None, state: Optional[str] = None,
    db: AsyncSession = Depends(get_db), _u=Depends(get_current_user),
):
    return await communication_service.list_activities(db, page=page, page_size=page_size, res_model=res_model, res_id=res_id, user_id=user_id, state=state)

@router.patch("/activities/{aid}", response_model=ActivityRead)
async def update_activity(aid: uuid.UUID, payload: ActivityUpdate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await communication_service.update_activity(db, aid, payload)
    if not obj:
        raise HTTPException(404, "Activity not found")
    return obj

@router.delete("/activities/{aid}", status_code=204)
async def delete_activity(aid: uuid.UUID, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    if not await communication_service.delete_activity(db, aid):
        raise HTTPException(404, "Activity not found")

@router.post("/activities/import/bulk", response_model=BulkImportResponse)
async def bulk_activities(payload: BulkActivityImport, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await communication_service.bulk_upsert_activities(db, payload)

# ── Messages ──────────────────────────────────────────────────────────────────
@router.post("/messages", response_model=MessageRead, status_code=201)
async def create_message(payload: MessageCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await communication_service.create_message(db, payload)

@router.get("/messages", response_model=MessageListResponse)
async def list_messages(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500),
    res_model: Optional[str] = None, res_id: Optional[uuid.UUID] = None,
    author_id: Optional[uuid.UUID] = None, message_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db), _u=Depends(get_current_user),
):
    return await communication_service.list_messages(db, page=page, page_size=page_size, res_model=res_model, res_id=res_id, author_id=author_id, message_type=message_type)

@router.post("/messages/import/bulk", response_model=BulkImportResponse)
async def bulk_messages(payload: BulkMessageImport, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await communication_service.bulk_upsert_messages(db, payload)

# ── Meetings ──────────────────────────────────────────────────────────────────
@router.post("/meetings", response_model=MeetingRead, status_code=201)
async def create_meeting(payload: MeetingCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await communication_service.create_meeting(db, payload)

@router.get("/meetings", response_model=MeetingListResponse)
async def list_meetings(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200),
    organizer_id: Optional[uuid.UUID] = None, active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db), _u=Depends(get_current_user),
):
    return await communication_service.list_meetings(db, page=page, page_size=page_size, organizer_id=organizer_id, active=active)

@router.get("/meetings/{mid}", response_model=MeetingRead)
async def get_meeting(mid: uuid.UUID, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await communication_service.get_meeting(db, mid)
    if not obj:
        raise HTTPException(404, "Meeting not found")
    return obj

@router.patch("/meetings/{mid}", response_model=MeetingRead)
async def update_meeting(mid: uuid.UUID, payload: MeetingUpdate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await communication_service.update_meeting(db, mid, payload)
    if not obj:
        raise HTTPException(404, "Meeting not found")
    return obj

@router.delete("/meetings/{mid}", status_code=204)
async def delete_meeting(mid: uuid.UUID, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    if not await communication_service.delete_meeting(db, mid):
        raise HTTPException(404, "Meeting not found")

@router.post("/meetings/import/bulk", response_model=BulkImportResponse)
async def bulk_meetings(payload: BulkMeetingImport, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await communication_service.bulk_upsert_meetings(db, payload)
