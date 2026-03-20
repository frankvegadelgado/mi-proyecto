"""Sales router — sale_orders + lines."""
from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.sales import BulkSaleOrderImport, SaleOrderCreate, SaleOrderListResponse, SaleOrderRead, SaleOrderUpdate
from app.schemas.partner import BulkImportResponse
from app.services import sales_service

router = APIRouter(prefix="/sales", tags=["sales"])

@router.post("/orders", response_model=SaleOrderRead, status_code=201)
async def create(payload: SaleOrderCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await sales_service.create_order(db, payload)

@router.get("/orders", response_model=SaleOrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200),
    search: Optional[str] = None, state: Optional[str] = None,
    partner_id: Optional[uuid.UUID] = None, user_id: Optional[uuid.UUID] = None,
    team_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db), _u=Depends(get_current_user),
):
    return await sales_service.list_orders(db, page=page, page_size=page_size, search=search, state=state, partner_id=partner_id, user_id=user_id, team_id=team_id)

@router.get("/orders/{oid}", response_model=SaleOrderRead)
async def get(oid: uuid.UUID, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await sales_service.get_order(db, oid)
    if not obj:
        raise HTTPException(404, "Order not found")
    return obj

@router.patch("/orders/{oid}", response_model=SaleOrderRead)
async def update(oid: uuid.UUID, payload: SaleOrderUpdate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await sales_service.update_order(db, oid, payload)
    if not obj:
        raise HTTPException(404, "Order not found")
    return obj

@router.delete("/orders/{oid}", status_code=204)
async def delete(oid: uuid.UUID, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    if not await sales_service.delete_order(db, oid):
        raise HTTPException(404, "Order not found")

@router.post("/orders/import/bulk", response_model=BulkImportResponse)
async def bulk_import(payload: BulkSaleOrderImport, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await sales_service.bulk_upsert_orders(db, payload)
