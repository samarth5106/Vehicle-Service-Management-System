# RevUp — Vehicle Service Management System

A full-stack web application for managing an automobile service workshop — built from scratch to learn and apply database design, backend API development, and deployment, without relying on an ORM. Every SQL query (CREATE, INSERT, SELECT, UPDATE) is generated programmatically through a custom-built Python query engine rather than using a query-builder library.

🔗 **Live App:** https://vehicle-service-management-system-one.vercel.app/
🔗 **Backend API:** https://revup-backend-vfuh.onrender.com/api

> Backend runs on Render's free tier, which sleeps after periods of inactivity — the first request after idle time may take 10–50s to respond while it spins back up.

## Why I built this

I wanted to design and implement a complete real-world workflow end-to-end — from relational schema design through to a deployed, usable application — without hiding the SQL behind an ORM. The goal was to actually understand what queries are being generated and executed at every step, and to practice full-stack deployment across separate frontend/backend/database providers.

## Architecture

```
Next.js (React/TypeScript) UI
        │
        ▼  HTTPS (REST)
Flask REST API (Python)
        │
        ▼
Custom SQL query engine (build_create / build_insert / build_select / build_update)
        │
        ▼
mysql-connector-python
        │
        ▼
MySQL (Aiven, cloud-hosted, SSL required)
```

**Deployed on:**
- Frontend → Vercel
- Backend → Render
- Database → Aiven MySQL

## Core workflow

```
Customer → Vehicle → Service Job → Mechanic → Parts Used → Invoice → Payment → Service History
```

Service jobs move through a fixed status pipeline, enforced at the database level via a `CHECK` constraint on `ServiceRecord.status` — so an invalid status transition isn't just a UI rule, it's rejected by the schema itself:

```
Received → Diagnosing → In Progress / Waiting for Parts → Completed → Delivered
```

## Database design

**Entities:** `Customer`, `Vehicle`, `Mechanic`, `ServiceRecord`, `Parts`, `ServiceParts` (junction table modeling the many-to-many relationship between a service job and the parts used in it), `Invoice`.

Relationships:
- Customer → Vehicle (1:N)
- Vehicle → ServiceRecord (1:N)
- Mechanic → ServiceRecord (1:N)
- ServiceRecord ↔ Parts (M:N, via ServiceParts)
- ServiceRecord → Invoice (1:1)

Schema is normalized to 3NF, with foreign key constraints and check constraints enforced at the DB layer.

## Local development setup

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set your local MySQL credentials:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=<your local MySQL password>
DB_PORT=3306
DB_NAME=vehicle_service_db
```
(Leave `DB_SSL_CA` unset for local MySQL — SSL is only needed for the cloud-hosted Aiven DB.)

Initialize the database and tables, then start the server:
```bash
python -m db.schema_builder
python app.py
```
API runs at `http://127.0.0.1:5000`.

### Frontend
```bash
cd vehicle-service-management-frontend
pnpm install
```

Set `NEXT_PUBLIC_API_URL` in `.env.local`:
```
NEXT_PUBLIC_API_URL=http://127.0.0.1:5000
```

```bash
pnpm dev
```
Frontend runs at `http://localhost:3000`.

## Deployment notes

**Backend (Render):**
Environment variables set in Render → Environment:
```
DB_HOST=<Aiven host>
DB_USER=avnadmin
DB_PASSWORD=<Aiven password>
DB_PORT=<Aiven port>
DB_NAME=defaultdb
DB_SSL_CA=certs/aiven-ca.pem
```
The Aiven CA certificate is committed at `backend/certs/aiven-ca.pem` (public cert, safe to commit — not a secret).

**Frontend (Vercel):**
Set in Vercel → Settings → Environment Variables (type: Config — this value is client-exposed by the `NEXT_PUBLIC_` prefix regardless):
```
NEXT_PUBLIC_API_URL=https://revup-backend-vfuh.onrender.com
```
`NEXT_PUBLIC_*` vars are baked in at build time — redeploy after changing this value for it to take effect.

**Database (Aiven MySQL):**
Requires SSL (`ssl-mode=REQUIRED`). Tables are created by running `backend/db/schema_builder.py` once, locally, with `.env` pointed at Aiven credentials.

## Tech stack

- **Frontend:** Next.js, React, TypeScript
- **Backend:** Python, Flask
- **Database:** MySQL (Aiven)
- **DB driver:** mysql-connector-python (no ORM)
- **Hosting:** Vercel (frontend), Render (backend), Aiven (database)
