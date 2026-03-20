"""Product router."""
from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.product import Product, ProductCategory, ProductVariant
from app.schemas.product import ProductCategoryCreate, ProductCategoryRead, ProductCreate, ProductRead, ProductUpdate, ProductVariantRead

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/categories", response_model=ProductCategoryRead, status_code=201)
async def create_category(payload: ProductCategoryCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = ProductCategory(**payload.model_dump())
    db.add(obj)
    await db.flush()
    return obj

@router.get("/categories", response_model=list[ProductCategoryRead])
async def list_categories(db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    r = await db.execute(select(ProductCategory).order_by(ProductCategory.name))
    return r.scalars().all()

@router.post("/", response_model=ProductRead, status_code=201)
async def create(payload: ProductCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = Product(**payload.model_dump())
    db.add(obj)
    await db.flush()
    return obj

@router.get("/", response_model=list[ProductRead])
async def list_products(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200),
    search: Optional[str] = None, active: Optional[bool] = True,
    categ_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db), _u=Depends(get_current_user),
):
    q = select(Product)
    if search:
        q = q.where(Product.name.ilike(f"%{search}%") | Product.default_code.ilike(f"%{search}%"))
    if active is not None:
        q = q.where(Product.active == active)
    if categ_id:
        q = q.where(Product.categ_id == categ_id)
    q = q.order_by(Product.name).offset((page - 1) * page_size).limit(page_size)
    r = await db.execute(q)
    return r.scalars().all()

@router.get("/{pid}", response_model=ProductRead)
async def get(pid: uuid.UUID, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await db.get(Product, pid)
    if not obj:
        raise HTTPException(404, "Product not found")
    return obj

@router.patch("/{pid}", response_model=ProductRead)
async def update(pid: uuid.UUID, payload: ProductUpdate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = await db.get(Product, pid)
    if not obj:
        raise HTTPException(404, "Product not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    await db.flush()
    return obj

@router.get("/{pid}/variants", response_model=list[ProductVariantRead])
async def list_variants(pid: uuid.UUID, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    r = await db.execute(select(ProductVariant).where(ProductVariant.product_id == pid))
    return r.scalars().all()
