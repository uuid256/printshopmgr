# Print Shop Manager

ระบบบริหารจัดการร้านพิมพ์สำหรับร้านพิมพ์ไทย
Job management system for Thai print shops.

## Features

### Core Operations
- **Job workflow** — 12-status lifecycle: pending → designing → awaiting approval → revision → approved → printing → cutting → laminating → ready → completed
- **Customer management** — walk-in, regular, and corporate customers with tax ID support; live autocomplete search
- **Payment collection** — cash, PromptPay QR, bank transfer; deposit and full payment tracking; WHT (withholding tax) recording
- **Document generation** — quotations, tax invoices, receipts, credit notes (WeasyPrint PDF, Thai Buddhist Era dates, baht text)
- **Owner dashboard** — monthly revenue, 30-day pipeline summary, overdue alerts
- **Production queue** — operator view for print/cut/laminate stages
- **Role-based access** — owner, counter staff, designer, operator, accountant

### Design & Approval
- **File uploads** — customer artwork, design proofs (versioned), reference files, output files
- **Designer Kanban** — drag-and-drop at `/jobs/kanban/` (Sortable.js)
- **Public tracking page** — customer views status timeline + approves/requests revision via unique UUID URL (no login required)

### Financial Reports
- **Aging report** — outstanding payments bucketed by 1-30/31-60/61-90/90+ days
- **VAT report** — monthly output tax report (ภ.พ.30 compatible)

### Notifications & Automation
- **LINE customer notifications** — status change + proof-ready push messages via LINE Messaging API
- **Celery Beat tasks** — scheduled daily at 08:00-10:00 (Asia/Bangkok):
  - Daily summary → owner LINE + email
  - Payment reminders → customers with overdue balance
  - Low-stock material alerts → owner (debounced 24 h)
  - Approval reminders → customers stuck in awaiting-approval
- **Notification settings page** — owner kill-switches for email/LINE; test-email button; LINE Login for staff
- **LINE Login OAuth** — staff connect personal LINE account for owner notifications

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.x, Python 3.13 |
| Database | PostgreSQL 16 |
| Frontend | Django Templates, HTMX, Alpine.js, Tailwind CSS (CDN) |
| PDF | WeasyPrint + fonts-noto-core |
| Task queue | Celery 5.x + Redis 7 + django-celery-beat |
| Package manager | uv |
| Dev environment | Docker Compose (5 services) |

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — the only required tool

### First run

```bash
git clone <repo-url>
cd printshopmgr
make dev
```

That's it. `make dev` will:
1. Copy `.env.example` → `.env` (skipped if `.env` already exists)
2. Build the Docker image
3. Start all 5 services (web, db, redis, celery, celery-beat)
4. Run all migrations automatically
5. Load initial reference data (product types, customer types, bank accounts)
6. Create a default superuser if none exists

Open **http://localhost:8000** and log in:

| Username | Password |
|---|---|
| `admin` | `admin` |

> **Change the password immediately** after first login in production.

### Optional: load demo data

```bash
make demo
```

Adds sample customers, jobs, and payments so you can explore the UI right away.
Demo accounts: `owner`, `counter1`, `designer1`, `operator1` — all with password `demo1234`.

---

### Makefile reference

| Command | What it does |
|---|---|
| `make dev` | Build + start all services (runs migrations automatically) |
| `make test` | Run the full test suite inside the container |
| `make shell` | Open a Django shell |
| `make logs` | Tail web server logs |
| `make demo` | Load demo data (run once after `make dev`) |

---

### Daily Development

```bash
docker compose up -d                       # Start all 5 services (migrations run on web startup)
docker compose down                        # Stop all services
docker compose down -v                     # Stop and wipe all data volumes (full reset)

# Django management
docker compose exec web uv run python manage.py makemigrations
docker compose exec web uv run python manage.py migrate
docker compose exec web uv run python manage.py shell  # or: make shell

# Tests
make test                                  # Run full suite
docker compose exec web uv run pytest --cov

# Linting / formatting
docker compose exec web uv run ruff check .
docker compose exec web uv run ruff format .

# Add a Python package
uv add <package-name>
docker compose build web                   # Rebuild image with new dep

# Reset everything to a clean state
docker compose down -v && make dev
```

---

## Project Structure

