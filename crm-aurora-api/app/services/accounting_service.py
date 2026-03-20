from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.accounting import Invoice, InvoiceLine, Payment
from app.models.partner import Partner
from app.models.product import Product
from app.schemas.accounting import (
    BulkInvoiceImport, BulkPaymentImport,
    InvoiceCreate, InvoiceListResponse, InvoiceUpdate,
    PaymentCreate, PaymentListResponse, PaymentUpdate,
)
from app.schemas.partner import BulkImportResponse
from app.services.base import upsert_by_odoo_id


# ── Invoices ──────────────────────────────────────────────────────────────────
def _invoice_q():
    return select(Invoice).options(selectinload(Invoice.lines))


async def create_invoice(db: AsyncSession, payload: InvoiceCreate) -> Invoice:
    lines_data = [l.model_dump() for l in payload.lines]
    obj = Invoice(**payload.model_dump(exclude={"lines"}))
    db.add(obj)
    await db.flush()
    for ld in lines_data:
        ld["move_id"] = obj.id
        db.add(InvoiceLine(**ld))
    await db.flush()
    await db.refresh(obj, ["lines"])
    return obj


async def get_invoice(db: AsyncSession, iid: uuid.UUID) -> Optional[Invoice]:
    r = await db.execute(_invoice_q().where(Invoice.id == iid))
    return r.scalar_one_or_none()


async def list_invoices(
    db: AsyncSession,
    page: int = 1, page_size: int = 20,
    move_type: Optional[str] = None,
    state: Optional[str] = None,
    payment_state: Optional[str] = None,
    partner_id: Optional[uuid.UUID] = None,
) -> InvoiceListResponse:
    q = _invoice_q()
    if move_type:
        q = q.where(Invoice.move_type == move_type)
    if state:
        q = q.where(Invoice.state == state)
    if payment_state:
        q = q.where(Invoice.payment_state == payment_state)
    if partner_id:
        q = q.where(Invoice.partner_id == partner_id)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.order_by(Invoice.invoice_date.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list((await db.execute(q)).scalars())
    return InvoiceListResponse(total=total, page=page, page_size=page_size, items=items)


async def update_invoice(db: AsyncSession, iid: uuid.UUID, payload: InvoiceUpdate) -> Optional[Invoice]:
    obj = await get_invoice(db, iid)
    if not obj:
        return None
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    await db.flush()
    return obj


async def bulk_upsert_invoices(db: AsyncSession, payload: BulkInvoiceImport) -> BulkImportResponse:
    created = updated = 0
    errors: list[str] = []
    for rec in payload.records:
        try:
            partner_uuid: Optional[uuid.UUID] = None
            if rec.partner_id:
                r = await db.execute(select(Partner.id).where(Partner.odoo_id == rec.partner_id))
                partner_uuid = r.scalar_one_or_none()

            fields = dict(
                name=rec.name, ref=rec.ref, move_type=rec.move_type,
                state=rec.state, payment_state=rec.payment_state,
                partner_id=partner_uuid,
                invoice_date=rec.invoice_date, invoice_date_due=rec.invoice_date_due,
                currency_id=rec.currency_id, payment_term_id=rec.payment_term_id,
                amount_untaxed=rec.amount_untaxed, amount_tax=rec.amount_tax,
                amount_total=rec.amount_total, amount_residual=rec.amount_residual,
                amount_total_signed=rec.amount_total_signed,
                narration=rec.narration, invoice_origin=rec.invoice_origin,
                odoo_created_at=rec.create_date, odoo_updated_at=rec.write_date,
            )
            inv, was_created = await upsert_by_odoo_id(db, Invoice, rec.id, fields)
            await db.flush()

            for line in rec.invoice_line_ids:
                prod_uuid: Optional[uuid.UUID] = None
                if line.product_id:
                    r = await db.execute(select(Product.id).where(Product.odoo_id == line.product_id))
                    prod_uuid = r.scalar_one_or_none()
                line_fields = dict(
                    move_id=inv.id, product_id=prod_uuid,
                    name=line.name, sequence=line.sequence,
                    quantity=line.quantity, price_unit=line.price_unit,
                    discount=line.discount, price_subtotal=line.price_subtotal,
                    price_total=line.price_total, display_type=line.display_type,
                )
                await upsert_by_odoo_id(db, InvoiceLine, line.id, line_fields)

            created += was_created
            updated += not was_created
        except Exception as exc:
            errors.append(f"invoice odoo_id={rec.id}: {exc}")
    await db.flush()
    return BulkImportResponse(created=created, updated=updated, errors=errors)


# ── Payments ──────────────────────────────────────────────────────────────────
async def create_payment(db: AsyncSession, payload: PaymentCreate) -> Payment:
    obj = Payment(**payload.model_dump())
    db.add(obj)
    await db.flush()
    return obj


async def get_payment(db: AsyncSession, pid: uuid.UUID) -> Optional[Payment]:
    r = await db.execute(select(Payment).where(Payment.id == pid))
    return r.scalar_one_or_none()


async def list_payments(
    db: AsyncSession,
    page: int = 1, page_size: int = 20,
    payment_type: Optional[str] = None,
    state: Optional[str] = None,
    partner_id: Optional[uuid.UUID] = None,
) -> PaymentListResponse:
    q = select(Payment)
    if payment_type:
        q = q.where(Payment.payment_type == payment_type)
    if state:
        q = q.where(Payment.state == state)
    if partner_id:
        q = q.where(Payment.partner_id == partner_id)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.order_by(Payment.payment_date.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list((await db.execute(q)).scalars())
    return PaymentListResponse(total=total, page=page, page_size=page_size, items=items)


async def update_payment(db: AsyncSession, pid: uuid.UUID, payload: PaymentUpdate) -> Optional[Payment]:
    obj = await get_payment(db, pid)
    if not obj:
        return None
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    await db.flush()
    return obj


async def bulk_upsert_payments(db: AsyncSession, payload: BulkPaymentImport) -> BulkImportResponse:
    created = updated = 0
    errors: list[str] = []
    for rec in payload.records:
        try:
            partner_uuid: Optional[uuid.UUID] = None
            if rec.partner_id:
                r = await db.execute(select(Partner.id).where(Partner.odoo_id == rec.partner_id))
                partner_uuid = r.scalar_one_or_none()

            fields = dict(
                name=rec.name, payment_type=rec.payment_type,
                partner_type=rec.partner_type, state=rec.state,
                partner_id=partner_uuid, currency_id=rec.currency_id,
                amount=rec.amount, payment_date=rec.date, memo=rec.ref,
                odoo_created_at=rec.create_date,
            )
            _, was_created = await upsert_by_odoo_id(db, Payment, rec.id, fields)
            created += was_created
            updated += not was_created
        except Exception as exc:
            errors.append(f"payment odoo_id={rec.id}: {exc}")
    await db.flush()
    return BulkImportResponse(created=created, updated=updated, errors=errors)
