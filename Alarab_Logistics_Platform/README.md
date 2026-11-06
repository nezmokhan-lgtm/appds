# Alarab Road Trading W.L.L. — Logistics & Business Platform

Complete **Phase 1+** operational platform for independent logistics and business management.  
Built for Alarab Road Trading W.L.L. — does **not** depend on Madar or any external ERP.

---

## Features

| Module | Capabilities |
|--------|--------------|
| **Overview** | Live KPIs, revenue, fleet availability, recent activity feed |
| **Shipments** | Create, assign vehicle + driver, status workflow (Pending → Confirmed → In Transit → Delivered / Cancelled) |
| **Customers** | Full directory with contact & location details, search-ready |
| **Fleet** | Vehicles with type, capacity, status (Available / In Use / Maintenance) |
| **Drivers** | Driver register with license & availability status |
| **Invoices** | Sequential numbers (`INV-YYYY-0001`), status workflow, multi-currency (SAR/BHD/USD/AED) |
| **Users** | Role-based access (Admin, MD, Operations, Transport Manager, Finance Manager, Accountant, Sales Manager) |
| **Audit Log** | Full create / update / status-change trail |
| **UI** | Modern responsive dashboard, English + Arabic (RTL) toggle |

---

## Requirements

- Python 3.10+
- pip

---

## Quick start

```bash
# 1. Extract / enter the folder
cd alarab_platform

# 2. Virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install
pip install -r requirements.txt

# 4. Environment
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux

# 5. Run
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://127.0.0.1:8000**

### Demo accounts (change immediately)

| Email | Password | Role |
|-------|----------|------|
| `admin@alarab.local` | `ChangeMe123!` | Admin |
| `ops@alarab.local` | `OpsDemo123!` | Operations |
| `finance@alarab.local` | `FinanceDemo123!` | Finance Manager |

The platform seeds realistic demo customers, vehicles, drivers, shipments and invoices on first run.

---

## Architecture

- **Backend**: FastAPI + SQLAlchemy 2 + Pydantic
- **Auth**: bcrypt passwords + signed JWT in HttpOnly cookie (12 h)
- **Database**: SQLite by default (swap to PostgreSQL via `DATABASE_URL`)
- **Frontend**: Vanilla JS SPA — no build step, fully offline-capable after load
- **Roles**: Admin & MD have full access; other roles are restricted per endpoint

---

## Production checklist

Before using real company data:

1. Generate a long random `APP_SECRET` (≥ 32 chars)
2. Change every demo password
3. Switch `DATABASE_URL` to PostgreSQL
4. Enable HTTPS and set cookie `secure=True`
5. Add rate limiting, proper migrations (Alembic), backups
6. Conduct a security review
7. Do **not** expose the default admin credentials

---

## Not included (future phases)

- Live GPS / telematics / maps
- Mobile driver apps
- Freight marketplace / bidding
- Full double-entry accounting
- Country-specific e-invoicing (ZATCA, etc.)
- Payment gateways
- Government system integrations

These require provider credentials, business rules, testing and regulatory review.

---

## License & ownership

Internal platform for **Alarab Road Trading W.L.L.**  
All rights reserved.
