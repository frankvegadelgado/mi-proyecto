"""
Partners (contacts / companies)
  partner_tags         ← res.partner.category
  partners             ← res.partner
  partner_partner_tags ← many-to-many join
"""
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


partner_partner_tags = Table(
    "partner_partner_tags",
    Base.metadata,
    Column("partner_id", UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("partner_tags.id", ondelete="CASCADE"), primary_key=True),
)


class PartnerTag(Base):
    __tablename__ = "partner_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    color: Mapped[str | None] = mapped_column(String(7))

    partners: Mapped[list["Partner"]] = relationship(secondary="partner_partner_tags", back_populates="tags")


class Partner(Base):
    __tablename__ = "partners"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    odoo_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    odoo_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Identity
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    is_company: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id", ondelete="SET NULL"), index=True)
    company_name: Mapped[str | None] = mapped_column(String(256))
    company_type: Mapped[str | None] = mapped_column(String(32))   # person / company

    # Contact
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(64))
    mobile: Mapped[str | None] = mapped_column(String(64))
    website: Mapped[str | None] = mapped_column(String(512))
    vat: Mapped[str | None] = mapped_column(String(64))            # Tax ID / VAT number
    ref: Mapped[str | None] = mapped_column(String(64))            # Internal reference

    # Address
    street: Mapped[str | None] = mapped_column(String(256))
    street2: Mapped[str | None] = mapped_column(String(256))
    city: Mapped[str | None] = mapped_column(String(128))
    zip_code: Mapped[str | None] = mapped_column(String(20))
    state_id: Mapped[int | None] = mapped_column(ForeignKey("states.id"), index=True)
    country_id: Mapped[int | None] = mapped_column(ForeignKey("countries.id"), index=True)

    # CRM classification
    customer_rank: Mapped[int] = mapped_column(Integer, default=0)
    supplier_rank: Mapped[int] = mapped_column(Integer, default=0)
    partner_type: Mapped[str | None] = mapped_column(String(32))   # contact, invoice, delivery, other

    # Locale
    lang: Mapped[str | None] = mapped_column(String(16))
    tz: Mapped[str | None] = mapped_column(String(64))

    # Finance
    payment_term_id: Mapped[int | None] = mapped_column(ForeignKey("payment_terms.id"))
    property_account_receivable_id: Mapped[int | None] = mapped_column(Integer)  # odoo account id (reference only)
    property_account_payable_id: Mapped[int | None] = mapped_column(Integer)

    # Notes & status
    notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    parent: Mapped["Partner | None"] = relationship("Partner", remote_side="Partner.id", back_populates="contacts")
    contacts: Mapped[list["Partner"]] = relationship("Partner", back_populates="parent", cascade="all, delete-orphan")
    state: Mapped["State | None"] = relationship(back_populates="partners")              # noqa: F821
    country: Mapped["Country | None"] = relationship(back_populates="partners")          # noqa: F821
    payment_term: Mapped["PaymentTerm | None"] = relationship()                          # noqa: F821
    tags: Mapped[list[PartnerTag]] = relationship(secondary="partner_partner_tags", back_populates="partners")
    crm_leads: Mapped[list["CrmLead"]] = relationship(back_populates="partner")          # noqa: F821
    sale_orders: Mapped[list["SaleOrder"]] = relationship(back_populates="partner")      # noqa: F821
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="partner")           # noqa: F821
    payments: Mapped[list["Payment"]] = relationship(back_populates="partner")           # noqa: F821
    meeting_attendances: Mapped[list["MeetingAttendee"]] = relationship(back_populates="partner")  # noqa: F821
