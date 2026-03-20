"""
Odoo → AWS Aurora CRM API
All 23 Odoo models, full CRUD + orchestrated sync.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    accounting, communication, crm, lookup,
    odoo_sync, partners, products, sales, users,
)

settings = get_settings()

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)

app = FastAPI(
    title="Odoo CRM → Aurora API",
    description=(
        "Full-fidelity mirror of Odoo CRM in AWS Aurora PostgreSQL.\n\n"
        "**23 Odoo models** imported across 8 domains:\n"
        "- **Lookup**: currencies, countries, states, payment terms, pricelists\n"
        "- **Users**: res.users, crm.team\n"
        "- **Partners**: res.partner, res.partner.category\n"
        "- **Products**: product.category, product.template, product.product, pricelist items\n"
        "- **CRM**: crm.stage, crm.tag, crm.lead\n"
        "- **Sales**: sale.order, sale.order.line\n"
        "- **Accounting**: account.move (invoices/bills), account.move.line, account.payment\n"
        "- **Communication**: mail.activity.type, mail.activity, mail.message, calendar.event\n\n"
        "Trigger a full or incremental sync via `POST /api/v1/sync/odoo`."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
V1 = "/api/v1"
app.include_router(lookup.router,        prefix=V1)
app.include_router(users.router,         prefix=V1)
app.include_router(partners.router,      prefix=V1)
app.include_router(products.router,      prefix=V1)
app.include_router(crm.router,           prefix=V1)
app.include_router(sales.router,         prefix=V1)
app.include_router(accounting.router,    prefix=V1)
app.include_router(communication.router, prefix=V1)
app.include_router(odoo_sync.router,     prefix=V1)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok", "env": settings.app_env, "version": "2.0.0"}


# ── Dev token (disabled in production) ───────────────────────────────────────
if settings.app_env == "development":
    from app.middleware.auth import create_access_token

    @app.post("/dev/token", tags=["ops"])
    async def dev_token(subject: str = "dev-user"):
        """Returns a JWT for local testing. Disabled in production."""
        return {"access_token": create_access_token(subject), "token_type": "bearer"}
