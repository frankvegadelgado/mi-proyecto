from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication import Activity, ActivityType, Message, Meeting, MeetingAttendee
from app.models.user import User
from app.models.partner import Partner
from app.schemas.communication import (
    ActivityCreate, ActivityListResponse, ActivityUpdate,
    BulkActivityImport, BulkMeetingImport, BulkMessageImport,
    MeetingCreate, MeetingListResponse, MeetingUpdate,
    MessageCreate, MessageListResponse,
)
from app.schemas.partner import BulkImportResponse
from app.services.base import upsert_by_odoo_id


# ── Activities ────────────────────────────────────────────────────────────────
async def create_activity(db: AsyncSession, payload: ActivityCreate) -> Activity:
    obj = Activity(**payload.model_dump())
    db.add(obj)
    await db.flush()
    return obj


async def get_activity(db: AsyncSession, aid: uuid.UUID) -> Optional[Activity]:
    r = await db.execute(select(Activity).where(Activity.id == aid))
    return r.scalar_one_or_none()


async def list_activities(
    db: AsyncSession,
    page: int = 1, page_size: int = 20,
    res_model: Optional[str] = None,
    res_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    state: Optional[str] = None,
) -> ActivityListResponse:
    q = select(Activity)
    if res_model:
        q = q.where(Activity.res_model == res_model)
    if res_id:
        q = q.where(Activity.res_id == res_id)
    if user_id:
        q = q.where(Activity.user_id == user_id)
    if state:
        q = q.where(Activity.state == state)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.order_by(Activity.date_deadline).offset((page - 1) * page_size).limit(page_size)
    items = list((await db.execute(q)).scalars())
    return ActivityListResponse(total=total, page=page, page_size=page_size, items=items)


async def update_activity(db: AsyncSession, aid: uuid.UUID, payload: ActivityUpdate) -> Optional[Activity]:
    obj = await get_activity(db, aid)
    if not obj:
        return None
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    await db.flush()
    return obj


async def delete_activity(db: AsyncSession, aid: uuid.UUID) -> bool:
    obj = await get_activity(db, aid)
    if not obj:
        return False
    await db.delete(obj)
    return True


async def bulk_upsert_activities(db: AsyncSession, payload: BulkActivityImport) -> BulkImportResponse:
    created = updated = 0
    errors: list[str] = []
    for rec in payload.records:
        try:
            user_uuid: Optional[uuid.UUID] = None
            if rec.user_id:
                r = await db.execute(select(User.id).where(User.odoo_id == rec.user_id))
                user_uuid = r.scalar_one_or_none()

            fields = dict(
                activity_type_id=rec.activity_type_id, user_id=user_uuid,
                res_model=rec.res_model, res_name=rec.res_name,
                summary=rec.summary, note=rec.note,
                date_deadline=rec.date_deadline, state=rec.state,
                odoo_created_at=rec.create_date,
            )
            _, was_created = await upsert_by_odoo_id(db, Activity, rec.id, fields)
            created += was_created
            updated += not was_created
        except Exception as exc:
            errors.append(f"activity odoo_id={rec.id}: {exc}")
    await db.flush()
    return BulkImportResponse(created=created, updated=updated, errors=errors)


# ── Messages ──────────────────────────────────────────────────────────────────
async def create_message(db: AsyncSession, payload: MessageCreate) -> Message:
    obj = Message(**payload.model_dump())
    db.add(obj)
    await db.flush()
    return obj


