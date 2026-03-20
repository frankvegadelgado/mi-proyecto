from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SaleOrderLineBase(BaseModel):
    odoo_id: Optional[int] = None
    order_id: uuid.UUID
    product_id: Optional[uuid.UUID] = None
    product_variant_id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    sequence: int = 10
    product_uom_qty: float = 1.0
    qty_delivered: Optional[float] = None
    qty_invoiced: Optional[float] = None
    qty_to_invoice: Optional[float] = None
    price_unit: Optional[float] = None
    discount: Optional[float] = None
    price_subtotal: Optional[float] = None
    price_tax: Optional[float] = None
    price_total: Optional[float] = None
    tax_names: Optional[str] = None
    is_downpayment: bool = False
    state: Optional[str] = None

class SaleOrderLineCreate(SaleOrderLineBase): pass
class SaleOrderLineRead(SaleOrderLineBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class SaleOrderBase(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=64)
    state: str = "draft"
    client_order_ref: Optional[str] = None
    partner_id: Optional[uuid.UUID] = None
    partner_invoice_id: Optional[uuid.UUID] = None
    partner_shipping_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    team_id: Optional[int] = None
    date_order: Optional[datetime] = None
    validity_date: Optional[date] = None
    commitment_date: Optional[datetime] = None
    expected_date: Optional[datetime] = None
    pricelist_id: Optional[int] = None
    payment_term_id: Optional[int] = None
    currency_name: Optional[str] = None
    amount_untaxed: Optional[float] = None
    amount_tax: Optional[float] = None
    amount_total: Optional[float] = None
    amount_to_invoice: Optional[float] = None
    invoice_status: Optional[str] = None
    note: Optional[str] = None
    internal_note: Optional[str] = None
    opportunity_id: Optional[uuid.UUID] = None
    source_name: Optional[str] = None
    medium_name: Optional[str] = None
    campaign_name: Optional[str] = None

class SaleOrderCreate(SaleOrderBase):
    order_lines: list[SaleOrderLineCreate] = Field(default_factory=list)

class SaleOrderUpdate(BaseModel):
    state: Optional[str] = None
    client_order_ref: Optional[str] = None
    validity_date: Optional[date] = None
    note: Optional[str] = None
    payment_term_id: Optional[int] = None
    pricelist_id: Optional[int] = None

class SaleOrderRead(SaleOrderBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    odoo_created_at: Optional[datetime] = None
    odoo_updated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    order_lines: list[SaleOrderLineRead] = []

class SaleOrderListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SaleOrderRead]


# ── Odoo import payload ───────────────────────────────────────────────────────
class OdooSaleOrderLineImport(BaseModel):
    id: int
    product_id: Optional[int] = None
    product_uom_qty: float = 1.0
    qty_delivered: Optional[float] = None
    qty_invoiced: Optional[float] = None
    name: Optional[str] = None
    sequence: int = 10
    price_unit: Optional[float] = None
    discount: Optional[float] = None
    price_subtotal: Optional[float] = None
    price_tax: Optional[float] = None
    price_total: Optional[float] = None
    tax_id: list[int] = Field(default_factory=list)
    is_downpayment: bool = False
    state: Optional[str] = None

class OdooSaleOrderImport(BaseModel):
    id: int
    name: str
    state: str = "draft"
    client_order_ref: Optional[str] = None
    partner_id: Optional[int] = None
    partner_invoice_id: Optional[int] = None
    partner_shipping_id: Optional[int] = None
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    date_order: Optional[datetime] = None
    validity_date: Optional[date] = None
    pricelist_id: Optional[int] = None
    payment_term_id: Optional[int] = None
    currency_id: Optional[int] = None
    amount_untaxed: Optional[float] = None
    amount_tax: Optional[float] = None
    amount_total: Optional[float] = None
    invoice_status: Optional[str] = None
    note: Optional[str] = None
    opportunity_id: Optional[int] = None
    order_line: list[OdooSaleOrderLineImport] = Field(default_factory=list)
    create_date: Optional[datetime] = None
    write_date: Optional[datetime] = None

class BulkSaleOrderImport(BaseModel):
    records: list[OdooSaleOrderImport]
