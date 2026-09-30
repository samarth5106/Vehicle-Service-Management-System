# RevUp - Vehicle Service Management System

Software for an automobile service center: customers, vehicles, service jobs, mechanics, parts, invoices and payments in one place.

Workflow: Customer -> Vehicle -> Service Job -> Mechanic -> Parts -> Invoice -> Payment -> Service History

Stack: Next.js (UI) -> Flask REST API -> own SQL query engine (build_create / build_insert / build_select / build_update / build_delete) -> mysql-connector-python -> MySQL. No ORM.

## Run
Backend (in `backend/`): create `.env` from `.env.example`, then
`python -m venv venv`, `.\venv\Scripts\Activate.ps1`, `pip install -r requirements.txt`, `python test_workflow.py` (optional check), `python app.py`

Frontend (in `vehicle-service-management-frontend/`): `pnpm install` (or `npm install`), `pnpm dev`, open http://localhost:3000

`test_workflow.py` leaves test rows behind. Drop the database (`DROP DATABASE vehicle_service_db`) before entering real data.
