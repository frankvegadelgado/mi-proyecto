"""
Lookup / configuration tables
  currencies       ← res.currency
  countries        ← res.country
  states           ← res.country.state
  payment_terms    ← account.payment.term
  pricelists       ← product.pricelist
  pricelist_items  ← product.pricelist.item
"""
from __future__ import annotations
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Currency(Base):
    __tablename__ = "currencies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    odoo_id: Mapped[int | None] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(8))
    code: Mapped[str | None] = mapped_column(String(3), unique=True)   # ISO 4217
    rounding: Mapped[float | None]
    active: Mapped[bool] = mapped_column(default=True)

    countries: Mapped[list["Country"]] = relationship(back_populates="currency")
    pricelists: Mapped[list["Pricelist"]] = relationship(back_populates="currency")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="currency")       # noqa: F821
    payments: Mapped[list["Payment"]] = relationship(back_populates="currency")       # noqa: F821


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    odoo_id: Mapped[int | None] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    code: Mapped[str | None] = mapped_column(String(3), unique=True)
    phone_code: Mapped[str | None] = mapped_column(String(10))
    currency_id: Mapped[int | None] = mapped_column(ForeignKey("currencies.id"))

    currency: Mapped[Currency | None] = relationship(back_populates="countries")
    states: Mapped[list["State"]] = relationship(back_populates="country")
    partners: Mapped[list["Partner"]] = relationship(back_populates="country")        # noqa: F821


class State(Base):
    __tablename__ = "states"
    __table_args__ = (UniqueConstraint("country_id", "code"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    odoo_id: Mapped[int | None] = mapped_column(unique=True, index=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str | None] = mapped_column(String(10))

    country: Mapped[Country] = relationship(back_populates="states")
    partners: Mapped[list["Partner"]] = relationship(back_populates="state")          # noqa: F821


class PaymentTerm(Base):
    __tablename__ = "payment_terms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    odoo_id: Mapped[int | None] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(default=True)

    sale_orders: Mapped[list["SaleOrder"]] = relationship(back_populates="payment_term")  # noqa: F821


class Pricelist(Base):
    __tablename__ = "pricelists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    odoo_id: Mapped[int | None] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    currency_id: Mapped[int | None] = mapped_column(ForeignKey("currencies.id"))
    active: Mapped[bool] = mapped_column(default=True)

    currency: Mapped[Currency | None] = relationship(back_populates="pricelists")
    items: Mapped[list["PricelistItem"]] = relationship(back_populates="pricelist", cascade="all, delete-orphan")
    sale_orders: Mapped[list["SaleOrder"]] = relationship(back_populates="pricelist")  # noqa: F821


class PricelistItem(Base):
    __tablename__ = "pricelist_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    odoo_id: Mapped[int | None] = mapped_column(unique=True, index=True)
    pricelist_id: Mapped[int] = mapped_column(ForeignKey("pricelists.id"), nullable=False)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"))         # noqa: F821
    compute_price: Mapped[str | None] = mapped_column(String(32))  # fixed, percentage, formula
    fixed_price: Mapped[float | None] = mapped_column(Numeric(16, 4))
    percent_price: Mapped[float | None] = mapped_column(Numeric(8, 4))
    price_discount: Mapped[float | None] = mapped_column(Numeric(8, 4))
    min_quantity: Mapped[float | None] = mapped_column(Numeric(16, 4))
    date_start: Mapped[str | None] = mapped_column(String(32))
    date_end: Mapped[str | None] = mapped_column(String(32))

    pricelist: Mapped[Pricelist] = relationship(back_populates="items")
    product: Mapped["Product | None"] = relationship(back_populates="pricelist_items")  # noqa: F821
