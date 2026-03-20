"""
Product catalogue
  product_categories ← product.category
  products           ← product.template
  product_variants   ← product.product
"""
from __future__ import annotations
import uuid
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("product_categories.id"))
    complete_name: Mapped[str | None] = mapped_column(String(512))  # e.g. "All / Saleable / Software"

    parent: Mapped["ProductCategory | None"] = relationship("ProductCategory", remote_side="ProductCategory.id", back_populates="children")
    children: Mapped[list["ProductCategory"]] = relationship("ProductCategory", back_populates="parent")
    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    description_sale: Mapped[str | None] = mapped_column(Text)
    description_purchase: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str | None] = mapped_column(String(32))        # consu, service, product
    categ_id: Mapped[int | None] = mapped_column(ForeignKey("product_categories.id"), index=True)
    uom_name: Mapped[str | None] = mapped_column(String(64))    # unit of measure name (denorm)
    uom_po_name: Mapped[str | None] = mapped_column(String(64))
    list_price: Mapped[float | None] = mapped_column(Numeric(16, 4))
    standard_price: Mapped[float | None] = mapped_column(Numeric(16, 4))  # cost
    taxes_name: Mapped[str | None] = mapped_column(String(256))  # denorm JSON list of tax names
    default_code: Mapped[str | None] = mapped_column(String(64), index=True)  # internal ref
    barcode: Mapped[str | None] = mapped_column(String(128), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    sale_ok: Mapped[bool] = mapped_column(Boolean, default=True)
    purchase_ok: Mapped[bool] = mapped_column(Boolean, default=True)
    can_be_expensed: Mapped[bool] = mapped_column(Boolean, default=False)
    invoice_policy: Mapped[str | None] = mapped_column(String(32))  # order, delivery
    weight: Mapped[float | None] = mapped_column(Numeric(16, 4))
    volume: Mapped[float | None] = mapped_column(Numeric(16, 4))

    category: Mapped[ProductCategory | None] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    pricelist_items: Mapped[list["PricelistItem"]] = relationship(back_populates="product")  # noqa: F821
    sale_order_lines: Mapped[list["SaleOrderLine"]] = relationship(back_populates="product")  # noqa: F821
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(back_populates="product")       # noqa: F821


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(512))         # variant attribute combination
    default_code: Mapped[str | None] = mapped_column(String(64), index=True)
    barcode: Mapped[str | None] = mapped_column(String(128), index=True)
    price_extra: Mapped[float | None] = mapped_column(Numeric(16, 4))  # added to template list_price
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    combination_indices: Mapped[str | None] = mapped_column(String(255))

    product: Mapped[Product] = relationship(back_populates="variants")