```
printshopmgr/
├── config/              # settings.py, urls.py, wsgi.py, celery.py
├── accounts/            # Custom User (RBAC roles, LINE Login OAuth, TailwindFormMixin)
├── customers/           # Customer, CustomerType; autocomplete endpoint
├── jobs/                # Job, JobStatusHistory, JobFile, JobApproval; status workflow
├── payments/            # Payment, BankAccount, PromptPay QR, WHT
├── documents/           # Document (sequential Thai tax numbering), PDF views, Setting k/v store
│                        #   ↳ also hosts aging report + VAT report
├── production/          # ProductType, Material (low-stock tracking), MaterialUsage
├── dashboard/           # Owner dashboard, thai_filters templatetags
├── public/              # Customer tracking page (no login, UUID URL)
├── notifications/       # LINE webhook, scheduled Celery tasks, notification settings
├── fixtures/            # initial_data.json — product types, customer types, bank accounts
└── templates/           # All Django templates (HTMX partials in */partials/)
```

---

## User Roles

| Role | Access |
|---|---|
| `owner` | Everything, including dashboard, reports, notification settings |
| `counter_staff` | Create jobs, receive payments, issue documents |
| `designer` | Design queue/Kanban, file uploads, submit for approval |
| `operator` | Production queue, status updates (print/cut/laminate) |
| `accountant` | Payments, documents, aging report, VAT report |

---

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | dev key in `.env.example` | Django secret key — **generate a fresh one for production** |
| `DATABASE_URL` | postgres://…@db/… | PostgreSQL connection string |
| `DEBUG` | `False` | Set `True` for local development |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hostnames |
| `REDIS_URL` | `redis://redis:6379/0` | Celery broker + result backend |
| `BASE_URL` | `http://localhost:8000` | Absolute base URL used in LINE tracking links |
| `LINE_CHANNEL_ACCESS_TOKEN` | — | LINE Messaging API (customer notifications) |
| `LINE_CHANNEL_SECRET` | — | LINE Messaging API webhook verification |
| `LINE_LOGIN_CHANNEL_ID` | — | LINE Login OAuth — staff LINE account connect |
| `LINE_LOGIN_CHANNEL_SECRET` | — | LINE Login OAuth — staff LINE account connect |
| `EMAIL_BACKEND` | console backend | `django.core.mail.backends.smtp.EmailBackend` for real email |
| `EMAIL_HOST` | — | SMTP server hostname |
| `EMAIL_PORT` | `587` | SMTP port |
| `EMAIL_HOST_USER` | — | SMTP username |
| `EMAIL_HOST_PASSWORD` | — | SMTP password |
| `DEFAULT_FROM_EMAIL` | `noreply@printshop.local` | From address for outgoing email |

---

## Document Numbering

Thai tax law requires gap-free sequential document numbers. Each type has its own prefix and sequence, implemented with `SELECT FOR UPDATE` inside `transaction.atomic()`:

- `QT-YYYY-NNNNN` — Quotation (ใบเสนอราคา)
- `IV-YYYY-NNNNN` — Tax Invoice (ใบกำกับภาษี)
- `RC-YYYY-NNNNN` — Receipt (ใบเสร็จรับเงิน)
- `CN-YYYY-NNNNN` — Credit Note (ใบลดหนี้)

---

## Scheduled Tasks (Celery Beat)

All tasks check `notification_email_enabled` / `notification_line_enabled` Setting keys before sending. Schedule is in Asia/Bangkok timezone and stored in the DB (editable via Django Admin → Periodic Tasks).

| Task | Schedule | What it does |
|---|---|---|
| `send_daily_summary` | 08:00 daily | Job pipeline counts + overdue payments → owner LINE + email |
| `send_payment_reminders` | 09:00 daily | LINE push to customers with balance due past `payment_reminder_days` |
| `send_material_alerts` | 09:05 daily | Low-stock materials → owner LINE + email (debounced 24 h) |
| `send_approval_reminders` | 10:00 daily | LINE push to customers awaiting approval > `approval_reminder_days` |

Configure thresholds and kill switches at `/notifications/settings/` (owner only).

Trigger manually:
```bash
docker compose exec web uv run celery -A config call notifications.tasks.send_daily_summary
```

---

## Roadmap

- **Phase 1** ✅ Core operations: customers, jobs, payments, documents, dashboard
- **Phase 2** ✅ File uploads, Designer Kanban, public tracking page, LINE notifications
- **Phase 3** ✅ Full tax invoice (Thai compliant), aging report, VAT report (ภ.พ.30)
- **Phase 4** ✅ Celery Beat automation, scheduled notifications, LINE Login for staff, notification settings page
