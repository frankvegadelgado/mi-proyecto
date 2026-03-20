from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sales import SaleOrder, SaleOrderLine
from app.models.partner import Partner
from app.models.user import User, SalesTeam
from app.models.product import Product
from app.schemas.sales import (
    BulkSaleOrderImport, SaleOrderCreate, SaleOrderListResponse, SaleOrderUpdate,
)
from app.schemas.partner import BulkImportResponse
from app.services.base import upsert_by_odoo_id


def _q():
    return select(SaleOrder).options(selectinload(SaleOrder.order_lines))


async def create_order(db: AsyncSession, payload: SaleOrderCreate) -> SaleOrder:
    lines_data = [l.model_dump() for l in payload.order_lines]
    data = payload.model_dump(exclude={"order_lines"})
    obj = SaleOrder(**data)
    db.add(obj)
    await db.flush()
    for ld in lines_data:
        ld["order_id"] = obj.id
        db.add(SaleOrderLine(**ld))
    await db.flush()
    await db.refresh(obj, ["order_lines"])
    return obj


async def get_order(db: AsyncSession, oid: uuid.UUID) -> Optional[SaleOrder]:
    r = await db.execute(_q().where(SaleOrder.id == oid))
    return r.scalar_one_or_none()


async def list_orders(
    db: AsyncSession,
    page: int = 1, page_size: int = 20,
    search: Optional[str] = None,
    state: Optional[str] = None,
    partner_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    team_id: Optional[int] = None,
) -> SaleOrderListResponse:
    q = _q()
    if search:
        q = q.where(SaleOrder.name.ilike(f"%{search}%") | SaleOrder.client_order_ref.ilike(f"%{search}%"))
    if state:
        q = q.where(SaleOrder.state == state)
    if partner_id:
        q = q.where(SaleOrder.partner_id == partner_id)
    if user_id:
        q = q.where(SaleOrder.user_id == user_id)
    if team_id:
        q = q.where(SaleOrder.team_id == team_id)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.order_by(SaleOrder.date_order.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list((await db.execute(q)).scalars())
    return SaleOrderListResponse(total=total, page=page, page_size=page_size, items=items)


async def update_order(db: AsyncSession, oid: uuid.UUID, payload: SaleOrderUpdate) -> Optional[SaleOrder]:
    obj = await get_order(db, oid)
    if not obj:
        return None
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    await db.flush()
    return obj


async def delete_order(db: AsyncSession, oid: uuid.UUID) -> bool:
    obj = await get_order(db, oid)
    if not obj:
        return False
    await db.delete(obj)
    return True


async def bulk_upsert_orders(db: AsyncSession, payload: BulkSaleOrderImport) -> BulkImportResponse:
    created = updated = 0
    errors: list[str] = []

    for rec in payload.records:
        try:
            async def resolve_partner(odoo_pid):
                if not odoo_pid:
                    return None
                r = await db.execute(select(Partner.id).where(Partner.odoo_id == odoo_pid))
                return r.scalar_one_or_none()

            partner_uuid = await resolve_partner(rec.partner_id)
            invoice_uuid = await resolve_partner(rec.partner_invoice_id)
            shipping_uuid = await resolve_partner(rec.partner_shipping_id)

            user_uuid: Optional[uuid.UUID] = None
            if rec.user_id:
                r = await db.execute(select(User.id).where(User.odoo_id == rec.user_id))
                user_uuid = r.scalar_one_or_none()

            team_id: Optional[int] = None
            if rec.team_id:
                r = await db.execute(select(SalesTeam.id).where(SalesTeam.odoo_id == rec.team_id))
                team_id = r.scalar_one_or_none()

            fields = dict(
                name=rec.name, state=rec.state,
                client_order_ref=rec.client_order_ref,
                partner_id=partner_uuid,
                partner_invoice_id=invoice_uuid,
                partner_shipping_id=shipping_uuid,
                user_id=user_uuid, team_id=team_id,
                date_order=rec.date_order, validity_date=rec.validity_date,
                pricelist_id=rec.pricelist_id, payment_term_id=rec.payment_term_id,
                amount_untaxed=rec.amount_untaxed, amount_tax=rec.amount_tax,
                amount_total=rec.amount_total, invoice_status=rec.invoice_status,
                note=rec.note,
                odoo_created_at=rec.create_date, odoo_updated_at=rec.write_date,
            )
            order, was_created = await upsert_by_odoo_id(db, SaleOrder, rec.id, fields)
            await db.flush()

            # Upsert lines
            for line in rec.order_line:
                product_uuid: Optional[uuid.UUID] = None
                if line.product_id:
                    r = await db.execute(select(Product.id).where(Product.odoo_id == line.product_id))
                    product_uuid = r.scalar_one_or_none()

                line_fields = dict(
                    order_id=order.id,
                    product_id=product_uuid,
                    name=line.name, sequence=line.sequence,
                    product_uom_qty=line.product_uom_qty,
                    qty_delivered=line.qty_delivered,
                    qty_invoiced=line.qty_invoiced,
                    price_unit=line.price_unit, discount=line.discount,
                    price_subtotal=line.price_subtotal,
                    price_tax=line.price_tax, price_total=line.price_total,
                    is_downpayment=line.is_downpayment, state=line.state,
                )
                await upsert_by_odoo_id(db, SaleOrderLine, line.id, line_fields)

            created += was_created
            updated += not was_created
        except Exception as exc:
            errors.append(f"sale_order odoo_id={rec.id}: {exc}")

    await db.flush()
    return BulkImportResponse(created=created, updated=updated, errors=errors)
