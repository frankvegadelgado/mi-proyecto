from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CrmStageBase(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=256)
    sequence: int = 1
    is_won: bool = False
    requirements: Optional[str] = None
    team_id: Optional[int] = None

class CrmStageCreate(CrmStageBase): pass
class CrmStageRead(CrmStageBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class CrmTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    color: Optional[str] = None

class CrmTagCreate(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=128)
    color: Optional[str] = Field(None, max_length=7)


class CrmLeadBase(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=512)
    type: str = "lead"
    active: bool = True
    stage_id: Optional[int] = None
    priority: str = "0"
    kanban_state: Optional[str] = None
    probability: Optional[float] = None
    expected_revenue: Optional[float] = None
    prorated_revenue: Optional[float] = None
    recurring_revenue: Optional[float] = None
    recurring_plan: Optional[str] = None
    partner_id: Optional[uuid.UUID] = None
    partner_name: Optional[str] = None
    contact_name: Optional[str] = None
    email_from: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    country_id: Optional[int] = None
    state_id: Optional[int] = None
    user_id: Optional[uuid.UUID] = None
    team_id: Optional[int] = None
    date_open: Optional[datetime] = None
    date_closed: Optional[datetime] = None
    date_deadline: Optional[date] = None
    source_name: Optional[str] = None
    medium_name: Optional[str] = None
    campaign_name: Optional[str] = None
    referred: Optional[str] = None
    lost_reason_name: Optional[str] = None
    description: Optional[str] = None

class CrmLeadCreate(CrmLeadBase):
    tag_ids: list[int] = Field(default_factory=list)

class CrmLeadUpdate(BaseModel):
    name: Optional[str] = None
    stage_id: Optional[int] = None
    priority: Optional[str] = None
    probability: Optional[float] = None
    expected_revenue: Optional[float] = None
    partner_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    team_id: Optional[int] = None
    date_deadline: Optional[date] = None
    active: Optional[bool] = None
    tag_ids: Optional[list[int]] = None
    description: Optional[str] = None
    kanban_state: Optional[str] = None

class CrmLeadRead(CrmLeadBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    odoo_created_at: Optional[datetime] = None
    odoo_updated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    tags: list[CrmTagRead] = []

class CrmLeadListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[CrmLeadRead]


# ── Odoo import payload (crm.lead) ────────────────────────────────────────────
class OddoCrmLeadImport(BaseModel):
    id: int
    name: str
    type: str = "lead"
    active: bool = True
    stage_id: Optional[int] = None
    priority: str = "0"
    kanban_state: Optional[str] = None
    probability: Optional[float] = None
    expected_revenue: Optional[float] = None
    prorated_revenue: Optional[float] = None
    partner_id: Optional[int] = None
    partner_name: Optional[str] = None
    contact_name: Optional[str] = None
    email_from: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    country_id: Optional[int] = None
    state_id: Optional[int] = None
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    date_open: Optional[datetime] = None
    date_closed: Optional[datetime] = None
    date_deadline: Optional[date] = None
    source_id: Optional[int] = None
    medium_id: Optional[int] = None
    campaign_id: Optional[int] = None
    referred: Optional[str] = None
    lost_reason_id: Optional[int] = None
    description: Optional[str] = None
    tag_ids: list[int] = Field(default_factory=list)
    create_date: Optional[datetime] = None
    write_date: Optional[datetime] = None

class BulkCrmLeadImport(BaseModel):
    records: list[OddoCrmLeadImport]
