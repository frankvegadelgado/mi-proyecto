"""
Accounting
  invoices      ← account.move  (customer_invoice, vendor_bill, credit_note …)
  invoice_lines ← account.move.line
  payments      ← account.payment
"""
from __future__ import annotations
import uuid
from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    odoo_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    odoo_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    name: Mapped[str | None] = mapped_column(String(64), index=True)   # INV/2024/0001
    ref: Mapped[str | None] = mapped_column(String(256))                # customer reference
    move_type: Mapped[str] = mapped_column(String(32), nullable=False)  # out_invoice, in_invoice, out_refund, in_refund, entry
    state: Mapped[str] = mapped_column(String(32), default="draft")     # draft, posted, cancel
    payment_state: Mapped[str | None] = mapped_column(String(32))       # not_paid, in_payment, paid, partial, reversed, invoicing_legacy

    # Partners
    partner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"), index=True)
    partner_shipping_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"))

    # Dates
    invoice_date: Mapped[date | None] = mapped_column(Date, index=True)
    invoice_date_due: Mapped[date | None] = mapped_column(Date)
    delivery_date: Mapped[date | None] = mapped_column(Date)

    # Finance
    currency_id: Mapped[int | None] = mapped_column(ForeignKey("currencies.id"))
    payment_term_id: Mapped[int | None] = mapped_column(ForeignKey("payment_terms.id"))
    amount_untaxed: Mapped[float | None] = mapped_column(Numeric(16, 4))
    amount_tax: Mapped[float | None] = mapped_column(Numeric(16, 4))
    amount_total: Mapped[float | None] = mapped_column(Numeric(16, 4))
    amount_residual: Mapped[float | None] = mapped_column(Numeric(16, 4))  # remaining to pay
    amount_total_signed: Mapped[float | None] = mapped_column(Numeric(16, 4))

    # Linked sale order (denorm reference list)
    sale_order_ids: Mapped[str | None] = mapped_column(Text)  # JSON list of sale_order odoo_ids

    # Notes
    narration: Mapped[str | None] = mapped_column(Text)   # terms and conditions / footer
    invoice_origin: Mapped[str | None] = mapped_column(String(256))  # source doc ref

    # Misc
    fiscal_position_name: Mapped[str | None] = mapped_column(String(256))
    auto_post: Mapped[str | None] = mapped_column(String(32))   # no, monthly, quarterly, yearly
    reversed_entry_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"))
    sequence_number: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    partner: Mapped["Partner | None"] = relationship(back_populates="invoices", foreign_keys=[partner_id])  # noqa: F821
    currency: Mapped["Currency | None"] = relationship(back_populates="invoices")       # noqa: F821
    lines: Mapped[list["InvoiceLine"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")
    reversed_entry: Mapped["Invoice | None"] = relationship("Invoice", remote_side="Invoice.id")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    move_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), index=True)
    name: Mapped[str | None] = mapped_column(Text)
    sequence: Mapped[int] = mapped_column(Integer, default=10)
    account_name: Mapped[str | None] = mapped_column(String(256))   # denorm account name
    quantity: Mapped[float | None] = mapped_column(Numeric(16, 4))
    price_unit: Mapped[float | None] = mapped_column(Numeric(16, 4))
    discount: Mapped[float | None] = mapped_column(Numeric(8, 4))
    price_subtotal: Mapped[float | None] = mapped_column(Numeric(16, 4))
    price_total: Mapped[float | None] = mapped_column(Numeric(16, 4))
    tax_names: Mapped[str | None] = mapped_column(String(256))
    display_type: Mapped[str | None] = mapped_column(String(32))  # line_section, line_note

    invoice: Mapped[Invoice] = relationship(back_populates="lines")
    product: Mapped["Product | None"] = relationship(back_populates="invoice_lines")  # noqa: F821


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    odoo_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    name: Mapped[str | None] = mapped_column(String(64), index=True)   # BNK1/2024/0001
    payment_type: Mapped[str] = mapped_column(String(32), nullable=False)  # inbound, outbound, transfer
    partner_type: Mapped[str | None] = mapped_column(String(32))   # customer, supplier
    state: Mapped[str] = mapped_column(String(32), default="draft")  # draft, posted, sent, reconciled, cancelled

    partner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"), index=True)
    currency_id: Mapped[int | None] = mapped_column(ForeignKey("currencies.id"))
    payment_method_name: Mapped[str | None] = mapped_column(String(128))  # denorm
    journal_name: Mapped[str | None] = mapped_column(String(128))         # denorm

    amount: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    payment_date: Mapped[date | None] = mapped_column(Date, index=True)
    memo: Mapped[str | None] = mapped_column(String(256))
    destination_account_name: Mapped[str | None] = mapped_column(String(256))

    # Linked invoices (denorm reference list)
    reconciled_invoice_ids: Mapped[str | None] = mapped_column(Text)  # JSON list of invoice odoo_ids

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    partner: Mapped["Partner | None"] = relationship(back_populates="payments")     # noqa: F821
    currency: Mapped["Currency | None"] = relationship(back_populates="payments")  # noqa: F821
