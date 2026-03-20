# Odoo CRM → AWS Aurora API

Full-fidelity mirror of **23 Odoo models** into AWS Aurora PostgreSQL, exposed as a FastAPI REST service with complete CRUD and an orchestrated sync engine.

---

## What's imported

| # | Odoo model | Aurora table | Domain |
|---|---|---|---|
| 1 | `res.currency` | `currencies` | Lookup |
| 2 | `res.country` | `countries` | Lookup |
| 3 | `res.country.state` | `states` | Lookup |
| 4 | `account.payment.term` | `payment_terms` | Lookup |
| 5 | `product.pricelist` | `pricelists` | Lookup |
| 6 | `product.pricelist.item` | `pricelist_items` | Lookup |
| 7 | `res.users` | `users` | Users |
| 8 | `crm.team` | `sales_teams` + `sales_team_members` | Users |
| 9 | `res.partner.category` | `partner_tags` | Partners |
| 10 | `res.partner` | `partners` + `partner_partner_tags` | Partners |
| 11 | `product.category` | `product_categories` | Products |
| 12 | `product.template` | `products` | Products |
| 13 | `product.product` | `product_variants` | Products |
| 14 | `crm.stage` | `crm_stages` | CRM |
| 15 | `crm.tag` | `crm_tags` | CRM |
| 16 | `crm.lead` | `crm_leads` + `crm_lead_tags` | CRM |
| 17 | `sale.order` | `sale_orders` | Sales |
| 18 | `sale.order.line` | `sale_order_lines` | Sales |
| 19 | `account.move` | `invoices` | Accounting |
| 20 | `account.move.line` | `invoice_lines` | Accounting |
| 21 | `account.payment` | `payments` | Accounting |
| 22 | `mail.activity.type` | `activity_types` | Communication |
| 23 | `mail.activity` | `activities` | Communication |
| 24 | `mail.message` | `messages` | Communication |
| 25 | `calendar.event` | `meetings` + `meeting_attendees` | Communication |

**28 Aurora tables** total (including association tables).

---

## Project structure

```
crm-aurora-api/
├── app/
│   ├── main.py                        # FastAPI app, all routers mounted
│   ├── config.py                      # Pydantic-settings (reads .env)
│   ├── database.py                    # Async SQLAlchemy engine + session dep
│   ├── models/
│   │   ├── lookup.py                  # Currency, Country, State, PaymentTerm, Pricelist
│   │   ├── user.py                    # User, SalesTeam
│   │   ├── partner.py                 # Partner, PartnerTag
│   │   ├── product.py                 # ProductCategory, Product, ProductVariant
│   │   ├── crm.py                     # CrmStage, CrmTag, CrmLead
│   │   ├── sales.py                   # SaleOrder, SaleOrderLine
│   │   ├── accounting.py              # Invoice, InvoiceLine, Payment
│   │   └── communication.py           # ActivityType, Activity, Message, Meeting
│   ├── schemas/                       # Pydantic v2 — one file per domain
│   │   ├── lookup.py
│   │   ├── user.py
│   │   ├── partner.py                 # includes OdooPartnerImport
│   │   ├── product.py
│   │   ├── crm.py
│   │   ├── sales.py
│   │   ├── accounting.py
│   │   └── communication.py
│   ├── routers/                       # Thin HTTP layer — one file per domain
│   │   ├── lookup.py
│   │   ├── users.py
│   │   ├── partners.py
│   │   ├── products.py
│   │   ├── crm.py
│   │   ├── sales.py
│   │   ├── accounting.py
│   │   ├── communication.py
│   │   └── odoo_sync.py              # POST /api/v1/sync/odoo
│   ├── services/
│   │   ├── base.py                    # upsert_by_odoo_id, m2o, m2m helpers
│   │   ├── partner_service.py
│   │   ├── crm_service.py
│   │   ├── sales_service.py
│   │   ├── accounting_service.py
│   │   ├── communication_service.py
│   │   └── odoo_import.py            # Full orchestrator (23 models, ordered)
│   └── middleware/
│       └── auth.py                    # JWT bearer
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_initial_full_schema.py
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Quick start

```bash
# 1. Configure
cp .env.example .env          # fill in Aurora + Odoo credentials

# 2. Start locally (Postgres stands in for Aurora)
docker compose up --build

# 3. Get a dev token
curl -X POST "http://localhost:8000/dev/token?subject=me"
# → {"access_token": "eyJ...", "token_type": "bearer"}
export TOKEN="eyJ..."

# 4. Trigger a full import from Odoo (all 23 models in order)
curl -X POST "http://localhost:8000/api/v1/sync/odoo" \
  -H "Authorization: Bearer $TOKEN"

# 5. Incremental sync (records changed since midnight UTC)
curl -X POST "http://localhost:8000/api/v1/sync/odoo?incremental=true" \
  -H "Authorization: Bearer $TOKEN"

# 6. Custom incremental boundary
curl -X POST "http://localhost:8000/api/v1/sync/odoo?incremental=true&since=2024-06-01T00:00:00Z" \
  -H "Authorization: Bearer $TOKEN"
```

Swagger UI: **http://localhost:8000/docs**

---

## API endpoints (full)

### Sync
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/sync/odoo` | Full or incremental sync of all 23 Odoo models |

