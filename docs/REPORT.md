# RevUp: Vehicle Service Management System (DBMS Project Report)

## 1. Problem
An automobile service center tracks customers, vehicles, service jobs, mechanics, parts, invoices and payments manually. RevUp keeps all of this in one relational database, so staff can see the full service history of any vehicle and the day-to-day state of the workshop.

## 2. Users and workflow
Users: service center staff.
Workflow: Customer -> Vehicle -> Service Job -> Mechanic -> Parts -> Cost calculation -> Invoice -> Payment -> Service History.

Service job lifecycle: Received -> Diagnosing -> In Progress <-> Waiting for Parts -> Completed -> Delivered.
Rules enforced by the backend:
- Status can only move to an allowed next step (no skipping).
- Parts can be added only after Received and before the invoice exists; stock never goes negative.
- An invoice is generated only for a Completed job, and only once per service.
- Delivered requires an invoice.
- Labour cost and parts are locked once the invoice exists.

## 3. Relationships
| Relationship | Type |
|---|---|
| Customer - Vehicle | 1 : N |
| Vehicle - ServiceRecord | 1 : N |
| Mechanic - ServiceRecord | 1 : N |
| ServiceRecord - Parts | N : N via ServiceParts |
| ServiceRecord - Invoice | 1 : 1 (UNIQUE service_id) |

## 4. Schema
- **Customer**(customer_id PK, name, phone, email, address)
- **Vehicle**(vehicle_id PK, customer_id FK, registration_no UNIQUE, make, model, manufacturing_year)
- **Mechanic**(mechanic_id PK, name, phone, specialization)
- **ServiceRecord**(service_id PK, vehicle_id FK, mechanic_id FK, service_date, service_type, description, labor_cost, status)
- **Parts**(part_id PK, part_name UNIQUE, quantity_in_stock, unit_price)
- **ServiceParts**(service_id FK, part_id FK, quantity, unit_price; PK = (service_id, part_id))
- **Invoice**(invoice_id PK, service_id FK UNIQUE, invoice_date, parts_amount, labor_amount, tax_amount, total_amount, payment_status, payment_date)

Integrity rules: all foreign keys use `ON DELETE RESTRICT` (ServiceParts to ServiceRecord uses CASCADE); CHECK constraints for status values, `quantity_in_stock >= 0`, `quantity > 0`, `payment_status IN ('Unpaid','Paid')`. Indexes on foreign keys, service date and status.

## 5. Normalization (up to 3NF)
- 1NF: every column holds one atomic value; every table has a primary key.
- 2NF: ServiceParts has a composite key (service_id, part_id); `quantity` depends on the whole key. Every other table has a single-column key.
- 3NF: customer details live only in Customer, vehicle details only in Vehicle, and mechanic details only in Mechanic. Nothing depends on a non-key attribute (for example the customer name is not stored in ServiceRecord; it is reached by joins).
- Deliberate snapshots: `ServiceParts.unit_price` and the Invoice amounts store values as they were at the time of service. This is historical data, not redundancy to be fixed: if Parts.unit_price changes later, old invoices must not change. The Invoice amounts are computed by the backend from ServiceRecord.labor_cost and SUM(quantity * unit_price) of ServiceParts, never typed by the user.

## 6. Programmatic SQL generation (no ORM)
All SQL is built by our own functions in `backend/query_engine/`:
- `build_create(table, columns, constraints)` produces CREATE TABLE (used by `db/schema_builder.py`).
- `build_insert(table, data)` produces `INSERT ... VALUES (%s, ...)`.
- `build_select(table, columns, conditions, joins, order_by, group_by, limit, for_update)` supports `=`, `<`, `>`, `LIKE`, `IN`, OR-groups, joins, aggregates and `FOR UPDATE`.
- `build_update(table, data, conditions)` and `build_delete(table, conditions)` (both refuse to run without a WHERE).

Security: table and column names must match a whitelist regex (`query_engine/safe.py`); user values are never placed in the SQL string, only passed as `%s` parameters to mysql-connector-python, which prevents SQL injection.

## 7. Transactions and stock control
Every API request runs in one transaction (`modules/common.py: transaction()`): commit on success, rollback on any error. When a part is added to a service, the Parts row is read with `SELECT ... FOR UPDATE`, stock is checked, the ServiceParts row is written and the stock is reduced, all in the same transaction. Two users cannot both take the last item. Removing a part line returns the stock.

## 8. API
- `GET/POST /api/customers`, `PUT /api/customers/<id>`, `GET /api/customers/<id>/history`
- `GET/POST /api/vehicles`, `PUT /api/vehicles/<id>`, `GET /api/vehicles/<id>/history`
- `GET/POST /api/mechanics`, `PUT /api/mechanics/<id>`
- `GET/POST /api/parts`, `PUT /api/parts/<id>`
- `GET/POST /api/services`, `PUT /api/services/<id>` (edit or change status), `GET/POST /api/services/<id>/parts`, `DELETE /api/services/<id>/parts/<part_id>`
- `GET/POST /api/invoices` (POST takes only `service_id`), `PUT /api/invoices/<id>/payment`
- `GET /api/dashboard`, `GET /api/reports/<name>`, `GET /api/health`

## 9. Dashboard and reports
Dashboard values are SQL aggregates: total customers, vehicles and mechanics; vehicles under service; pending jobs; completed services; low-stock parts (stock <= 5); unpaid invoices; revenue (paid); outstanding amount; recent service jobs.
Reports: services by status, mechanic workload, parts inventory and usage, low-stock parts, revenue by date, paid vs unpaid invoices. Vehicle and customer service history are available through the History buttons.

## 10. Example calculation
Labour Rs 2000 + parts Rs 700 (2 x Rs 350) = Rs 2700; GST 18% = Rs 486; total Rs 3186.

## 11. Testing
`backend/test_workflow.py` runs the full flow against MySQL: customer, vehicle, mechanic, part, service job, invalid transitions rejected, stock check (cannot go negative), stock reduction, invoice calculation, duplicate invoice rejected, payment, delivery, vehicle history, dashboard and all reports.

## 12. Scope decisions
No delete buttons for customers, vehicles, services or invoices: deleting them would break service history. Settings and notifications were removed because they are outside the project scope.
