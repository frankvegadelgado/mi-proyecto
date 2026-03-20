from __future__ import annotations
import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductCategoryBase(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=256)
    parent_id: Optional[int] = None
    complete_name: Optional[str] = None

class ProductCategoryCreate(ProductCategoryBase): pass
class ProductCategoryRead(ProductCategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProductBase(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=512)
    description: Optional[str] = None
    description_sale: Optional[str] = None
    description_purchase: Optional[str] = None
    type: Optional[str] = None
    categ_id: Optional[int] = None
    uom_name: Optional[str] = None
    uom_po_name: Optional[str] = None
    list_price: Optional[float] = None
    standard_price: Optional[float] = None
    taxes_name: Optional[str] = None
    default_code: Optional[str] = None
    barcode: Optional[str] = None
    active: bool = True
    sale_ok: bool = True
    purchase_ok: bool = True
    can_be_expensed: bool = False
    invoice_policy: Optional[str] = None
    weight: Optional[float] = None
    volume: Optional[float] = None

class ProductCreate(ProductBase): pass
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    list_price: Optional[float] = None
    standard_price: Optional[float] = None
    active: Optional[bool] = None
    categ_id: Optional[int] = None
    default_code: Optional[str] = None

class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class ProductVariantBase(BaseModel):
    odoo_id: Optional[int] = None
    product_id: uuid.UUID
    name: Optional[str] = None
    default_code: Optional[str] = None
    barcode: Optional[str] = None
    price_extra: Optional[float] = None
    active: bool = True
    combination_indices: Optional[str] = None

class ProductVariantCreate(ProductVariantBase): pass
class ProductVariantRead(ProductVariantBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


# ── Odoo import payload ───────────────────────────────────────────────────────
class OdooProductImport(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    description_sale: Optional[str] = None
    description_purchase: Optional[str] = None
    type: Optional[str] = None
    categ_id: Optional[int] = None
    uom_id: Optional[int] = None       # resolved to name
    uom_po_id: Optional[int] = None
    list_price: Optional[float] = None
    standard_price: Optional[float] = None
    taxes_id: list[int] = Field(default_factory=list)
    default_code: Optional[str] = None
    barcode: Optional[str] = None
    active: bool = True
    sale_ok: bool = True
    purchase_ok: bool = True
    can_be_expensed: bool = False
    invoice_policy: Optional[str] = None
    weight: Optional[float] = None
    volume: Optional[float] = None
    uom_name: Optional[str] = None
    uom_po_name: Optional[str] = None

class BulkProductImport(BaseModel):
    records: list[OdooProductImport]