async def list_messages(
    db: AsyncSession,
    page: int = 1, page_size: int = 50,
    res_model: Optional[str] = None,
    res_id: Optional[uuid.UUID] = None,
    author_id: Optional[uuid.UUID] = None,
    message_type: Optional[str] = None,
) -> MessageListResponse:
    q = select(Message)
    if res_model:
        q = q.where(Message.res_model == res_model)
    if res_id:
        q = q.where(Message.res_id == res_id)
    if author_id:
        q = q.where(Message.author_id == author_id)
    if message_type:
        q = q.where(Message.message_type == message_type)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.order_by(Message.date.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list((await db.execute(q)).scalars())
    return MessageListResponse(total=total, page=page, page_size=page_size, items=items)


async def bulk_upsert_messages(db: AsyncSession, payload: BulkMessageImport) -> BulkImportResponse:
    created = updated = 0
    errors: list[str] = []
    for rec in payload.records:
        try:
            author_uuid: Optional[uuid.UUID] = None
            if rec.author_id:
                r = await db.execute(select(User.id).where(User.odoo_id == rec.author_id))
                author_uuid = r.scalar_one_or_none()

            fields = dict(
                author_id=author_uuid, res_model=rec.res_model, res_name=rec.res_name,
                message_type=rec.message_type, subject=rec.subject,
                body=rec.body, date=rec.date, email_from=rec.email_from,
                message_id=rec.message_id, is_internal=rec.is_internal,
            )
            _, was_created = await upsert_by_odoo_id(db, Message, rec.id, fields)
            created += was_created
            updated += not was_created
        except Exception as exc:
            errors.append(f"message odoo_id={rec.id}: {exc}")
    await db.flush()
    return BulkImportResponse(created=created, updated=updated, errors=errors)


# ── Meetings ──────────────────────────────────────────────────────────────────
async def create_meeting(db: AsyncSession, payload: MeetingCreate) -> Meeting:
    attendee_ids = payload.attendee_ids
    data = payload.model_dump(exclude={"attendee_ids"})
    obj = Meeting(**data)
    db.add(obj)
    await db.flush()
    if attendee_ids:
        r = await db.execute(select(Partner).where(Partner.id.in_(attendee_ids)))
        obj.attendees = list(r.scalars())
    await db.flush()
    return obj


async def get_meeting(db: AsyncSession, mid: uuid.UUID) -> Optional[Meeting]:
    r = await db.execute(select(Meeting).where(Meeting.id == mid))
    return r.scalar_one_or_none()


async def list_meetings(
    db: AsyncSession,
    page: int = 1, page_size: int = 20,
    organizer_id: Optional[uuid.UUID] = None,
    active: Optional[bool] = True,
) -> MeetingListResponse:
    q = select(Meeting)
    if organizer_id:
        q = q.where(Meeting.organizer_id == organizer_id)
    if active is not None:
        q = q.where(Meeting.active == active)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.order_by(Meeting.start.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list((await db.execute(q)).scalars())
    return MeetingListResponse(total=total, page=page, page_size=page_size, items=items)


async def update_meeting(db: AsyncSession, mid: uuid.UUID, payload: MeetingUpdate) -> Optional[Meeting]:
    obj = await get_meeting(db, mid)
    if not obj:
        return None
    for k, v in payload.model_dump(exclude_none=True, exclude={"attendee_ids"}).items():
        setattr(obj, k, v)
    if payload.attendee_ids is not None:
        r = await db.execute(select(Partner).where(Partner.id.in_(payload.attendee_ids)))
        obj.attendees = list(r.scalars())
    await db.flush()
    return obj


async def delete_meeting(db: AsyncSession, mid: uuid.UUID) -> bool:
    obj = await get_meeting(db, mid)
    if not obj:
        return False
    obj.active = False
    return True


async def bulk_upsert_meetings(db: AsyncSession, payload: BulkMeetingImport) -> BulkImportResponse:
    created = updated = 0
    errors: list[str] = []
    for rec in payload.records:
        try:
            organizer_uuid: Optional[uuid.UUID] = None
            if rec.user_id:
                r = await db.execute(select(User.id).where(User.odoo_id == rec.user_id))
                organizer_uuid = r.scalar_one_or_none()

            fields = dict(
                name=rec.name, description=rec.description,
                organizer_id=organizer_uuid,
                start=rec.start, stop=rec.stop, allday=rec.allday,
                start_date=rec.start_date, stop_date=rec.stop_date,
                location=rec.location, videocall_location=rec.videocall_location,
                privacy=rec.privacy, show_as=rec.show_as, active=rec.active,
                recurrency=rec.recurrency, rrule=rec.rrule,
                odoo_created_at=rec.create_date, odoo_updated_at=rec.write_date,
            )
            obj, was_created = await upsert_by_odoo_id(db, Meeting, rec.id, fields)
            await db.flush()

            # Sync attendees
            if rec.partner_ids:
                partners_r = await db.execute(
                    select(Partner).where(Partner.odoo_id.in_(rec.partner_ids))
                )
                obj.attendees = list(partners_r.scalars())

            created += was_created
            updated += not was_created
        except Exception as exc:
            errors.append(f"meeting odoo_id={rec.id}: {exc}")
    await db.flush()
    return BulkImportResponse(created=created, updated=updated, errors=errors)