### Lookup
| Method | Path | Description |
|---|---|---|
| `GET/POST` | `/api/v1/lookup/currencies` | Currencies |
| `GET/POST` | `/api/v1/lookup/countries` | Countries |
| `GET/POST` | `/api/v1/lookup/states` | States |
| `GET` | `/api/v1/lookup/countries/{id}/states` | States for a country |
| `GET/POST` | `/api/v1/lookup/payment-terms` | Payment terms |
| `GET/POST` | `/api/v1/lookup/pricelists` | Pricelists |

### Users
| Method | Path | Description |
|---|---|---|
| `GET/POST` | `/api/v1/users` | Users |
| `GET/PATCH` | `/api/v1/users/{id}` | Single user |
| `GET/POST` | `/api/v1/users/teams` | Sales teams |

### Partners
| Method | Path | Description |
|---|---|---|
| `GET/POST` | `/api/v1/partners` | Partners (paginated, filterable) |
| `GET/PATCH/DELETE` | `/api/v1/partners/{id}` | Single partner |
| `POST` | `/api/v1/partners/import/bulk` | Bulk upsert from Odoo payload |
| `GET/POST` | `/api/v1/partners/tags` | Partner tags |

### Products
| Method | Path | Description |
|---|---|---|
| `GET/POST` | `/api/v1/products` | Products |
| `GET/PATCH` | `/api/v1/products/{id}` | Single product |
| `GET` | `/api/v1/products/{id}/variants` | Variants for a product |
| `GET/POST` | `/api/v1/products/categories` | Product categories |

### CRM
| Method | Path | Description |
|---|---|---|
| `GET/POST` | `/api/v1/crm/leads` | Leads & opportunities |
| `GET/PATCH/DELETE` | `/api/v1/crm/leads/{id}` | Single lead |
| `POST` | `/api/v1/crm/leads/import/bulk` | Bulk upsert |
| `GET/POST` | `/api/v1/crm/stages` | Pipeline stages |
| `GET/POST` | `/api/v1/crm/tags` | CRM tags |

### Sales
| Method | Path | Description |
|---|---|---|
| `GET/POST` | `/api/v1/sales/orders` | Sale orders |
| `GET/PATCH/DELETE` | `/api/v1/sales/orders/{id}` | Single order (with lines) |
| `POST` | `/api/v1/sales/orders/import/bulk` | Bulk upsert |

### Accounting
| Method | Path | Description |
|---|---|---|
| `GET/POST` | `/api/v1/accounting/invoices` | Invoices, bills, credit notes |
| `GET/PATCH` | `/api/v1/accounting/invoices/{id}` | Single invoice (with lines) |
| `POST` | `/api/v1/accounting/invoices/import/bulk` | Bulk upsert |
| `GET/POST` | `/api/v1/accounting/payments` | Payments |
| `GET/PATCH` | `/api/v1/accounting/payments/{id}` | Single payment |
| `POST` | `/api/v1/accounting/payments/import/bulk` | Bulk upsert |

### Communication
| Method | Path | Description |
|---|---|---|
| `GET/POST` | `/api/v1/communication/activities` | Activities |
| `PATCH/DELETE` | `/api/v1/communication/activities/{id}` | Single activity |
| `GET/POST` | `/api/v1/communication/messages` | Chatter messages |
| `GET/POST` | `/api/v1/communication/meetings` | Calendar events |
| `GET/PATCH/DELETE` | `/api/v1/communication/meetings/{id}` | Single meeting |

---

## Import order & FK dependency resolution

The orchestrator in `odoo_import.py` runs 23 steps in strict FK order. Each step resolves foreign keys by querying for the local UUID/int PK using the `odoo_id` stored in the prior step. Failures in one step are logged and skipped — the remaining steps continue.

```
currencies → countries → states → payment_terms → pricelists
→ users → sales_teams → partner_tags → partners
→ product_categories → products → product_variants → pricelist_items
→ crm_stages → crm_tags → crm_leads
→ sale_orders → invoices → payments
→ activity_types → activities → messages → meetings
```

---

## Environment variables

| Variable | Description |
|---|---|
| `AURORA_HOST` | Aurora cluster endpoint |
| `AURORA_PORT` | Port (default 5432) |
| `AURORA_DB` | Database name |
| `AURORA_USER` | DB username |
| `AURORA_PASSWORD` | DB password |
| `SECRET_KEY` | JWT signing secret |
| `ALGORITHM` | JWT algorithm (default `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL (default 60) |
| `ODOO_URL` | Odoo base URL |
| `ODOO_DB` | Odoo database name |
| `ODOO_USER` | Odoo login |
| `ODOO_PASSWORD` | Odoo password / API key |
| `APP_ENV` | `development` or `production` |
| `LOG_LEVEL` | Python log level |

---

## Aurora setup

```sql
CREATE DATABASE odoo_crm;
CREATE USER crm_user WITH PASSWORD 'strong-password';
GRANT ALL PRIVILEGES ON DATABASE odoo_crm TO crm_user;
```

Then run migrations:

```bash
alembic upgrade head
```

---

## Production checklist

- [ ] Set `APP_ENV=production` (disables `/dev/token` and open CORS)
- [ ] Replace symmetric JWT with **AWS Cognito** or your IdP
- [ ] Use **IAM DB Auth** for Aurora instead of username/password
- [ ] Store secrets in **AWS Secrets Manager** (not `.env`)
- [ ] Enable Aurora **encryption at rest** and **TLS**
- [ ] Schedule incremental sync via **EventBridge** + Lambda or a cron job
- [ ] Add rate limiting (`slowapi`) and request size limits
- [ ] Set up **CloudWatch** log forwarding from the ECS task
