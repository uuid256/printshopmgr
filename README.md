# Print Shop Manager

ระบบบริหารจัดการร้านพิมพ์สำหรับร้านพิมพ์ไทย
Job management system for Thai print shops.

## Features

- **Job workflow** — full status lifecycle: pending → designing → awaiting approval → printing → ready → completed
- **Customer management** — walk-in, regular, and corporate customers with tax ID support
- **Payment collection** — cash, PromptPay QR, bank transfer; deposit and full payment tracking
- **Document generation** — quotations, tax invoices, receipts, credit notes (WeasyPrint PDF, Thai Buddhist Era dates)
- **Owner dashboard** — monthly revenue, pipeline summary, overdue alerts
- **Production queue** — operator view for print/cut/laminate stages
- **Role-based access** — owner, counter staff, designer, operator, accountant

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.x, Python 3.13 |
| Database | PostgreSQL 16 |
| Frontend | Django Templates, HTMX, Alpine.js, Tailwind CSS |
| PDF | WeasyPrint |
| Async (Phase 2) | Celery + Redis |
| Package manager | uv |
| Dev environment | Docker Compose |

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Setup

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd printshopmgr

# 2. Create your .env file
cp .env.example .env
# Edit .env and set a SECRET_KEY:
#   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 3. Build and start services
docker compose up -d

# 4. Run migrations and load initial reference data
docker compose exec web uv run python manage.py migrate
docker compose exec web uv run python manage.py loaddata fixtures/initial_data.json

# 5. Create a superuser (owner account)
docker compose exec web uv run python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin', 'admin@example.com', 'changeme123')
"

# 6. (Optional) Load demo data to explore the UI
docker compose exec web uv run python manage.py create_demo_data
```

Open http://localhost:8000 — log in with `admin` / `changeme123`.

### Daily Development

```bash
docker compose up                          # Start all services (web + db + redis)
docker compose down                        # Stop

# Django management
docker compose exec web uv run python manage.py makemigrations
docker compose exec web uv run python manage.py migrate
docker compose exec web uv run python manage.py shell

# Tests
docker compose exec web uv run pytest
docker compose exec web uv run pytest --cov

# Linting
docker compose exec web uv run ruff check .
docker compose exec web uv run ruff format .

# Add a Python package
uv add <package-name>
docker compose build web                   # Rebuild image with new dep
```

### Reset demo data

```bash
docker compose exec web uv run python manage.py create_demo_data --reset
```

## Project Structure

```
printshopmgr/
├── config/              # settings.py, urls.py, wsgi.py, celery.py
├── accounts/            # Custom User model, roles (RBAC), TailwindFormMixin
├── customers/           # Customer, CustomerType; autocomplete endpoint
├── jobs/                # Job, JobStatusHistory, status workflow
├── payments/            # Payment, BankAccount, PromptPay QR
├── documents/           # Document (sequential Thai tax numbering), PDF views
├── production/          # ProductType, Material, auto-pricing engine
├── dashboard/           # Owner dashboard, Thai template filters
├── public/              # Customer tracking page (no login, UUID URL)
├── notifications/       # Phase 2: LINE messaging
├── fixtures/            # initial_data.json — product types, customer types, bank accounts
└── templates/           # All Django templates (HTMX partials in */partials/)
```

## User Roles

| Role | Access |
|---|---|
| `owner` | Everything, including dashboard and reports |
| `counter_staff` | Create jobs, receive payments, issue documents |
| `designer` | Design queue, file uploads, submit for approval |
| `operator` | Production queue, status updates (print/cut/laminate) |
| `accountant` | Payments, documents, aging report |

Demo accounts (created by `create_demo_data`): `owner`, `counter1`, `designer1`, `operator1` — all with password `demo1234`.

## Environment Variables

See `.env.example` for all variables. Key ones:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key — generate a fresh one per environment |
| `DATABASE_URL` | PostgreSQL connection string |
| `DEBUG` | `True` for dev, `False` in production |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames |

## Document Numbering

Thai tax law requires gap-free sequential document numbers. Each type has its own prefix and sequence, implemented with `SELECT FOR UPDATE` to prevent race conditions under concurrent writes:

- `QT-YYYY-NNNNN` — Quotation (ใบเสนอราคา)
- `IV-YYYY-NNNNN` — Tax Invoice (ใบกำกับภาษี)
- `RC-YYYY-NNNNN` — Receipt (ใบเสร็จรับเงิน)
- `CN-YYYY-NNNNN` — Credit Note (ใบลดหนี้)

## Roadmap

- **Phase 1** ✅ Core operations: customers, jobs, payments, documents, dashboard
- **Phase 2** Designer Kanban board, file uploads, customer public tracking page, LINE notifications
- **Phase 3** Full VAT compliance, aging report, withholding tax (WHT) tracking
- **Phase 4** Celery automation: payment reminders, daily summaries, accounting export
