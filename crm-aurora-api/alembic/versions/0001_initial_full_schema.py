"""Full Odoo CRM schema — all 28 tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01 00:00:00
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── currencies ────────────────────────────────────────────────────────────
    op.create_table("currencies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("symbol", sa.String(8), nullable=True),
        sa.Column("code", sa.String(3), nullable=True, unique=True),
        sa.Column("rounding", sa.Float(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true"),
    )
    op.create_index("ix_currencies_odoo_id", "currencies", ["odoo_id"], unique=True)

    # ── countries ─────────────────────────────────────────────────────────────
    op.create_table("countries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("code", sa.String(3), nullable=True, unique=True),
        sa.Column("phone_code", sa.String(10), nullable=True),
        sa.Column("currency_id", sa.Integer(), sa.ForeignKey("currencies.id"), nullable=True),
    )
    op.create_index("ix_countries_odoo_id", "countries", ["odoo_id"], unique=True)

    # ── states ────────────────────────────────────────────────────────────────
    op.create_table("states",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("country_id", sa.Integer(), sa.ForeignKey("countries.id"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("code", sa.String(10), nullable=True),
        sa.UniqueConstraint("country_id", "code"),
    )
    op.create_index("ix_states_odoo_id", "states", ["odoo_id"], unique=True)

    # ── payment_terms ─────────────────────────────────────────────────────────
    op.create_table("payment_terms",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(256), nullable=False, unique=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true"),
    )
    op.create_index("ix_payment_terms_odoo_id", "payment_terms", ["odoo_id"], unique=True)

    # ── pricelists ────────────────────────────────────────────────────────────
    op.create_table("pricelists",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("currency_id", sa.Integer(), sa.ForeignKey("currencies.id"), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true"),
    )
    op.create_index("ix_pricelists_odoo_id", "pricelists", ["odoo_id"], unique=True)

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table("users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("login", sa.String(256), nullable=True, unique=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("mobile", sa.String(64), nullable=True),
        sa.Column("lang", sa.String(16), nullable=True),
        sa.Column("tz", sa.String(64), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true"),
        sa.Column("share", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_odoo_id", "users", ["odoo_id"], unique=True)
    op.create_index("ix_users_email", "users", ["email"])

    # ── sales_teams ───────────────────────────────────────────────────────────
    op.create_table("sales_teams",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("leader_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("alias_email", sa.String(320), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true"),
    )
    op.create_index("ix_sales_teams_odoo_id", "sales_teams", ["odoo_id"], unique=True)

    # ── sales_team_members ────────────────────────────────────────────────────
    op.create_table("sales_team_members",
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("sales_teams.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    )

    # ── partner_tags ──────────────────────────────────────────────────────────
    op.create_table("partner_tags",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("color", sa.String(7), nullable=True),
    )
    op.create_index("ix_partner_tags_odoo_id", "partner_tags", ["odoo_id"], unique=True)

    # ── partners ──────────────────────────────────────────────────────────────
    op.create_table("partners",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("odoo_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("odoo_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("is_company", sa.Boolean(), server_default="false"),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id", ondelete="SET NULL"), nullable=True),
        sa.Column("company_name", sa.String(256), nullable=True),
        sa.Column("company_type", sa.String(32), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("mobile", sa.String(64), nullable=True),
        sa.Column("website", sa.String(512), nullable=True),
        sa.Column("vat", sa.String(64), nullable=True),
        sa.Column("ref", sa.String(64), nullable=True),
        sa.Column("street", sa.String(256), nullable=True),
        sa.Column("street2", sa.String(256), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("zip_code", sa.String(20), nullable=True),
        sa.Column("state_id", sa.Integer(), sa.ForeignKey("states.id"), nullable=True),
        sa.Column("country_id", sa.Integer(), sa.ForeignKey("countries.id"), nullable=True),
        sa.Column("customer_rank", sa.Integer(), server_default="0"),
        sa.Column("supplier_rank", sa.Integer(), server_default="0"),
        sa.Column("partner_type", sa.String(32), nullable=True),
        sa.Column("lang", sa.String(16), nullable=True),
        sa.Column("tz", sa.String(64), nullable=True),
        sa.Column("payment_term_id", sa.Integer(), sa.ForeignKey("payment_terms.id"), nullable=True),
        sa.Column("property_account_receivable_id", sa.Integer(), nullable=True),
        sa.Column("property_account_payable_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_partners_odoo_id", "partners", ["odoo_id"], unique=True)
    op.create_index("ix_partners_name", "partners", ["name"])
    op.create_index("ix_partners_email", "partners", ["email"])
    op.create_index("ix_partners_parent_id", "partners", ["parent_id"])
    op.create_index("ix_partners_country_id", "partners", ["country_id"])

    # ── partner_partner_tags ──────────────────────────────────────────────────
    op.create_table("partner_partner_tags",
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("partner_tags.id", ondelete="CASCADE"), primary_key=True),
    )

    # ── product_categories ────────────────────────────────────────────────────
    op.create_table("product_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("product_categories.id"), nullable=True),
        sa.Column("complete_name", sa.String(512), nullable=True),
    )
    op.create_index("ix_product_categories_odoo_id", "product_categories", ["odoo_id"], unique=True)

    # ── products ──────────────────────────────────────────────────────────────
    op.create_table("products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("description_sale", sa.Text(), nullable=True),
        sa.Column("description_purchase", sa.Text(), nullable=True),
        sa.Column("type", sa.String(32), nullable=True),
        sa.Column("categ_id", sa.Integer(), sa.ForeignKey("product_categories.id"), nullable=True),
        sa.Column("uom_name", sa.String(64), nullable=True),
        sa.Column("uom_po_name", sa.String(64), nullable=True),
        sa.Column("list_price", sa.Numeric(16, 4), nullable=True),
        sa.Column("standard_price", sa.Numeric(16, 4), nullable=True),
        sa.Column("taxes_name", sa.String(256), nullable=True),
        sa.Column("default_code", sa.String(64), nullable=True),
        sa.Column("barcode", sa.String(128), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true"),
        sa.Column("sale_ok", sa.Boolean(), server_default="true"),
        sa.Column("purchase_ok", sa.Boolean(), server_default="true"),
        sa.Column("can_be_expensed", sa.Boolean(), server_default="false"),
        sa.Column("invoice_policy", sa.String(32), nullable=True),
        sa.Column("weight", sa.Numeric(16, 4), nullable=True),
        sa.Column("volume", sa.Numeric(16, 4), nullable=True),
    )
    op.create_index("ix_products_odoo_id", "products", ["odoo_id"], unique=True)
    op.create_index("ix_products_name", "products", ["name"])
    op.create_index("ix_products_default_code", "products", ["default_code"])

    # ── product_variants ──────────────────────────────────────────────────────
    op.create_table("product_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("name", sa.String(512), nullable=True),
        sa.Column("default_code", sa.String(64), nullable=True),
        sa.Column("barcode", sa.String(128), nullable=True),
        sa.Column("price_extra", sa.Numeric(16, 4), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true"),
        sa.Column("combination_indices", sa.String(255), nullable=True),
    )
    op.create_index("ix_product_variants_odoo_id", "product_variants", ["odoo_id"], unique=True)
    op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"])

    # ── pricelist_items ───────────────────────────────────────────────────────
    op.create_table("pricelist_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("pricelist_id", sa.Integer(), sa.ForeignKey("pricelists.id"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("compute_price", sa.String(32), nullable=True),
        sa.Column("fixed_price", sa.Numeric(16, 4), nullable=True),
        sa.Column("percent_price", sa.Numeric(8, 4), nullable=True),
        sa.Column("price_discount", sa.Numeric(8, 4), nullable=True),
        sa.Column("min_quantity", sa.Numeric(16, 4), nullable=True),
        sa.Column("date_start", sa.String(32), nullable=True),
        sa.Column("date_end", sa.String(32), nullable=True),
    )
    op.create_index("ix_pricelist_items_odoo_id", "pricelist_items", ["odoo_id"], unique=True)

    # ── crm_stages ────────────────────────────────────────────────────────────
    op.create_table("crm_stages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("sequence", sa.Integer(), server_default="1"),
        sa.Column("is_won", sa.Boolean(), server_default="false"),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("sales_teams.id"), nullable=True),
    )
    op.create_index("ix_crm_stages_odoo_id", "crm_stages", ["odoo_id"], unique=True)

    # ── crm_tags ──────────────────────────────────────────────────────────────
    op.create_table("crm_tags",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("color", sa.String(7), nullable=True),
    )
    op.create_index("ix_crm_tags_odoo_id", "crm_tags", ["odoo_id"], unique=True)

    # ── crm_leads ─────────────────────────────────────────────────────────────
    op.create_table("crm_leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("odoo_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("odoo_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("type", sa.String(16), server_default="'lead'"),
        sa.Column("active", sa.Boolean(), server_default="true"),
        sa.Column("stage_id", sa.Integer(), sa.ForeignKey("crm_stages.id"), nullable=True),
        sa.Column("priority", sa.String(1), server_default="'0'"),
        sa.Column("kanban_state", sa.String(32), nullable=True),
        sa.Column("probability", sa.Float(), nullable=True),
        sa.Column("automated_probability", sa.Float(), nullable=True),
        sa.Column("expected_revenue", sa.Numeric(16, 4), nullable=True),
        sa.Column("prorated_revenue", sa.Numeric(16, 4), nullable=True),
        sa.Column("recurring_revenue", sa.Numeric(16, 4), nullable=True),
        sa.Column("recurring_plan", sa.String(64), nullable=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id"), nullable=True),
        sa.Column("partner_name", sa.String(256), nullable=True),
        sa.Column("contact_name", sa.String(256), nullable=True),
        sa.Column("email_from", sa.String(320), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("mobile", sa.String(64), nullable=True),
        sa.Column("website", sa.String(512), nullable=True),
        sa.Column("street", sa.String(256), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("country_id", sa.Integer(), sa.ForeignKey("countries.id"), nullable=True),
        sa.Column("state_id", sa.Integer(), sa.ForeignKey("states.id"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("sales_teams.id"), nullable=True),
        sa.Column("date_open", sa.DateTime(timezone=True), nullable=True),
        sa.Column("date_closed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("date_deadline", sa.Date(), nullable=True),
        sa.Column("date_last_stage_update", sa.DateTime(timezone=True), nullable=True),
        sa.Column("date_conversion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_name", sa.String(256), nullable=True),
        sa.Column("medium_name", sa.String(256), nullable=True),
        sa.Column("campaign_name", sa.String(256), nullable=True),
        sa.Column("referred", sa.String(256), nullable=True),
        sa.Column("lost_reason_name", sa.String(256), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_crm_leads_odoo_id", "crm_leads", ["odoo_id"], unique=True)
    op.create_index("ix_crm_leads_partner_id", "crm_leads", ["partner_id"])
    op.create_index("ix_crm_leads_user_id", "crm_leads", ["user_id"])
    op.create_index("ix_crm_leads_stage_id", "crm_leads", ["stage_id"])

    # ── crm_lead_tags ─────────────────────────────────────────────────────────
    op.create_table("crm_lead_tags",
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm_leads.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("crm_tags.id", ondelete="CASCADE"), primary_key=True),
    )

    # ── sale_orders ───────────────────────────────────────────────────────────
    op.create_table("sale_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("odoo_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("odoo_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("state", sa.String(32), server_default="'draft'"),
        sa.Column("client_order_ref", sa.String(256), nullable=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id"), nullable=True),
        sa.Column("partner_invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id"), nullable=True),
        sa.Column("partner_shipping_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("sales_teams.id"), nullable=True),
        sa.Column("date_order", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validity_date", sa.Date(), nullable=True),
        sa.Column("commitment_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expected_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pricelist_id", sa.Integer(), sa.ForeignKey("pricelists.id"), nullable=True),
        sa.Column("payment_term_id", sa.Integer(), sa.ForeignKey("payment_terms.id"), nullable=True),
        sa.Column("currency_name", sa.String(16), nullable=True),
        sa.Column("amount_untaxed", sa.Numeric(16, 4), nullable=True),
        sa.Column("amount_tax", sa.Numeric(16, 4), nullable=True),
        sa.Column("amount_total", sa.Numeric(16, 4), nullable=True),
        sa.Column("amount_to_invoice", sa.Numeric(16, 4), nullable=True),
        sa.Column("invoice_status", sa.String(32), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("internal_note", sa.Text(), nullable=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm_leads.id"), nullable=True),
        sa.Column("source_name", sa.String(256), nullable=True),
        sa.Column("medium_name", sa.String(256), nullable=True),
        sa.Column("campaign_name", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_sale_orders_odoo_id", "sale_orders", ["odoo_id"], unique=True)
    op.create_index("ix_sale_orders_name", "sale_orders", ["name"])
    op.create_index("ix_sale_orders_partner_id", "sale_orders", ["partner_id"])

    # ── sale_order_lines ──────────────────────────────────────────────────────
    op.create_table("sale_order_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sale_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("product_variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_variants.id"), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("sequence", sa.Integer(), server_default="10"),
        sa.Column("product_uom_qty", sa.Numeric(16, 4), server_default="1"),
        sa.Column("qty_delivered", sa.Numeric(16, 4), nullable=True),
        sa.Column("qty_invoiced", sa.Numeric(16, 4), nullable=True),
        sa.Column("qty_to_invoice", sa.Numeric(16, 4), nullable=True),
        sa.Column("price_unit", sa.Numeric(16, 4), nullable=True),
        sa.Column("discount", sa.Numeric(8, 4), nullable=True),
        sa.Column("price_subtotal", sa.Numeric(16, 4), nullable=True),
        sa.Column("price_tax", sa.Numeric(16, 4), nullable=True),
        sa.Column("price_total", sa.Numeric(16, 4), nullable=True),
        sa.Column("tax_names", sa.String(256), nullable=True),
        sa.Column("is_downpayment", sa.Boolean(), server_default="false"),
        sa.Column("state", sa.String(32), nullable=True),
    )
    op.create_index("ix_sale_order_lines_odoo_id", "sale_order_lines", ["odoo_id"], unique=True)
    op.create_index("ix_sale_order_lines_order_id", "sale_order_lines", ["order_id"])

    # ── invoices ──────────────────────────────────────────────────────────────
    op.create_table("invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("odoo_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("odoo_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(64), nullable=True),
        sa.Column("ref", sa.String(256), nullable=True),
        sa.Column("move_type", sa.String(32), nullable=False),
        sa.Column("state", sa.String(32), server_default="'draft'"),
        sa.Column("payment_state", sa.String(32), nullable=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id"), nullable=True),
        sa.Column("partner_shipping_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id"), nullable=True),
        sa.Column("invoice_date", sa.Date(), nullable=True),
        sa.Column("invoice_date_due", sa.Date(), nullable=True),
        sa.Column("delivery_date", sa.Date(), nullable=True),
        sa.Column("currency_id", sa.Integer(), sa.ForeignKey("currencies.id"), nullable=True),
        sa.Column("payment_term_id", sa.Integer(), sa.ForeignKey("payment_terms.id"), nullable=True),
        sa.Column("amount_untaxed", sa.Numeric(16, 4), nullable=True),
        sa.Column("amount_tax", sa.Numeric(16, 4), nullable=True),
        sa.Column("amount_total", sa.Numeric(16, 4), nullable=True),
        sa.Column("amount_residual", sa.Numeric(16, 4), nullable=True),
        sa.Column("amount_total_signed", sa.Numeric(16, 4), nullable=True),
        sa.Column("sale_order_ids", sa.Text(), nullable=True),
        sa.Column("narration", sa.Text(), nullable=True),
        sa.Column("invoice_origin", sa.String(256), nullable=True),
        sa.Column("fiscal_position_name", sa.String(256), nullable=True),
        sa.Column("auto_post", sa.String(32), nullable=True),
        sa.Column("reversed_entry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("invoices.id"), nullable=True),
        sa.Column("sequence_number", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_invoices_odoo_id", "invoices", ["odoo_id"], unique=True)
    op.create_index("ix_invoices_partner_id", "invoices", ["partner_id"])
    op.create_index("ix_invoices_invoice_date", "invoices", ["invoice_date"])

    # ── invoice_lines ─────────────────────────────────────────────────────────
    op.create_table("invoice_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("move_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("sequence", sa.Integer(), server_default="10"),
        sa.Column("account_name", sa.String(256), nullable=True),
        sa.Column("quantity", sa.Numeric(16, 4), nullable=True),
        sa.Column("price_unit", sa.Numeric(16, 4), nullable=True),
        sa.Column("discount", sa.Numeric(8, 4), nullable=True),
        sa.Column("price_subtotal", sa.Numeric(16, 4), nullable=True),
        sa.Column("price_total", sa.Numeric(16, 4), nullable=True),
        sa.Column("tax_names", sa.String(256), nullable=True),
        sa.Column("display_type", sa.String(32), nullable=True),
    )
    op.create_index("ix_invoice_lines_odoo_id", "invoice_lines", ["odoo_id"], unique=True)
    op.create_index("ix_invoice_lines_move_id", "invoice_lines", ["move_id"])

    # ── payments ──────────────────────────────────────────────────────────────
    op.create_table("payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("odoo_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(64), nullable=True),
        sa.Column("payment_type", sa.String(32), nullable=False),
        sa.Column("partner_type", sa.String(32), nullable=True),
        sa.Column("state", sa.String(32), server_default="'draft'"),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id"), nullable=True),
        sa.Column("currency_id", sa.Integer(), sa.ForeignKey("currencies.id"), nullable=True),
        sa.Column("payment_method_name", sa.String(128), nullable=True),
        sa.Column("journal_name", sa.String(128), nullable=True),
        sa.Column("amount", sa.Numeric(16, 4), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("memo", sa.String(256), nullable=True),
        sa.Column("destination_account_name", sa.String(256), nullable=True),
        sa.Column("reconciled_invoice_ids", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_payments_odoo_id", "payments", ["odoo_id"], unique=True)
    op.create_index("ix_payments_partner_id", "payments", ["partner_id"])
    op.create_index("ix_payments_payment_date", "payments", ["payment_date"])

    # ── activity_types ────────────────────────────────────────────────────────
    op.create_table("activity_types",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("summary", sa.String(256), nullable=True),
        sa.Column("icon", sa.String(64), nullable=True),
        sa.Column("decoration_type", sa.String(32), nullable=True),
        sa.Column("delay_count", sa.Integer(), nullable=True),
        sa.Column("delay_unit", sa.String(16), nullable=True),
        sa.Column("delay_from", sa.String(32), nullable=True),
        sa.Column("category", sa.String(32), nullable=True),
    )
    op.create_index("ix_activity_types_odoo_id", "activity_types", ["odoo_id"], unique=True)

    # ── activities ────────────────────────────────────────────────────────────
    op.create_table("activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("odoo_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activity_type_id", sa.Integer(), sa.ForeignKey("activity_types.id"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("res_model", sa.String(128), nullable=True),
        sa.Column("res_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("res_name", sa.String(256), nullable=True),
        sa.Column("summary", sa.String(256), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("date_deadline", sa.Date(), nullable=True),
        sa.Column("date_done", sa.Date(), nullable=True),
        sa.Column("state", sa.String(32), nullable=True),
        sa.Column("calendar_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_activities_odoo_id", "activities", ["odoo_id"], unique=True)
    op.create_index("ix_activities_res_model", "activities", ["res_model"])
    op.create_index("ix_activities_user_id", "activities", ["user_id"])
    op.create_index("ix_activities_date_deadline", "activities", ["date_deadline"])

    # ── messages ──────────────────────────────────────────────────────────────
    op.create_table("messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("res_model", sa.String(128), nullable=True),
        sa.Column("res_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("res_name", sa.String(256), nullable=True),
        sa.Column("message_type", sa.String(32), server_default="'comment'"),
        sa.Column("subtype_name", sa.String(128), nullable=True),
        sa.Column("subject", sa.String(512), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email_from", sa.String(320), nullable=True),
        sa.Column("reply_to", sa.String(320), nullable=True),
        sa.Column("message_id", sa.String(512), nullable=True),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("is_internal", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_messages_odoo_id", "messages", ["odoo_id"], unique=True)
    op.create_index("ix_messages_res_model", "messages", ["res_model"])
    op.create_index("ix_messages_date", "messages", ["date"])

    # ── meetings ──────────────────────────────────────────────────────────────
    op.create_table("meetings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("odoo_id", sa.Integer(), nullable=True),
        sa.Column("odoo_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("organizer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stop", sa.DateTime(timezone=True), nullable=True),
        sa.Column("allday", sa.Boolean(), server_default="false"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("stop_date", sa.Date(), nullable=True),
        sa.Column("location", sa.String(512), nullable=True),
        sa.Column("videocall_location", sa.String(512), nullable=True),
        sa.Column("privacy", sa.String(32), nullable=True),
        sa.Column("show_as", sa.String(32), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true"),
        sa.Column("recurrency", sa.Boolean(), server_default="false"),
        sa.Column("rrule", sa.String(512), nullable=True),
        sa.Column("recurrence_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("meetings.id"), nullable=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crm_leads.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_meetings_odoo_id", "meetings", ["odoo_id"], unique=True)
    op.create_index("ix_meetings_start", "meetings", ["start"])
    op.create_index("ix_meetings_organizer_id", "meetings", ["organizer_id"])

    # ── meeting_attendees ─────────────────────────────────────────────────────
    op.create_table("meeting_attendees",
        sa.Column("meeting_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("state", sa.String(32), nullable=True),
        sa.Column("availability", sa.String(32), nullable=True),
    )

    # ── updated_at trigger (applied to all timestamped tables) ───────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN NEW.updated_at = now(); RETURN NEW; END;
        $$ LANGUAGE plpgsql;
    """)
    for tbl in ["partners", "users", "crm_leads", "sale_orders", "invoices", "payments", "meetings"]:
        op.execute(f"""
            CREATE TRIGGER {tbl}_updated_at
            BEFORE UPDATE ON {tbl}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """)


def downgrade() -> None:
    for tbl in ["partners", "users", "crm_leads", "sale_orders", "invoices", "payments", "meetings"]:
        op.execute(f"DROP TRIGGER IF EXISTS {tbl}_updated_at ON {tbl};")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at;")

    for tbl in [
        "meeting_attendees", "meetings", "messages", "activities", "activity_types",
        "payments", "invoice_lines", "invoices",
        "sale_order_lines", "sale_orders",
        "crm_lead_tags", "crm_leads", "crm_tags", "crm_stages",
        "pricelist_items", "product_variants", "products", "product_categories",
        "partner_partner_tags", "partners", "partner_tags",
        "sales_team_members", "sales_teams", "users",
        "pricelists", "payment_terms", "states", "countries", "currencies",
    ]:
        op.drop_table(tbl)
