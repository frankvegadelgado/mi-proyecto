from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=256)
    login: Optional[str] = Field(None, max_length=256)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    lang: Optional[str] = None
    tz: Optional[str] = None
    active: bool = True
    share: bool = False

class UserCreate(UserBase): pass
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    active: Optional[bool] = None
class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class SalesTeamBase(BaseModel):
    odoo_id: Optional[int] = None
    name: str = Field(..., max_length=256)
    leader_id: Optional[uuid.UUID] = None
    alias_email: Optional[str] = None
    active: bool = True

class SalesTeamCreate(SalesTeamBase): pass
class SalesTeamRead(SalesTeamBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
