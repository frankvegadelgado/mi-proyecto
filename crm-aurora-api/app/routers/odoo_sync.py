"""
Odoo sync trigger endpoint.
POST /api/v1/sync/odoo           → full import of all 23 models
POST /api/v1/sync/odoo?incremental=true  → only records changed since today midnight
POST /api/v1/sync/odoo?incremental=true&since=2024-01-01T00:00:00Z  → custom boundary
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user
from app.services.odoo_import import OdooImportService

router = APIRouter(prefix="/sync", tags=["odoo-sync"])


@router.post("/odoo", summary="Trigger full or incremental Odoo → Aurora sync")
async def sync_from_odoo(
    incremental: bool = Query(False, description="Only import records modified since `since`"),
    since: Optional[datetime] = Query(None, description="ISO-8601 UTC boundary for incremental sync"),
    db: AsyncSession = Depends(get_db),
    _u: str = Depends(get_current_user),
) -> list[dict]:
    svc = OdooImportService()
    if incremental:
        return await svc.run_incremental_import(db, since=since)
    return await svc.run_full_import(db)
