"""
Shared helpers for all domain services.
"""
from __future__ import annotations
from typing import Any, Type, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Base

M = TypeVar("M", bound=Base)


async def upsert_by_odoo_id(
    db: AsyncSession,
    model: Type[M],
    odoo_id: int,
    fields: dict[str, Any],
) -> tuple[M, bool]:
    """
    Fetch a row by odoo_id; create it if missing.
    Returns (instance, created:bool).
    """
    result = await db.execute(select(model).where(model.odoo_id == odoo_id))
    obj = result.scalar_one_or_none()
    created = False
    if obj is None:
        obj = model(odoo_id=odoo_id, **fields)
        db.add(obj)
        created = True
    else:
        for k, v in fields.items():
            setattr(obj, k, v)
    return obj, created


def m2o(val: Any) -> int | None:
    """Normalise Odoo many2one field: [id, name] → int, False → None."""
    if isinstance(val, (list, tuple)) and val:
        return int(val[0])
    if isinstance(val, int):
        return val
    return None


def m2m(val: Any) -> list[int]:
    """Normalise Odoo many2many field: [id, ...] → list[int]."""
    if isinstance(val, list):
        return [int(v) for v in val if isinstance(v, int)]
    return []
