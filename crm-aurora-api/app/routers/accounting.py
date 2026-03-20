from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.accounting import (
    BulkInvoiceImport, BulkPaymentImport,
    InvoiceCreate, InvoiceListResponse, InvoiceRead, InvoiceUpdate,
    PaymentCreate, PaymentListResponse, PaymentRead, PaymentUpdate,
)
from app.schemas.partner import BulkImportResponse
from app.services import accounting_service

router = APIRouter(prefix="/accounting", tags=["accounting"])

# ── Invoices ──────────────────────────────────────────────────────────────────
@router.post("/invoices", response_model=InvoiceRead, status_code=201)
async def create_invoice(payload: InvoiceCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await accounting_service.create_invoice(db, payload)

@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200),
    move_type: Optional[str] = None, state: Optional[str] = None,
    payment_state: Optional[str] = None, partner_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db), _u=Depends(get_current_user),
):
    return await accounting_service.list_invoices(db, page=page, page_size=page_size, move_type=move_type, state=state, payment_state=payment_state, partner_id=partner_id)

@router.get("/invoices/{iid}", response_model=InvoiceRead)
async def get_invoice(iid: uuid.UUID, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await accounting_service.get_invoice(db, iid)
    if not obj:
        raise HTTPException(404, "Invoice not found")
    return obj

@router.patch("/invoices/{iid}", response_model=InvoiceRead)
async def update_invoice(iid: uuid.UUID, payload: InvoiceUpdate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await accounting_service.update_invoice(db, iid, payload)
    if not obj:
        raise HTTPException(404, "Invoice not found")
    return obj

@router.post("/invoices/import/bulk", response_model=BulkImportResponse)
async def bulk_invoices(payload: BulkInvoiceImport, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await accounting_service.bulk_upsert_invoices(db, payload)

# ── Payments ──────────────────────────────────────────────────────────────────
@router.post("/payments", response_model=PaymentRead, status_code=201)
async def create_payment(payload: PaymentCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await accounting_service.create_payment(db, payload)

@router.get("/payments", response_model=PaymentListResponse)
async def list_payments(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200),
    payment_type: Optional[str] = None, state: Optional[str] = None,
    partner_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db), _u=Depends(get_current_user),
):
    return await accounting_service.list_payments(db, page=page, page_size=page_size, payment_type=payment_type, state=state, partner_id=partner_id)

@router.get("/payments/{pid}", response_model=PaymentRead)
async def get_payment(pid: uuid.UUID, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await accounting_service.get_payment(db, pid)
    if not obj:
        raise HTTPException(404, "Payment not found")
    return obj

@router.patch("/payments/{pid}", response_model=PaymentRead)
async def update_payment(pid: uuid.UUID, payload: PaymentUpdate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await accounting_service.update_payment(db, pid, payload)
    if not obj:
        raise HTTPException(404, "Payment not found")
    return obj

@router.post("/payments/import/bulk", response_model=BulkImportResponse)
async def bulk_payments(payload: BulkPaymentImport, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return await accounting_service.bulk_upsert_payments(db, payload)
