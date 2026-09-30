# Quick setup

## 1. MySQL
Ensure MySQL80 is running. The schema builder creates `vehicle_service_db`, seven tables, foreign keys and indexes.

## 2. Backend
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# edit .env and put your MySQL password in DB_PASSWORD
python -m db.schema_builder
python seed_data.py
python app.py
```

## 3. Frontend
In a second terminal:
```powershell
cd vehicle-service-management-frontend
pnpm install
Copy-Item .env.local.example .env.local
pnpm dev
```
Open http://localhost:3000.

## 4. API
- GET /api/health
- GET/POST /api/customers
- GET/POST/PUT /api/vehicles
- GET/POST/PUT /api/mechanics
- GET/POST/PUT /api/services
- GET/POST/PUT /api/parts
- GET/POST/PUT /api/invoices
- GET/POST /api/service-parts
- GET /api/overview
