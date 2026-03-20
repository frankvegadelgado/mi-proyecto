from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ActivityTypeBase(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=128)
    summary: Optional[str] = None
    icon: Optional[str] = None
    decoration_type: Optional[str] = None
    delay_count: Optional[int] = None
    delay_unit: Optional[str] = None
    delay_from: Optional[str] = None
    category: Optional[str] = None

class ActivityTypeCreate(ActivityTypeBase): pass
class ActivityTypeRead(ActivityTypeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ActivityBase(BaseModel):
    odoo_id: Optional[int] = None
    activity_type_id: Optional[int] = None
    user_id: Optional[uuid.UUID] = None
    res_model: Optional[str] = None
    res_id: Optional[uuid.UUID] = None
    res_name: Optional[str] = None
    summary: Optional[str] = None
    note: Optional[str] = None
    date_deadline: Optional[date] = None
    date_done: Optional[date] = None
    state: Optional[str] = None
    calendar_event_id: Optional[uuid.UUID] = None

class ActivityCreate(ActivityBase): pass
class ActivityUpdate(BaseModel):
    summary: Optional[str] = None
    note: Optional[str] = None
    date_deadline: Optional[date] = None
    state: Optional[str] = None
    user_id: Optional[uuid.UUID] = None

class ActivityRead(ActivityBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    odoo_created_at: Optional[datetime] = None
    created_at: datetime

class ActivityListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ActivityRead]


class MessageBase(BaseModel):
    odoo_id: Optional[int] = None
    author_id: Optional[uuid.UUID] = None
    res_model: Optional[str] = None
    res_id: Optional[uuid.UUID] = None
    res_name: Optional[str] = None
    message_type: str = "comment"
    subtype_name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    date: Optional[datetime] = None
    email_from: Optional[str] = None
    reply_to: Optional[str] = None
    message_id: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    is_internal: bool = False

class MessageCreate(MessageBase): pass
class MessageRead(MessageBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime

class MessageListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[MessageRead]


class MeetingBase(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=512)
    description: Optional[str] = None
    organizer_id: Optional[uuid.UUID] = None
    start: Optional[datetime] = None
    stop: Optional[datetime] = None
    allday: bool = False
    start_date: Optional[date] = None
    stop_date: Optional[date] = None
    location: Optional[str] = None
    videocall_location: Optional[str] = None
    privacy: Optional[str] = None
    show_as: Optional[str] = None
    active: bool = True
    recurrency: bool = False
    rrule: Optional[str] = None
    opportunity_id: Optional[uuid.UUID] = None

class MeetingCreate(MeetingBase):
    attendee_ids: list[uuid.UUID] = Field(default_factory=list)

class MeetingUpdate(BaseModel):
    name: Optional[str] = None
    start: Optional[datetime] = None
    stop: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    attendee_ids: Optional[list[uuid.UUID]] = None

class MeetingRead(MeetingBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    odoo_created_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class MeetingListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[MeetingRead]


# ── Odoo import payloads ──────────────────────────────────────────────────────
class OdooActivityImport(BaseModel):
    id: int
    activity_type_id: Optional[int] = None
    user_id: Optional[int] = None
    res_model: Optional[str] = None
    res_id: Optional[int] = None
    res_name: Optional[str] = None
    summary: Optional[str] = None
    note: Optional[str] = None
    date_deadline: Optional[date] = None
    date_done: Optional[date] = None
    state: Optional[str] = None
    calendar_event_id: Optional[int] = None
    create_date: Optional[datetime] = None

class BulkActivityImport(BaseModel):
    records: list[OdooActivityImport]


class OdooMessageImport(BaseModel):
    id: int
    author_id: Optional[int] = None
    res_model: Optional[str] = None
    res_id: Optional[int] = None
    res_name: Optional[str] = None
    message_type: str = "comment"
    subtype_xmlid: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    date: Optional[datetime] = None
    email_from: Optional[str] = None
    reply_to: Optional[str] = None
    message_id: Optional[str] = None
    parent_id: Optional[int] = None
    is_internal: bool = False

class BulkMessageImport(BaseModel):
    records: list[OdooMessageImport]


class OdooMeetingImport(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    user_id: Optional[int] = None        # organizer
    start: Optional[datetime] = None
    stop: Optional[datetime] = None
    allday: bool = False
    start_date: Optional[date] = None
    stop_date: Optional[date] = None
    location: Optional[str] = None
    videocall_location: Optional[str] = None
    privacy: Optional[str] = None
    show_as: Optional[str] = None
    active: bool = True
    recurrency: bool = False
    rrule: Optional[str] = None
    opportunity_id: Optional[int] = None
    partner_ids: list[int] = Field(default_factory=list)  # attendees
    create_date: Optional[datetime] = None
    write_date: Optional[datetime] = None

class BulkMeetingImport(BaseModel):
    records: list[OdooMeetingImport]
