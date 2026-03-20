"""
Sales
  sale_orders      ← sale.order
  sale_order_lines ← sale.order.line
"""
from __future__ import annotations
import uuid
from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SaleOrder(Base):
    __tablename__ = "sale_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    odoo_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    odoo_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SO0001
    state: Mapped[str] = mapped_column(String(32), default="draft")  # draft, sent, sale, done, cancel
    client_order_ref: Mapped[str | None] = mapped_column(String(256))

    # Partners
    partner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"), index=True)
    partner_invoice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"))
    partner_shipping_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"))

    # Assignment
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("sales_teams.id"), index=True)

    # Dates
    date_order: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    validity_date: Mapped[date | None] = mapped_column(Date)
    commitment_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expected_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Finance
    pricelist_id: Mapped[int | None] = mapped_column(ForeignKey("pricelists.id"))
    payment_term_id: Mapped[int | None] = mapped_column(ForeignKey("payment_terms.id"))
    currency_name: Mapped[str | None] = mapped_column(String(16))  # denorm
    amount_untaxed: Mapped[float | None] = mapped_column(Numeric(16, 4))
    amount_tax: Mapped[float | None] = mapped_column(Numeric(16, 4))
    amount_total: Mapped[float | None] = mapped_column(Numeric(16, 4))
    amount_to_invoice: Mapped[float | None] = mapped_column(Numeric(16, 4))
    invoice_status: Mapped[str | None] = mapped_column(String(32))  # upselling, invoiced, to invoice, nothing

    # Notes
    note: Mapped[str | None] = mapped_column(Text)
    internal_note: Mapped[str | None] = mapped_column(Text)

    # CRM link
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crm_leads.id"))

    # Source
    source_name: Mapped[str | None] = mapped_column(String(256))
    medium_name: Mapped[str | None] = mapped_column(String(256))
    campaign_name: Mapped[str | None] = mapped_column(String(256))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    partner: Mapped["Partner | None"] = relationship(back_populates="sale_orders", foreign_keys=[partner_id])  # noqa: F821
    user: Mapped["User | None"] = relationship(back_populates="sale_orders")            # noqa: F821
    team: Mapped["SalesTeam | None"] = relationship(back_populates="sale_orders")       # noqa: F821
    pricelist: Mapped["Pricelist | None"] = relationship(back_populates="sale_orders")  # noqa: F821
    payment_term: Mapped["PaymentTerm | None"] = relationship(back_populates="sale_orders")  # noqa: F821
    order_lines: Mapped[list["SaleOrderLine"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    opportunity: Mapped["CrmLead | None"] = relationship()                              # noqa: F821


class SaleOrderLine(Base):
    __tablename__ = "sale_order_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sale_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), index=True)
    product_variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("product_variants.id"))
    name: Mapped[str | None] = mapped_column(Text)            # description shown on line
    sequence: Mapped[int] = mapped_column(Integer, default=10)
    product_uom_qty: Mapped[float] = mapped_column(Numeric(16, 4), default=1)
    qty_delivered: Mapped[float | None] = mapped_column(Numeric(16, 4))
    qty_invoiced: Mapped[float | None] = mapped_column(Numeric(16, 4))
    qty_to_invoice: Mapped[float | None] = mapped_column(Numeric(16, 4))
    price_unit: Mapped[float | None] = mapped_column(Numeric(16, 4))
    discount: Mapped[float | None] = mapped_column(Numeric(8, 4))
    price_subtotal: Mapped[float | None] = mapped_column(Numeric(16, 4))
    price_tax: Mapped[float | None] = mapped_column(Numeric(16, 4))
    price_total: Mapped[float | None] = mapped_column(Numeric(16, 4))
    tax_names: Mapped[str | None] = mapped_column(String(256))  # denorm
    is_downpayment: Mapped[bool] = mapped_column(Boolean, default=False)
    state: Mapped[str | None] = mapped_column(String(32))

    order: Mapped[SaleOrder] = relationship(back_populates="order_lines")
    product: Mapped["Product | None"] = relationship(back_populates="sale_order_lines")  # noqa: F821
    product_variant: Mapped["ProductVariant | None"] = relationship()                    # noqa: F821
