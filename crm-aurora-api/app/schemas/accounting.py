from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class InvoiceLineBase(BaseModel):
    odoo_id: Optional[int] = None
    move_id: uuid.UUID
    product_id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    sequence: int = 10
    account_name: Optional[str] = None
    quantity: Optional[float] = None
    price_unit: Optional[float] = None
    discount: Optional[float] = None
    price_subtotal: Optional[float] = None
    price_total: Optional[float] = None
    tax_names: Optional[str] = None
    display_type: Optional[str] = None

class InvoiceLineCreate(InvoiceLineBase): pass
class InvoiceLineRead(InvoiceLineBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class InvoiceBase(BaseModel):
    odoo_id: Optional[int] = None
    name: Optional[str] = None
    ref: Optional[str] = None
    move_type: str
    state: str = "draft"
    payment_state: Optional[str] = None
    partner_id: Optional[uuid.UUID] = None
    partner_shipping_id: Optional[uuid.UUID] = None
    invoice_date: Optional[date] = None
    invoice_date_due: Optional[date] = None
    delivery_date: Optional[date] = None
    currency_id: Optional[int] = None
    payment_term_id: Optional[int] = None
    amount_untaxed: Optional[float] = None
    amount_tax: Optional[float] = None
    amount_total: Optional[float] = None
    amount_residual: Optional[float] = None
    amount_total_signed: Optional[float] = None
    sale_order_ids: Optional[str] = None
    narration: Optional[str] = None
    invoice_origin: Optional[str] = None
    fiscal_position_name: Optional[str] = None
    reversed_entry_id: Optional[uuid.UUID] = None

class InvoiceCreate(InvoiceBase):
    lines: list[InvoiceLineCreate] = Field(default_factory=list)

class InvoiceUpdate(BaseModel):
    state: Optional[str] = None
    payment_state: Optional[str] = None
    amount_residual: Optional[float] = None
    invoice_date_due: Optional[date] = None
    narration: Optional[str] = None

class InvoiceRead(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    odoo_created_at: Optional[datetime] = None
    odoo_updated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineRead] = []

class InvoiceListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[InvoiceRead]


class PaymentBase(BaseModel):
    odoo_id: Optional[int] = None
    name: Optional[str] = None
    payment_type: str
    partner_type: Optional[str] = None
    state: str = "draft"
    partner_id: Optional[uuid.UUID] = None
    currency_id: Optional[int] = None
    payment_method_name: Optional[str] = None
    journal_name: Optional[str] = None
    amount: float
    payment_date: Optional[date] = None
    memo: Optional[str] = None
    destination_account_name: Optional[str] = None
    reconciled_invoice_ids: Optional[str] = None

class PaymentCreate(PaymentBase): pass
class PaymentUpdate(BaseModel):
    state: Optional[str] = None
    memo: Optional[str] = None
    payment_date: Optional[date] = None

class PaymentRead(PaymentBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    odoo_created_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class PaymentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[PaymentRead]


# ── Odoo import payloads ──────────────────────────────────────────────────────
class OdooInvoiceLineImport(BaseModel):
    id: int
    product_id: Optional[int] = None
    name: Optional[str] = None
    sequence: int = 10
    account_id: Optional[int] = None   # resolved to name
    quantity: Optional[float] = None
    price_unit: Optional[float] = None
    discount: Optional[float] = None
    price_subtotal: Optional[float] = None
    price_total: Optional[float] = None
    tax_ids: list[int] = Field(default_factory=list)
    display_type: Optional[str] = None

class OdooInvoiceImport(BaseModel):
    id: int
    name: Optional[str] = None
    ref: Optional[str] = None
    move_type: str
    state: str = "draft"
    payment_state: Optional[str] = None
    partner_id: Optional[int] = None
    partner_shipping_id: Optional[int] = None
    invoice_date: Optional[date] = None
    invoice_date_due: Optional[date] = None
    currency_id: Optional[int] = None
    payment_term_id: Optional[int] = None
    amount_untaxed: Optional[float] = None
    amount_tax: Optional[float] = None
    amount_total: Optional[float] = None
    amount_residual: Optional[float] = None
    amount_total_signed: Optional[float] = None
    narration: Optional[str] = None
    invoice_origin: Optional[str] = None
    invoice_line_ids: list[OdooInvoiceLineImport] = Field(default_factory=list)
    create_date: Optional[datetime] = None
    write_date: Optional[datetime] = None

class BulkInvoiceImport(BaseModel):
    records: list[OdooInvoiceImport]


class OdooPaymentImport(BaseModel):
    id: int
    name: Optional[str] = None
    payment_type: str
    partner_type: Optional[str] = None
    state: str = "draft"
    partner_id: Optional[int] = None
    currency_id: Optional[int] = None
    payment_method_id: Optional[int] = None
    journal_id: Optional[int] = None
    amount: float = 0.0
    date: Optional[date] = None
    ref: Optional[str] = None
    create_date: Optional[datetime] = None

class BulkPaymentImport(BaseModel):
    records: list[OdooPaymentImport]
