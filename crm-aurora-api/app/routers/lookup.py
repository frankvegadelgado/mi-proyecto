from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.lookup import Country, Currency, PaymentTerm, Pricelist, State
from app.schemas.lookup import (
    CountryCreate, CountryRead, CurrencyCreate, CurrencyRead,
    PaymentTermCreate, PaymentTermRead, PricelistCreate, PricelistRead,
    StateCreate, StateRead,
)

router = APIRouter(prefix="/lookup", tags=["lookup"])

# Currencies
@router.post("/currencies", response_model=CurrencyRead, status_code=201)
async def create_currency(p: CurrencyCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = Currency(**p.model_dump()); db.add(obj); await db.flush(); return obj

@router.get("/currencies", response_model=list[CurrencyRead])
async def list_currencies(db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return (await db.execute(select(Currency).order_by(Currency.name))).scalars().all()

# Countries
@router.post("/countries", response_model=CountryRead, status_code=201)
async def create_country(p: CountryCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = Country(**p.model_dump()); db.add(obj); await db.flush(); return obj

@router.get("/countries", response_model=list[CountryRead])
async def list_countries(db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return (await db.execute(select(Country).order_by(Country.name))).scalars().all()

@router.get("/countries/{cid}/states", response_model=list[StateRead])
async def list_states(cid: int, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return (await db.execute(select(State).where(State.country_id == cid).order_by(State.name))).scalars().all()

@router.post("/states", response_model=StateRead, status_code=201)
async def create_state(p: StateCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = State(**p.model_dump()); db.add(obj); await db.flush(); return obj

# Payment Terms
@router.post("/payment-terms", response_model=PaymentTermRead, status_code=201)
async def create_term(p: PaymentTermCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = PaymentTerm(**p.model_dump()); db.add(obj); await db.flush(); return obj

@router.get("/payment-terms", response_model=list[PaymentTermRead])
async def list_terms(db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return (await db.execute(select(PaymentTerm).order_by(PaymentTerm.name))).scalars().all()

# Pricelists
@router.post("/pricelists", response_model=PricelistRead, status_code=201)
async def create_pricelist(p: PricelistCreate, db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    obj = Pricelist(**p.model_dump()); db.add(obj); await db.flush(); return obj

@router.get("/pricelists", response_model=list[PricelistRead])
async def list_pricelists(db: AsyncSession = Depends(get_db), _u=Depends(get_current_user)):
    return (await db.execute(select(Pricelist).order_by(Pricelist.name))).scalars().all()
