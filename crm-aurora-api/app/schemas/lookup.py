from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CurrencyBase(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=64)
    symbol: Optional[str] = Field(None, max_length=8)
    code: Optional[str] = Field(None, max_length=3)
    rounding: Optional[float] = None
    active: bool = True

class CurrencyCreate(CurrencyBase): pass
class CurrencyRead(CurrencyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class CountryBase(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=128)
    code: Optional[str] = Field(None, max_length=3)
    phone_code: Optional[str] = Field(None, max_length=10)
    currency_id: Optional[int] = None

class CountryCreate(CountryBase): pass
class CountryRead(CountryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class StateBase(BaseModel):
    odoo_id: Optional[int] = None
    country_id: int
    name: str = Field(..., max_length=128)
    code: Optional[str] = Field(None, max_length=10)

class StateCreate(StateBase): pass
class StateRead(StateBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PaymentTermBase(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=256)
    note: Optional[str] = None
    active: bool = True

class PaymentTermCreate(PaymentTermBase): pass
class PaymentTermRead(PaymentTermBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PricelistBase(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=256)
    currency_id: Optional[int] = None
    active: bool = True

class PricelistCreate(PricelistBase): pass
class PricelistRead(PricelistBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PricelistItemBase(BaseModel):
    odoo_id: Optional[int] = None
    pricelist_id: int
    product_id: Optional[str] = None
    compute_price: Optional[str] = None
    fixed_price: Optional[float] = None
    percent_price: Optional[float] = None
    price_discount: Optional[float] = None
    min_quantity: Optional[float] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None

class PricelistItemCreate(PricelistItemBase): pass
class PricelistItemRead(PricelistItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
