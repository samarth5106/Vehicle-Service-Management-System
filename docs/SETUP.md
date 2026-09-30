# RevUp Setup Guide

## Requirements
Windows 11, MySQL Server 8.0 (service `MySQL80`), Python 3.10+, Node.js with pnpm (or npm).

## 1. Database
Make sure the MySQL service is running: `Get-Service MySQL80` (start with `net start MySQL80` in an Admin terminal).
Confirm login works: `mysql -u root -p` should show the `mysql>` prompt. The database and all tables are created automatically by the backend on first start.

## 2. Backend (`backend/`)
1. Copy `.env.example` to `.env` and set `DB_PASSWORD` to your MySQL root password. Never commit `.env`.
2. `python -m venv venv`
3. `.\venv\Scripts\Activate.ps1`
4. `pip install -r requirements.txt`
5. Optional check: `python test_workflow.py` (runs the full workshop flow; last line must be `ALL WORKFLOW CHECKS PASSED`).
6. `python app.py` (API on http://127.0.0.1:5000)

## 3. Frontend (`vehicle-service-management-frontend/`)
1. `pnpm install` (or `npm install`)
2. `pnpm dev` (or `npm run dev`), then open http://localhost:3000
3. Optional: `.env.local` with `NEXT_PUBLIC_API_URL=http://127.0.0.1:5000`

## 4. Reset to a clean database
`test_workflow.py` leaves test rows. Before a demo:
`mysql -u root -p -e "DROP DATABASE IF EXISTS vehicle_service_db"` then restart `python app.py`.

## Troubleshooting
- "Cannot reach the server" in the UI: backend is not running on port 5000.
- `Access denied for user 'root'`: wrong `DB_PASSWORD` in `.env`.
- Old tables missing new rules (CHECK constraints, `payment_date`): drop the database (step 4) so tables are recreated.
