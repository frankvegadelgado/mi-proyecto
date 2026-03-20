"""
CRM Pipeline
  crm_stages    ← crm.stage
  crm_tags      ← crm.tag
  crm_leads     ← crm.lead  (type = lead | opportunity)
  crm_lead_tags ← many-to-many
"""
from __future__ import annotations
import uuid
from datetime import date, datetime
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey,
    Integer, Numeric, String, Table, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


crm_lead_tags = Table(
    "crm_lead_tags",
    Base.metadata,
    Column("lead_id", UUID(as_uuid=True), ForeignKey("crm_leads.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("crm_tags.id", ondelete="CASCADE"), primary_key=True),
)


class CrmStage(Base):
    __tablename__ = "crm_stages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=1)
    is_won: Mapped[bool] = mapped_column(Boolean, default=False)
    requirements: Mapped[str | None] = mapped_column(Text)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("sales_teams.id"))

    leads: Mapped[list["CrmLead"]] = relationship(back_populates="stage")


class CrmTag(Base):
    __tablename__ = "crm_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    color: Mapped[str | None] = mapped_column(String(7))

    leads: Mapped[list["CrmLead"]] = relationship(secondary="crm_lead_tags", back_populates="tags")


class CrmLead(Base):
    __tablename__ = "crm_leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    odoo_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    odoo_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(16), default="lead")  # lead | opportunity
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Pipeline
    stage_id: Mapped[int | None] = mapped_column(ForeignKey("crm_stages.id"), index=True)
    priority: Mapped[str] = mapped_column(String(1), default="0")  # 0-3
    kanban_state: Mapped[str | None] = mapped_column(String(32))   # normal, done, blocked
    probability: Mapped[float | None] = mapped_column(Float)
    automated_probability: Mapped[float | None] = mapped_column(Float)

    # Commercial
    expected_revenue: Mapped[float | None] = mapped_column(Numeric(16, 4))
    prorated_revenue: Mapped[float | None] = mapped_column(Numeric(16, 4))
    recurring_revenue: Mapped[float | None] = mapped_column(Numeric(16, 4))
    recurring_plan: Mapped[str | None] = mapped_column(String(64))

    # Contact
    partner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"), index=True)
    partner_name: Mapped[str | None] = mapped_column(String(256))  # lead contact name if no partner
    contact_name: Mapped[str | None] = mapped_column(String(256))
    email_from: Mapped[str | None] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(64))
    mobile: Mapped[str | None] = mapped_column(String(64))
    website: Mapped[str | None] = mapped_column(String(512))

    # Address (when no partner)
    street: Mapped[str | None] = mapped_column(String(256))
    city: Mapped[str | None] = mapped_column(String(128))
    country_id: Mapped[int | None] = mapped_column(ForeignKey("countries.id"))
    state_id: Mapped[int | None] = mapped_column(ForeignKey("states.id"))

    # Assignment
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("sales_teams.id"), index=True)

    # Dates
    date_open: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_closed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_deadline: Mapped[date | None] = mapped_column(Date)
    date_last_stage_update: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_conversion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Source / Campaign
    source_name: Mapped[str | None] = mapped_column(String(256))
    medium_name: Mapped[str | None] = mapped_column(String(256))
    campaign_name: Mapped[str | None] = mapped_column(String(256))
    referred: Mapped[str | None] = mapped_column(String(256))

    # Won/Lost
    lost_reason_name: Mapped[str | None] = mapped_column(String(256))

    # Description
    description: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    stage: Mapped[CrmStage | None] = relationship(back_populates="leads")
    partner: Mapped["Partner | None"] = relationship(back_populates="crm_leads")       # noqa: F821
    user: Mapped["User | None"] = relationship(back_populates="crm_leads")             # noqa: F821
    team: Mapped["SalesTeam | None"] = relationship(back_populates="crm_leads")        # noqa: F821
    tags: Mapped[list[CrmTag]] = relationship(secondary="crm_lead_tags", back_populates="leads")
