from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.partner import Partner, PartnerTag
from app.schemas.partner import (
    BulkImportResponse, BulkPartnerImport,
    PartnerCreate, PartnerListResponse, PartnerUpdate,
)
from app.services.base import upsert_by_odoo_id


def _q():
    return select(Partner).options(
        selectinload(Partner.tags),
        selectinload(Partner.state),
        selectinload(Partner.country),
    )


async def _load_tags(db: AsyncSession, ids: list[int]) -> list[PartnerTag]:
    if not ids:
        return []
    r = await db.execute(select(PartnerTag).where(PartnerTag.id.in_(ids)))
    return list(r.scalars())


async def create_partner(db: AsyncSession, payload: PartnerCreate) -> Partner:
    data = payload.model_dump(exclude={"tag_ids"})
    tags = await _load_tags(db, payload.tag_ids)
    obj = Partner(**data, tags=tags)
    db.add(obj)
    await db.flush()
    await db.refresh(obj, ["tags", "state", "country"])
    return obj


async def get_partner(db: AsyncSession, pid: uuid.UUID) -> Optional[Partner]:
    r = await db.execute(_q().where(Partner.id == pid))
    return r.scalar_one_or_none()


async def list_partners(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    is_company: Optional[bool] = None,
    active: Optional[bool] = True,
    country_id: Optional[int] = None,
    tag_id: Optional[int] = None,
) -> PartnerListResponse:
    q = _q()
    if search:
        p = f"%{search}%"
        q = q.where(Partner.name.ilike(p) | Partner.email.ilike(p) | Partner.city.ilike(p))
    if is_company is not None:
        q = q.where(Partner.is_company == is_company)
    if active is not None:
        q = q.where(Partner.active == active)
    if country_id:
        q = q.where(Partner.country_id == country_id)
    if tag_id:
        q = q.where(Partner.tags.any(PartnerTag.id == tag_id))

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.order_by(Partner.name).offset((page - 1) * page_size).limit(page_size)
    items = list((await db.execute(q)).scalars())
    return PartnerListResponse(total=total, page=page, page_size=page_size, items=items)


async def update_partner(db: AsyncSession, pid: uuid.UUID, payload: PartnerUpdate) -> Optional[Partner]:
    obj = await get_partner(db, pid)
    if not obj:
        return None
    for k, v in payload.model_dump(exclude_none=True, exclude={"tag_ids"}).items():
        setattr(obj, k, v)
    if payload.tag_ids is not None:
        obj.tags = await _load_tags(db, payload.tag_ids)
    await db.flush()
    await db.refresh(obj, ["tags", "state", "country"])
    return obj


async def delete_partner(db: AsyncSession, pid: uuid.UUID, hard: bool = False) -> bool:
    obj = await get_partner(db, pid)
    if not obj:
        return False
    if hard:
        await db.delete(obj)
    else:
        obj.active = False
    return True


async def bulk_upsert_partners(db: AsyncSession, payload: BulkPartnerImport) -> BulkImportResponse:
    created = updated = 0
    errors: list[str] = []
    for rec in payload.records:
        try:
            # Resolve parent UUID from odoo_id
            parent_uuid: Optional[uuid.UUID] = None
            if rec.parent_id:
                r = await db.execute(select(Partner.id).where(Partner.odoo_id == rec.parent_id))
                parent_uuid = r.scalar_one_or_none()

            # Resolve tags
            tags = []
            for tid in rec.category_id:
                tr = await db.execute(select(PartnerTag).where(PartnerTag.odoo_id == tid))
                t = tr.scalar_one_or_none()
                if t:
                    tags.append(t)

            fields = dict(
                name=rec.name, is_company=rec.is_company,
                parent_id=parent_uuid, company_name=rec.company_name,
                company_type=rec.company_type,
                email=rec.email, phone=rec.phone, mobile=rec.mobile,
                website=rec.website, vat=rec.vat, ref=rec.ref,
                street=rec.street, street2=rec.street2, city=rec.city,
                zip_code=rec.zip, state_id=rec.state_id, country_id=rec.country_id,
                customer_rank=rec.customer_rank, supplier_rank=rec.supplier_rank,
                partner_type=rec.partner_type, lang=rec.lang, tz=rec.tz,
                payment_term_id=rec.property_payment_term_id,
                notes=rec.comment, active=rec.active,
                odoo_created_at=rec.create_date, odoo_updated_at=rec.write_date,
            )
            obj, was_created = await upsert_by_odoo_id(db, Partner, rec.id, fields)
            obj.tags = tags
            if was_created:
                created += 1
            else:
                updated += 1
        except Exception as exc:
            errors.append(f"partner odoo_id={rec.id}: {exc}")
    await db.flush()
    return BulkImportResponse(created=created, updated=updated, errors=errors)
