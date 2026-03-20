from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PartnerTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    color: Optional[str] = None

class PartnerTagCreate(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=128)
    color: Optional[str] = Field(None, max_length=7)


class PartnerBase(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=256)
    is_company: bool = False
    parent_id: Optional[uuid.UUID] = None
    company_name: Optional[str] = None
    company_type: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    vat: Optional[str] = None
    ref: Optional[str] = None
    street: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    state_id: Optional[int] = None
    country_id: Optional[int] = None
    customer_rank: int = 0
    supplier_rank: int = 0
    partner_type: Optional[str] = None
    lang: Optional[str] = None
    tz: Optional[str] = None
    payment_term_id: Optional[int] = None
    notes: Optional[str] = None
    active: bool = True

class PartnerCreate(PartnerBase):
    tag_ids: list[int] = Field(default_factory=list)

class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    vat: Optional[str] = None
    street: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    state_id: Optional[int] = None
    country_id: Optional[int] = None
    customer_rank: Optional[int] = None
    supplier_rank: Optional[int] = None
    notes: Optional[str] = None
    active: Optional[bool] = None
    tag_ids: Optional[list[int]] = None

class PartnerRead(PartnerBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    odoo_created_at: Optional[datetime] = None
    odoo_updated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    tags: list[PartnerTagRead] = []


class PartnerListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[PartnerRead]


# ── Odoo import payload (res.partner) ────────────────────────────────────────
class OdooPartnerImport(BaseModel):
    id: int
    name: str
    is_company: bool = False
    parent_id: Optional[int] = None
    company_name: Optional[str] = None
    company_type: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    vat: Optional[str] = None
    ref: Optional[str] = None
    street: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    state_id: Optional[int] = None
    country_id: Optional[int] = None
    customer_rank: int = 0
    supplier_rank: int = 0
    partner_type: Optional[str] = None
    lang: Optional[str] = None
    tz: Optional[str] = None
    property_payment_term_id: Optional[int] = None
    comment: Optional[str] = None
    active: bool = True
    category_id: list[int] = Field(default_factory=list)
    create_date: Optional[datetime] = None
    write_date: Optional[datetime] = None


class BulkPartnerImport(BaseModel):
    records: list[OdooPartnerImport]

class BulkImportResponse(BaseModel):
    created: int
    updated: int
    errors: list[str] = []
