from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.crm import CrmLead, CrmTag, CrmStage
from app.models.user import User, SalesTeam
from app.schemas.crm import (
    BulkCrmLeadImport, CrmLeadCreate, CrmLeadListResponse, CrmLeadUpdate,
)
from app.schemas.partner import BulkImportResponse
from app.services.base import upsert_by_odoo_id


def _q():
    return select(CrmLead).options(selectinload(CrmLead.tags), selectinload(CrmLead.stage))


async def _tags(db: AsyncSession, odoo_ids: list[int]) -> list[CrmTag]:
    if not odoo_ids:
        return []
    r = await db.execute(select(CrmTag).where(CrmTag.odoo_id.in_(odoo_ids)))
    return list(r.scalars())


async def _tags_by_id(db: AsyncSession, ids: list[int]) -> list[CrmTag]:
    if not ids:
        return []
    r = await db.execute(select(CrmTag).where(CrmTag.id.in_(ids)))
    return list(r.scalars())


async def create_lead(db: AsyncSession, payload: CrmLeadCreate) -> CrmLead:
    data = payload.model_dump(exclude={"tag_ids"})
    tags = await _tags_by_id(db, payload.tag_ids)
    obj = CrmLead(**data, tags=tags)
    db.add(obj)
    await db.flush()
    return obj


async def get_lead(db: AsyncSession, lid: uuid.UUID) -> Optional[CrmLead]:
    r = await db.execute(_q().where(CrmLead.id == lid))
    return r.scalar_one_or_none()


async def list_leads(
    db: AsyncSession,
    page: int = 1, page_size: int = 20,
    search: Optional[str] = None,
    lead_type: Optional[str] = None,
    stage_id: Optional[int] = None,
    user_id: Optional[uuid.UUID] = None,
    team_id: Optional[int] = None,
    active: Optional[bool] = True,
) -> CrmLeadListResponse:
    q = _q()
    if search:
        p = f"%{search}%"
        q = q.where(CrmLead.name.ilike(p) | CrmLead.email_from.ilike(p) | CrmLead.partner_name.ilike(p))
    if lead_type:
        q = q.where(CrmLead.type == lead_type)
    if stage_id:
        q = q.where(CrmLead.stage_id == stage_id)
    if user_id:
        q = q.where(CrmLead.user_id == user_id)
    if team_id:
        q = q.where(CrmLead.team_id == team_id)
    if active is not None:
        q = q.where(CrmLead.active == active)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.order_by(CrmLead.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list((await db.execute(q)).scalars())
    return CrmLeadListResponse(total=total, page=page, page_size=page_size, items=items)


async def update_lead(db: AsyncSession, lid: uuid.UUID, payload: CrmLeadUpdate) -> Optional[CrmLead]:
    obj = await get_lead(db, lid)
    if not obj:
        return None
    for k, v in payload.model_dump(exclude_none=True, exclude={"tag_ids"}).items():
        setattr(obj, k, v)
    if payload.tag_ids is not None:
        obj.tags = await _tags_by_id(db, payload.tag_ids)
    await db.flush()
    return obj


async def delete_lead(db: AsyncSession, lid: uuid.UUID, hard: bool = False) -> bool:
    obj = await get_lead(db, lid)
    if not obj:
        return False
    if hard:
        await db.delete(obj)
    else:
        obj.active = False
    return True


async def bulk_upsert_leads(db: AsyncSession, payload: BulkCrmLeadImport) -> BulkImportResponse:
    from app.models.partner import Partner
    created = updated = 0
    errors: list[str] = []
    for rec in payload.records:
        try:
            partner_uuid: Optional[uuid.UUID] = None
            if rec.partner_id:
                r = await db.execute(select(Partner.id).where(Partner.odoo_id == rec.partner_id))
                partner_uuid = r.scalar_one_or_none()

            user_uuid: Optional[uuid.UUID] = None
            if rec.user_id:
                r = await db.execute(select(User.id).where(User.odoo_id == rec.user_id))
                user_uuid = r.scalar_one_or_none()

            team_id: Optional[int] = None
            if rec.team_id:
                r = await db.execute(select(SalesTeam.id).where(SalesTeam.odoo_id == rec.team_id))
                team_id = r.scalar_one_or_none()

            stage_id: Optional[int] = None
            if rec.stage_id:
                r = await db.execute(select(CrmStage.id).where(CrmStage.odoo_id == rec.stage_id))
                stage_id = r.scalar_one_or_none()

            tags = await _tags(db, rec.tag_ids)

            fields = dict(
                name=rec.name, type=rec.type, active=rec.active,
                stage_id=stage_id, priority=rec.priority,
                kanban_state=rec.kanban_state, probability=rec.probability,
                expected_revenue=rec.expected_revenue,
                prorated_revenue=rec.prorated_revenue,
                partner_id=partner_uuid, partner_name=rec.partner_name,
                contact_name=rec.contact_name, email_from=rec.email_from,
                phone=rec.phone, mobile=rec.mobile,
                street=rec.street, city=rec.city,
                country_id=rec.country_id, state_id=rec.state_id,
                user_id=user_uuid, team_id=team_id,
                date_open=rec.date_open, date_closed=rec.date_closed,
                date_deadline=rec.date_deadline,
                description=rec.description,
                odoo_created_at=rec.create_date, odoo_updated_at=rec.write_date,
            )
            obj, was_created = await upsert_by_odoo_id(db, CrmLead, rec.id, fields)
            obj.tags = tags
            created += was_created
            updated += not was_created
        except Exception as exc:
            errors.append(f"lead odoo_id={rec.id}: {exc}")
    await db.flush()
    return BulkImportResponse(created=created, updated=updated, errors=errors)
