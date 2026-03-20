"""
OdooImportService
-----------------
Pulls every supported Odoo model in dependency order and upserts into Aurora.

Import order (respects FK dependencies):
  1.  res.currency
  2.  res.country
  3.  res.country.state
  4.  account.payment.term
  5.  product.pricelist
  6.  res.users
  7.  crm.team  (+ team members)
  8.  res.partner.category  (partner tags)
  9.  res.partner
  10. product.category
  11. product.template      (products)
  12. product.product        (variants)
  13. product.pricelist.item
  14. crm.stage
  15. crm.tag
  16. crm.lead
  17. sale.order             (+ lines)
  18. account.move           (invoices, bills, refunds + lines)
  19. account.payment
  20. mail.activity.type
  21. mail.activity
  22. mail.message
  23. calendar.event         (meetings + attendees)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.communication import ActivityType
from app.models.crm import CrmStage, CrmTag
from app.models.lookup import Country, Currency, PaymentTerm, Pricelist, PricelistItem, State
from app.models.partner import Partner, PartnerTag
from app.models.product import Product, ProductCategory, ProductVariant
from app.models.user import SalesTeam, User, sales_team_members
from app.schemas.accounting import BulkInvoiceImport, BulkPaymentImport, OdooInvoiceImport, OdooInvoiceLineImport, OdooPaymentImport
from app.schemas.communication import BulkActivityImport, BulkMeetingImport, BulkMessageImport, OdooActivityImport, OdooMeetingImport, OdooMessageImport
from app.schemas.crm import BulkCrmLeadImport, OddoCrmLeadImport
from app.schemas.partner import BulkImportResponse, BulkPartnerImport, OdooPartnerImport
from app.schemas.product import BulkProductImport, OdooProductImport
from app.schemas.sales import BulkSaleOrderImport, OdooSaleOrderImport, OdooSaleOrderLineImport
from app.services import (
    accounting_service,
    communication_service,
    crm_service,
    partner_service,
    sales_service,
)
from app.services.base import m2m, m2o, upsert_by_odoo_id

logger = logging.getLogger(__name__)
settings = get_settings()


# ═════════════════════════════════════════════════════════════════════════════
# Low-level JSON-RPC client
# ═════════════════════════════════════════════════════════════════════════════
class OdooRPC:
    def __init__(self):
        self.url = settings.odoo_url
        self.db = settings.odoo_db
        self.username = settings.odoo_user
        self.password = settings.odoo_password
        self._uid: int | None = None

    async def authenticate(self, client: httpx.AsyncClient) -> int:
        if self._uid:
            return self._uid
        resp = await client.post(
            f"{self.url}/web/dataset/call_kw",
            json={
                "jsonrpc": "2.0", "method": "call", "id": 1,
                "params": {
                    "model": "res.users",
                    "method": "authenticate",
                    "args": [self.db, self.username, self.password, {}],
                    "kwargs": {},
                },
            },
        )
        resp.raise_for_status()
        self._uid = resp.json()["result"]
        logger.info("Authenticated as uid=%s", self._uid)
        return self._uid

    async def search_read(
        self,
        client: httpx.AsyncClient,
        model: str,
        domain: list,
        fields: list[str],
        limit: int = 500,
        offset: int = 0,
        order: str = "id asc",
    ) -> list[dict[str, Any]]:
        uid = await self.authenticate(client)
        resp = await client.post(
            f"{self.url}/web/dataset/call_kw",
            json={
                "jsonrpc": "2.0", "method": "call", "id": 2,
                "params": {
                    "model": model,
                    "method": "search_read",
                    "args": [domain],
                    "kwargs": {
                        "fields": fields,
                        "limit": limit,
                        "offset": offset,
                        "order": order,
                        "context": {"uid": uid, "lang": "en_US"},
                    },
                },
            },
        )
        resp.raise_for_status()
        return resp.json().get("result", [])

    async def fetch_all(
        self,
        client: httpx.AsyncClient,
        model: str,
        domain: list,
        fields: list[str],
        batch: int = 500,
    ) -> list[dict]:
        records: list[dict] = []
        offset = 0
        while True:
            batch_data = await self.search_read(client, model, domain, fields, limit=batch, offset=offset)
            if not batch_data:
                break
            records.extend(batch_data)
            logger.debug("%s → fetched %d (total %d)", model, len(batch_data), len(records))
            if len(batch_data) < batch:
                break
            offset += batch
        return records


# ═════════════════════════════════════════════════════════════════════════════
# Full import orchestrator
# ═════════════════════════════════════════════════════════════════════════════
class OdooImportService:
    def __init__(self):
        self.rpc = OdooRPC()

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _since_domain(since: datetime | None, field: str = "write_date") -> list:
        if since is None:
            return []
        return [[field, ">=", since.strftime("%Y-%m-%d %H:%M:%S")]]

    # ── 1. Currencies ─────────────────────────────────────────────────────────
    async def import_currencies(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        records = await self.rpc.fetch_all(
            client, "res.currency",
            self._since_domain(since),
            ["id", "name", "symbol", "name", "rounding", "active"],
        )
        c = u = 0
        for r in records:
            fields = dict(name=r["name"], symbol=r.get("symbol"), rounding=r.get("rounding"), active=r.get("active", True))
            _, was_new = await upsert_by_odoo_id(db, Currency, r["id"], fields)
            c += was_new; u += not was_new
        await db.flush()
        return {"model": "res.currency", "created": c, "updated": u}

    # ── 2. Countries ──────────────────────────────────────────────────────────
    async def import_countries(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        records = await self.rpc.fetch_all(
            client, "res.country",
            self._since_domain(since, "write_date"),
            ["id", "name", "code", "phone_code", "currency_id"],
        )
        c = u = 0
        for r in records:
            from sqlalchemy import select as sa_select
            currency_id: int | None = None
            if cid := m2o(r.get("currency_id")):
                res = await db.execute(sa_select(Currency.id).where(Currency.odoo_id == cid))
                currency_id = res.scalar_one_or_none()
            fields = dict(name=r["name"], code=r.get("code") or None, phone_code=r.get("phone_code") or None, currency_id=currency_id)
            _, was_new = await upsert_by_odoo_id(db, Country, r["id"], fields)
            c += was_new; u += not was_new
        await db.flush()
        return {"model": "res.country", "created": c, "updated": u}

    # ── 3. States ─────────────────────────────────────────────────────────────
    async def import_states(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        from sqlalchemy import select as sa_select
        records = await self.rpc.fetch_all(
            client, "res.country.state", [],
            ["id", "name", "code", "country_id"],
        )
        c = u = 0
        for r in records:
            country_id: int | None = None
            if cid := m2o(r.get("country_id")):
                res = await db.execute(sa_select(Country.id).where(Country.odoo_id == cid))
                country_id = res.scalar_one_or_none()
            if not country_id:
                continue
            fields = dict(name=r["name"], code=r.get("code") or None, country_id=country_id)
            _, was_new = await upsert_by_odoo_id(db, State, r["id"], fields)
            c += was_new; u += not was_new
        await db.flush()
        return {"model": "res.country.state", "created": c, "updated": u}

    # ── 4. Payment Terms ──────────────────────────────────────────────────────
    async def import_payment_terms(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        records = await self.rpc.fetch_all(client, "account.payment.term", [], ["id", "name", "note", "active"])
        c = u = 0
        for r in records:
            fields = dict(name=r["name"], note=r.get("note") or None, active=r.get("active", True))
            _, was_new = await upsert_by_odoo_id(db, PaymentTerm, r["id"], fields)
            c += was_new; u += not was_new
        await db.flush()
        return {"model": "account.payment.term", "created": c, "updated": u}

    # ── 5. Pricelists ─────────────────────────────────────────────────────────
    async def import_pricelists(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        from sqlalchemy import select as sa_select
        records = await self.rpc.fetch_all(client, "product.pricelist", [["active", "in", [True, False]]], ["id", "name", "currency_id", "active"])
        c = u = 0
        for r in records:
            currency_id = None
            if cid := m2o(r.get("currency_id")):
                res = await db.execute(sa_select(Currency.id).where(Currency.odoo_id == cid))
                currency_id = res.scalar_one_or_none()
            fields = dict(name=r["name"], currency_id=currency_id, active=r.get("active", True))
            _, was_new = await upsert_by_odoo_id(db, Pricelist, r["id"], fields)
            c += was_new; u += not was_new
        await db.flush()
        return {"model": "product.pricelist", "created": c, "updated": u}

    # ── 6. Users ──────────────────────────────────────────────────────────────
    async def import_users(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        records = await self.rpc.fetch_all(
            client, "res.users",
            self._since_domain(since),
            ["id", "name", "login", "email", "phone", "mobile", "lang", "tz", "active", "share"],
        )
        c = u = 0
        for r in records:
            fields = dict(
                name=r.get("name", ""), login=r.get("login"), email=r.get("email") or None,
                phone=r.get("phone") or None, mobile=r.get("mobile") or None,
                lang=r.get("lang") or None, tz=r.get("tz") or None,
                active=r.get("active", True), share=r.get("share", False),
            )
            _, was_new = await upsert_by_odoo_id(db, User, r["id"], fields)
            c += was_new; u += not was_new
        await db.flush()
        return {"model": "res.users", "created": c, "updated": u}

    # ── 7. Sales Teams ────────────────────────────────────────────────────────
    async def import_sales_teams(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        from sqlalchemy import select as sa_select
        records = await self.rpc.fetch_all(
            client, "crm.team", [],
            ["id", "name", "user_id", "alias_email", "active", "member_ids"],
        )
        c = u = 0
        for r in records:
            leader_uuid = None
            if lid := m2o(r.get("user_id")):
                res = await db.execute(sa_select(User.id).where(User.odoo_id == lid))
                leader_uuid = res.scalar_one_or_none()
            fields = dict(name=r["name"], leader_id=leader_uuid, alias_email=r.get("alias_email") or None, active=r.get("active", True))
            team, was_new = await upsert_by_odoo_id(db, SalesTeam, r["id"], fields)
            await db.flush()
            # Sync member associations
            member_odoo_ids = m2m(r.get("member_ids", []))
            if member_odoo_ids:
                member_uuids_res = await db.execute(sa_select(User.id).where(User.odoo_id.in_(member_odoo_ids)))
                member_uuids = list(member_uuids_res.scalars())
                members_res = await db.execute(sa_select(User).where(User.id.in_(member_uuids)))
                team.members = list(members_res.scalars())
            c += was_new; u += not was_new
        await db.flush()
        return {"model": "crm.team", "created": c, "updated": u}

    # ── 8. Partner Tags ───────────────────────────────────────────────────────
    async def import_partner_tags(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        records = await self.rpc.fetch_all(client, "res.partner.category", [], ["id", "name", "color"])
        c = u = 0
        for r in records:
            fields = dict(name=r["name"], color=f"#{r['color']:06x}" if isinstance(r.get("color"), int) else None)
            _, was_new = await upsert_by_odoo_id(db, PartnerTag, r["id"], fields)
            c += was_new; u += not was_new
        await db.flush()
        return {"model": "res.partner.category", "created": c, "updated": u}

    # ── 9. Partners ───────────────────────────────────────────────────────────
    async def import_partners(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        FIELDS = [
            "id", "name", "is_company", "parent_id", "company_name", "company_type",
            "email", "phone", "mobile", "website", "vat", "ref",
            "street", "street2", "city", "zip", "state_id", "country_id",
            "customer_rank", "supplier_rank", "lang", "tz",
            "property_payment_term_id", "comment", "active", "category_id",
            "create_date", "write_date",
        ]
        domain = self._since_domain(since) or [["active", "in", [True, False]]]
        records = await self.rpc.fetch_all(client, "res.partner", domain, FIELDS)
        schema_records = []
        for r in records:
            schema_records.append(OdooPartnerImport(
                id=r["id"], name=r.get("name") or "",
                is_company=bool(r.get("is_company")),
                parent_id=m2o(r.get("parent_id")),
                company_name=r.get("company_name") or None,
                company_type=r.get("company_type") or None,
                email=r.get("email") or None, phone=r.get("phone") or None,
                mobile=r.get("mobile") or None, website=r.get("website") or None,
                vat=r.get("vat") or None, ref=r.get("ref") or None,
                street=r.get("street") or None, street2=r.get("street2") or None,
                city=r.get("city") or None, zip=r.get("zip") or None,
                state_id=m2o(r.get("state_id")), country_id=m2o(r.get("country_id")),
                customer_rank=r.get("customer_rank", 0),
                supplier_rank=r.get("supplier_rank", 0),
                lang=r.get("lang") or None, tz=r.get("tz") or None,
                property_payment_term_id=m2o(r.get("property_payment_term_id")),
                comment=r.get("comment") or None, active=r.get("active", True),
                category_id=m2m(r.get("category_id", [])),
                create_date=r.get("create_date"), write_date=r.get("write_date"),
            ))
        result = await partner_service.bulk_upsert_partners(db, BulkPartnerImport(records=schema_records))
        return {"model": "res.partner", **result.model_dump()}

    # ── 10. Product Categories ────────────────────────────────────────────────
    async def import_product_categories(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        records = await self.rpc.fetch_all(client, "product.category", [], ["id", "name", "parent_id", "complete_name"])
        c = u = 0
        for r in records:
            fields = dict(name=r["name"], complete_name=r.get("complete_name") or None)
            _, was_new = await upsert_by_odoo_id(db, ProductCategory, r["id"], fields)
            c += was_new; u += not was_new
        await db.flush()
        # Second pass: resolve parent_id (self-ref needs all rows inserted first)
        from sqlalchemy import select as sa_select
        for r in records:
            if pid := m2o(r.get("parent_id")):
                res_parent = await db.execute(sa_select(ProductCategory.id).where(ProductCategory.odoo_id == pid))
                parent_local = res_parent.scalar_one_or_none()
                res_self = await db.execute(sa_select(ProductCategory).where(ProductCategory.odoo_id == r["id"]))
                obj = res_self.scalar_one_or_none()
                if obj and parent_local:
                    obj.parent_id = parent_local
        await db.flush()
        return {"model": "product.category", "created": c, "updated": u}

    # ── 11. Products (templates) ──────────────────────────────────────────────
    async def import_products(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        from sqlalchemy import select as sa_select
        FIELDS = [
            "id", "name", "description", "description_sale", "description_purchase",
            "type", "categ_id", "uom_id", "uom_po_id",
            "list_price", "standard_price", "taxes_id",
            "default_code", "barcode", "active", "sale_ok", "purchase_ok",
            "can_be_expensed", "invoice_policy", "weight", "volume",
        ]
        domain = self._since_domain(since) or [["active", "in", [True, False]]]
        records = await self.rpc.fetch_all(client, "product.template", domain, FIELDS)
        schemas = []
        for r in records:
            schemas.append(OdooProductImport(
                id=r["id"], name=r["name"],
                description=r.get("description") or None,
                description_sale=r.get("description_sale") or None,
                description_purchase=r.get("description_purchase") or None,
                type=r.get("type") or None, categ_id=m2o(r.get("categ_id")),
                list_price=r.get("list_price"), standard_price=r.get("standard_price"),
                default_code=r.get("default_code") or None,
                barcode=r.get("barcode") or None,
                active=r.get("active", True), sale_ok=r.get("sale_ok", True),
                purchase_ok=r.get("purchase_ok", True),
                can_be_expensed=r.get("can_be_expensed", False),
                invoice_policy=r.get("invoice_policy") or None,
                weight=r.get("weight"), volume=r.get("volume"),
                taxes_id=m2m(r.get("taxes_id", [])),
            ))
        c = u = 0
        for s in schemas:
            categ_id = None
            if s.categ_id:
                res = await db.execute(sa_select(ProductCategory.id).where(ProductCategory.odoo_id == s.categ_id))
                categ_id = res.scalar_one_or_none()
            fields = dict(
                name=s.name, description=s.description,
                description_sale=s.description_sale, description_purchase=s.description_purchase,
                type=s.type, categ_id=categ_id,
                list_price=s.list_price, standard_price=s.standard_price,
                default_code=s.default_code, barcode=s.barcode,
                active=s.active, sale_ok=s.sale_ok, purchase_ok=s.purchase_ok,
                can_be_expensed=s.can_be_expensed, invoice_policy=s.invoice_policy,
                weight=s.weight, volume=s.volume,
            )
            _, was_new = await upsert_by_odoo_id(db, Product, s.id, fields)
            c += was_new; u += not was_new
        await db.flush()
        return {"model": "product.template", "created": c, "updated": u}

    # ── 12. Product Variants ──────────────────────────────────────────────────
    async def import_product_variants(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        from sqlalchemy import select as sa_select
        records = await self.rpc.fetch_all(
            client, "product.product",
            [["active", "in", [True, False]]],
            ["id", "product_tmpl_id", "name", "default_code", "barcode", "price_extra", "active", "combination_indices"],
        )
        c = u = 0
        for r in records:
            product_uuid = None
            if tid := m2o(r.get("product_tmpl_id")):
                res = await db.execute(sa_select(Product.id).where(Product.odoo_id == tid))
                product_uuid = res.scalar_one_or_none()
            if not product_uuid:
                continue
            fields = dict(
                product_id=product_uuid, name=r.get("name") or None,
                default_code=r.get("default_code") or None,
                barcode=r.get("barcode") or None,
                price_extra=r.get("price_extra"), active=r.get("active", True),
                combination_indices=r.get("combination_indices") or None,
            )
            _, was_new = await upsert_by_odoo_id(db, ProductVariant, r["id"], fields)
            c += was_new; u += not was_new
        await db.flush()
        return {"model": "product.product", "created": c, "updated": u}

    # ── 13. Pricelist Items ───────────────────────────────────────────────────
    async def import_pricelist_items(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        from sqlalchemy import select as sa_select
        records = await self.rpc.fetch_all(
            client, "product.pricelist.item", [],
            ["id", "pricelist_id", "product_tmpl_id", "compute_price", "fixed_price",
             "percent_price", "price_discount", "min_quantity", "date_start", "date_end"],
        )
        c = u = 0
        for r in records:
            pl_id = None
            if ploid := m2o(r.get("pricelist_id")):
                res = await db.execute(sa_select(Pricelist.id).where(Pricelist.odoo_id == ploid))
                pl_id = res.scalar_one_or_none()
            if not pl_id:
                continue
            prod_id = None
            if toid := m2o(r.get("product_tmpl_id")):
                res = await db.execute(sa_select(Product.id).where(Product.odoo_id == toid))
                prod_id = res.scalar_one_or_none()
            fields = dict(
                pricelist_id=pl_id, product_id=prod_id,
                compute_price=r.get("compute_price"),
                fixed_price=r.get("fixed_price"), percent_price=r.get("percent_price"),
                price_discount=r.get("price_discount"), min_quantity=r.get("min_quantity"),
                date_start=str(r["date_start"]) if r.get("date_start") else None,
                date_end=str(r["date_end"]) if r.get("date_end") else None,
            )
            _, was_new = await upsert_by_odoo_id(db, PricelistItem, r["id"], fields)
            c += was_new; u += not was_new
        await db.flush()
        return {"model": "product.pricelist.item", "created": c, "updated": u}

    # ── 14. CRM Stages ────────────────────────────────────────────────────────
    async def import_crm_stages(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        records = await self.rpc.fetch_all(client, "crm.stage", [], ["id", "name", "sequence", "is_won", "requirements", "team_id"])
        c = u = 0
        for r in records:
            fields = dict(name=r["name"], sequence=r.get("sequence", 1), is_won=r.get("is_won", False), requirements=r.get("requirements") or None)
            _, was_new = await upsert_by_odoo_id(db, CrmStage, r["id"], fields)
            c += was_new; u += not was_new
        await db.flush()
        return {"model": "crm.stage", "created": c, "updated": u}

    # ── 15. CRM Tags ──────────────────────────────────────────────────────────
    async def import_crm_tags(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        records = await self.rpc.fetch_all(client, "crm.tag", [], ["id", "name", "color"])
        c = u = 0
        for r in records:
            fields = dict(name=r["name"], color=f"#{r['color']:06x}" if isinstance(r.get("color"), int) else None)
            _, was_new = await upsert_by_odoo_id(db, CrmTag, r["id"], fields)
            c += was_new; u += not was_new
        await db.flush()
        return {"model": "crm.tag", "created": c, "updated": u}

    # ── 16. CRM Leads ─────────────────────────────────────────────────────────
    async def import_crm_leads(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        FIELDS = [
            "id", "name", "type", "active", "stage_id", "priority", "kanban_state",
            "probability", "expected_revenue", "prorated_revenue",
            "partner_id", "partner_name", "contact_name", "email_from",
            "phone", "mobile", "street", "city", "country_id", "state_id",
            "user_id", "team_id", "date_open", "date_closed", "date_deadline",
            "source_id", "medium_id", "campaign_id", "referred", "lost_reason_id",
            "description", "tag_ids", "create_date", "write_date",
        ]
        domain = self._since_domain(since) or [["active", "in", [True, False]]]
        records = await self.rpc.fetch_all(client, "crm.lead", domain, FIELDS)
        schemas = [
            OddoCrmLeadImport(
                id=r["id"], name=r.get("name", ""),
                type=r.get("type", "lead"), active=r.get("active", True),
                stage_id=m2o(r.get("stage_id")), priority=r.get("priority", "0"),
                kanban_state=r.get("kanban_state"),
                probability=r.get("probability"),
                expected_revenue=r.get("expected_revenue"),
                prorated_revenue=r.get("prorated_revenue"),
                partner_id=m2o(r.get("partner_id")),
                partner_name=r.get("partner_name") or None,
                contact_name=r.get("contact_name") or None,
                email_from=r.get("email_from") or None,
                phone=r.get("phone") or None, mobile=r.get("mobile") or None,
                street=r.get("street") or None, city=r.get("city") or None,
                country_id=m2o(r.get("country_id")), state_id=m2o(r.get("state_id")),
                user_id=m2o(r.get("user_id")), team_id=m2o(r.get("team_id")),
                date_open=r.get("date_open"), date_closed=r.get("date_closed"),
                date_deadline=r.get("date_deadline"),
                description=r.get("description") or None,
                tag_ids=m2m(r.get("tag_ids", [])),
                create_date=r.get("create_date"), write_date=r.get("write_date"),
            ) for r in records
        ]
        result = await crm_service.bulk_upsert_leads(db, BulkCrmLeadImport(records=schemas))
        return {"model": "crm.lead", **result.model_dump()}

    # ── 17. Sale Orders ───────────────────────────────────────────────────────
    async def import_sale_orders(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        ORDER_FIELDS = [
            "id", "name", "state", "client_order_ref", "partner_id",
            "partner_invoice_id", "partner_shipping_id", "user_id", "team_id",
            "date_order", "validity_date", "pricelist_id", "payment_term_id",
            "currency_id", "amount_untaxed", "amount_tax", "amount_total",
            "invoice_status", "note", "opportunity_id",
            "order_line", "create_date", "write_date",
        ]
        LINE_FIELDS = [
            "id", "product_id", "product_uom_qty", "qty_delivered", "qty_invoiced",
            "name", "sequence", "price_unit", "discount",
            "price_subtotal", "price_tax", "price_total", "tax_id",
            "is_downpayment", "state",
        ]
        domain = self._since_domain(since) or [["state", "not in", ["cancel"]]]
        records = await self.rpc.fetch_all(client, "sale.order", domain, ORDER_FIELDS)
        schemas = []
        for r in records:
            # Fetch lines for this order
            line_ids = m2m(r.get("order_line", []))
            lines_raw = []
            if line_ids:
                lines_raw = await self.rpc.search_read(
                    client, "sale.order.line",
                    [["id", "in", line_ids]], LINE_FIELDS
                )
            schemas.append(OdooSaleOrderImport(
                id=r["id"], name=r["name"], state=r.get("state", "draft"),
                client_order_ref=r.get("client_order_ref") or None,
                partner_id=m2o(r.get("partner_id")),
                partner_invoice_id=m2o(r.get("partner_invoice_id")),
                partner_shipping_id=m2o(r.get("partner_shipping_id")),
                user_id=m2o(r.get("user_id")), team_id=m2o(r.get("team_id")),
                date_order=r.get("date_order"), validity_date=r.get("validity_date"),
                pricelist_id=m2o(r.get("pricelist_id")),
                payment_term_id=m2o(r.get("payment_term_id")),
                currency_id=m2o(r.get("currency_id")),
                amount_untaxed=r.get("amount_untaxed"), amount_tax=r.get("amount_tax"),
                amount_total=r.get("amount_total"), invoice_status=r.get("invoice_status"),
                note=r.get("note") or None, opportunity_id=m2o(r.get("opportunity_id")),
                create_date=r.get("create_date"), write_date=r.get("write_date"),
                order_line=[
                    OdooSaleOrderLineImport(
                        id=l["id"], product_id=m2o(l.get("product_id")),
                        product_uom_qty=l.get("product_uom_qty", 1),
                        qty_delivered=l.get("qty_delivered"),
                        qty_invoiced=l.get("qty_invoiced"),
                        name=l.get("name"), sequence=l.get("sequence", 10),
                        price_unit=l.get("price_unit"), discount=l.get("discount"),
                        price_subtotal=l.get("price_subtotal"),
                        price_tax=l.get("price_tax"), price_total=l.get("price_total"),
                        tax_id=m2m(l.get("tax_id", [])),
                        is_downpayment=l.get("is_downpayment", False),
                        state=l.get("state"),
                    ) for l in lines_raw
                ],
            ))
        result = await sales_service.bulk_upsert_orders(db, BulkSaleOrderImport(records=schemas))
        return {"model": "sale.order", **result.model_dump()}

    # ── 18. Invoices ──────────────────────────────────────────────────────────
    async def import_invoices(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        MOVE_FIELDS = [
            "id", "name", "ref", "move_type", "state", "payment_state",
            "partner_id", "partner_shipping_id", "invoice_date", "invoice_date_due",
            "currency_id", "payment_term_id",
            "amount_untaxed", "amount_tax", "amount_total", "amount_residual", "amount_total_signed",
            "narration", "invoice_origin", "invoice_line_ids", "create_date", "write_date",
        ]
        LINE_FIELDS = [
            "id", "product_id", "name", "sequence", "account_id",
            "quantity", "price_unit", "discount",
            "price_subtotal", "price_total", "tax_ids", "display_type",
        ]
        domain = self._since_domain(since) or [["move_type", "in", ["out_invoice", "in_invoice", "out_refund", "in_refund"]]]
        records = await self.rpc.fetch_all(client, "account.move", domain, MOVE_FIELDS)
        schemas = []
        for r in records:
            line_ids = m2m(r.get("invoice_line_ids", []))
            lines_raw = []
            if line_ids:
                lines_raw = await self.rpc.search_read(client, "account.move.line", [["id", "in", line_ids]], LINE_FIELDS)
            schemas.append(OdooInvoiceImport(
                id=r["id"], name=r.get("name") or None, ref=r.get("ref") or None,
                move_type=r["move_type"], state=r.get("state", "draft"),
                payment_state=r.get("payment_state"),
                partner_id=m2o(r.get("partner_id")),
                invoice_date=r.get("invoice_date"), invoice_date_due=r.get("invoice_date_due"),
                currency_id=m2o(r.get("currency_id")),
                payment_term_id=m2o(r.get("payment_term_id")),
                amount_untaxed=r.get("amount_untaxed"), amount_tax=r.get("amount_tax"),
                amount_total=r.get("amount_total"), amount_residual=r.get("amount_residual"),
                amount_total_signed=r.get("amount_total_signed"),
                narration=r.get("narration") or None, invoice_origin=r.get("invoice_origin") or None,
                create_date=r.get("create_date"), write_date=r.get("write_date"),
                invoice_line_ids=[
                    OdooInvoiceLineImport(
                        id=l["id"], product_id=m2o(l.get("product_id")),
                        name=l.get("name"), sequence=l.get("sequence", 10),
                        quantity=l.get("quantity"), price_unit=l.get("price_unit"),
                        discount=l.get("discount"), price_subtotal=l.get("price_subtotal"),
                        price_total=l.get("price_total"),
                        tax_ids=m2m(l.get("tax_ids", [])), display_type=l.get("display_type"),
                    ) for l in lines_raw if l.get("display_type") in (None, False, "line_section", "line_note")
                ],
            ))
        result = await accounting_service.bulk_upsert_invoices(db, BulkInvoiceImport(records=schemas))
        return {"model": "account.move", **result.model_dump()}

    # ── 19. Payments ──────────────────────────────────────────────────────────
    async def import_payments(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        FIELDS = ["id", "name", "payment_type", "partner_type", "state", "partner_id", "currency_id", "payment_method_id", "journal_id", "amount", "date", "ref", "create_date"]
        domain = self._since_domain(since) or [["state", "!=", "draft"]]
        records = await self.rpc.fetch_all(client, "account.payment", domain, FIELDS)
        schemas = [
            OdooPaymentImport(
                id=r["id"], name=r.get("name") or None,
                payment_type=r.get("payment_type", "inbound"),
                partner_type=r.get("partner_type") or None, state=r.get("state", "draft"),
                partner_id=m2o(r.get("partner_id")), currency_id=m2o(r.get("currency_id")),
                payment_method_id=m2o(r.get("payment_method_id")),
                journal_id=m2o(r.get("journal_id")),
                amount=r.get("amount", 0), date=r.get("date"),
                ref=r.get("ref") or None, create_date=r.get("create_date"),
            ) for r in records
        ]
        result = await accounting_service.bulk_upsert_payments(db, BulkPaymentImport(records=schemas))
        return {"model": "account.payment", **result.model_dump()}

    # ── 20. Activity Types ────────────────────────────────────────────────────
    async def import_activity_types(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        records = await self.rpc.fetch_all(
            client, "mail.activity.type", [],
            ["id", "name", "summary", "icon", "decoration_type", "delay_count", "delay_unit", "delay_from", "category"],
        )
        c = u = 0
        for r in records:
            fields = dict(
                name=r["name"], summary=r.get("summary") or None,
                icon=r.get("icon") or None, decoration_type=r.get("decoration_type") or None,
                delay_count=r.get("delay_count"), delay_unit=r.get("delay_unit") or None,
                delay_from=r.get("delay_from") or None, category=r.get("category") or None,
            )
            _, was_new = await upsert_by_odoo_id(db, ActivityType, r["id"], fields)
            c += was_new; u += not was_new
        await db.flush()
        return {"model": "mail.activity.type", "created": c, "updated": u}

    # ── 21. Activities ────────────────────────────────────────────────────────
    async def import_activities(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        FIELDS = ["id", "activity_type_id", "user_id", "res_model", "res_id", "res_name", "summary", "note", "date_deadline", "date_done", "activity_category", "create_date"]
        domain = self._since_domain(since, "create_date") or []
        records = await self.rpc.fetch_all(client, "mail.activity", domain, FIELDS)
        schemas = [
            OdooActivityImport(
                id=r["id"], activity_type_id=m2o(r.get("activity_type_id")),
                user_id=m2o(r.get("user_id")),
                res_model=r.get("res_model"), res_id=r.get("res_id"),
                res_name=r.get("res_name") or None,
                summary=r.get("summary") or None, note=r.get("note") or None,
                date_deadline=r.get("date_deadline"), create_date=r.get("create_date"),
            ) for r in records
        ]
        result = await communication_service.bulk_upsert_activities(db, BulkActivityImport(records=schemas))
        return {"model": "mail.activity", **result.model_dump()}

    # ── 22. Messages ──────────────────────────────────────────────────────────
    async def import_messages(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        FIELDS = ["id", "author_id", "res_model", "res_id", "res_name", "message_type", "subtype_xmlid", "subject", "body", "date", "email_from", "reply_to", "message_id", "parent_id", "is_internal"]
        # Only import chatter messages (exclude system notifications)
        domain = [["message_type", "in", ["comment", "email"]]]
        if since:
            domain.append(["date", ">=", since.strftime("%Y-%m-%d %H:%M:%S")])
        records = await self.rpc.fetch_all(client, "mail.message", domain, FIELDS)
        schemas = [
            OdooMessageImport(
                id=r["id"], author_id=m2o(r.get("author_id")),
                res_model=r.get("res_model"), res_id=r.get("res_id"),
                res_name=r.get("res_name") or None,
                message_type=r.get("message_type", "comment"),
                subject=r.get("subject") or None, body=r.get("body") or None,
                date=r.get("date"), email_from=r.get("email_from") or None,
                reply_to=r.get("reply_to") or None,
                message_id=r.get("message_id") or None,
                parent_id=m2o(r.get("parent_id")),
                is_internal=r.get("is_internal", False),
            ) for r in records
        ]
        result = await communication_service.bulk_upsert_messages(db, BulkMessageImport(records=schemas))
        return {"model": "mail.message", **result.model_dump()}

    # ── 23. Meetings ──────────────────────────────────────────────────────────
    async def import_meetings(self, client: httpx.AsyncClient, db: AsyncSession, since=None) -> dict:
        FIELDS = ["id", "name", "description", "user_id", "start", "stop", "allday", "start_date", "stop_date", "location", "videocall_location", "privacy", "show_as", "active", "recurrency", "rrule", "opportunity_id", "partner_ids", "create_date", "write_date"]
        domain = self._since_domain(since) or [["active", "in", [True, False]]]
        records = await self.rpc.fetch_all(client, "calendar.event", domain, FIELDS)
        schemas = [
            OdooMeetingImport(
                id=r["id"], name=r["name"],
                description=r.get("description") or None,
                user_id=m2o(r.get("user_id")),
                start=r.get("start"), stop=r.get("stop"),
                allday=r.get("allday", False),
                start_date=r.get("start_date"), stop_date=r.get("stop_date"),
                location=r.get("location") or None,
                videocall_location=r.get("videocall_location") or None,
                privacy=r.get("privacy") or None, show_as=r.get("show_as") or None,
                active=r.get("active", True), recurrency=r.get("recurrency", False),
                rrule=r.get("rrule") or None,
                opportunity_id=m2o(r.get("opportunity_id")),
                partner_ids=m2m(r.get("partner_ids", [])),
                create_date=r.get("create_date"), write_date=r.get("write_date"),
            ) for r in records
        ]
        result = await communication_service.bulk_upsert_meetings(db, BulkMeetingImport(records=schemas))
        return {"model": "calendar.event", **result.model_dump()}

    # ═════════════════════════════════════════════════════════════════════════
    # Public API
    # ═════════════════════════════════════════════════════════════════════════
    async def run_full_import(self, db: AsyncSession) -> list[dict]:
        """Import ALL models in dependency order."""
        return await self._run(db, since=None)

    async def run_incremental_import(self, db: AsyncSession, since: datetime | None = None) -> list[dict]:
        """Import only records modified since `since` (UTC). Defaults to today midnight."""
        if since is None:
            since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        return await self._run(db, since=since)

    async def _run(self, db: AsyncSession, since: datetime | None) -> list[dict]:
        results = []
        async with httpx.AsyncClient(timeout=120) as client:
            steps = [
                self.import_currencies,
                self.import_countries,
                self.import_states,
                self.import_payment_terms,
                self.import_pricelists,
                self.import_users,
                self.import_sales_teams,
                self.import_partner_tags,
                self.import_partners,
                self.import_product_categories,
                self.import_products,
                self.import_product_variants,
                self.import_pricelist_items,
                self.import_crm_stages,
                self.import_crm_tags,
                self.import_crm_leads,
                self.import_sale_orders,
                self.import_invoices,
                self.import_payments,
                self.import_activity_types,
                self.import_activities,
                self.import_messages,
                self.import_meetings,
            ]
            for step in steps:
                try:
                    result = await step(client, db, since)
                    results.append(result)
                    logger.info("✓ %s → created=%s updated=%s", result.get("model"), result.get("created"), result.get("updated"))
                except Exception as exc:
                    logger.error("✗ step %s failed: %s", step.__name__, exc)
                    results.append({"step": step.__name__, "error": str(exc)})
        return results
