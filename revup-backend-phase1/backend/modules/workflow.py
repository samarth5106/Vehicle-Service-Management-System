"""Service job lifecycle: job creation, status changes, parts consumption, invoicing, payment."""
from datetime import date

from config.db_config import TAX_RATE
from modules.common import ValidationError, clean, jsonable, q_delete, q_insert, q_one, q_select, q_update, transaction

STATUSES = ["Received", "Diagnosing", "In Progress", "Waiting for Parts", "Completed", "Delivered"]
NEXT = {"Received": ["Diagnosing"], "Diagnosing": ["In Progress", "Waiting for Parts"],
        "In Progress": ["Waiting for Parts", "Completed"], "Waiting for Parts": ["In Progress"],
        "Completed": ["Delivered"], "Delivered": []}

SERVICE_COLS = ["s.service_id", "s.vehicle_id", "v.registration_no", "v.make", "v.model", "c.customer_id",
                "c.name AS customer_name", "s.mechanic_id", "m.name AS mechanic_name", "s.service_date",
                "s.service_type", "s.description", "s.labor_cost", "s.status", "i.invoice_id"]
SERVICE_JOINS = ["JOIN Vehicle v ON s.vehicle_id = v.vehicle_id", "JOIN Customer c ON v.customer_id = c.customer_id",
                 "JOIN Mechanic m ON s.mechanic_id = m.mechanic_id", "LEFT JOIN Invoice i ON i.service_id = s.service_id"]
SPEC = {"vehicle_id": ("int", True), "mechanic_id": ("int", True), "service_date": ("date", True),
        "service_type": ("str", True), "description": ("str", False), "labor_cost": ("money", False)}


def list_services(search=None, status=None, vehicle_id=None, customer_id=None, limit=None):
    cond = []
    if search:
        cond.append(("OR", [(c, "LIKE", f"%{search}%") for c in ("v.registration_no", "c.name", "s.service_type", "m.name")]))
    if status: cond.append(("s.status", "=", status))
    if vehicle_id: cond.append(("s.vehicle_id", "=", vehicle_id))
    if customer_id: cond.append(("c.customer_id", "=", customer_id))
    with transaction() as cur:
        return jsonable(q_select(cur, "ServiceRecord s", SERVICE_COLS, cond, SERVICE_JOINS,
                                 "s.service_date DESC, s.service_id DESC", limit=limit))


def _service(cur, service_id, lock=False):
    s = q_one(cur, "ServiceRecord", "*", {"service_id": service_id}, for_update=lock)
    if not s:
        raise ValidationError("Service job not found")
    return s


def _invoice_of(cur, service_id):
    return q_one(cur, "Invoice", "*", {"service_id": service_id})


def create_service(data):
    f = clean(data, SPEC)
    f["status"] = "Received"
    f.setdefault("labor_cost", 0)
    with transaction() as cur:
        if not q_one(cur, "Vehicle", "*", {"vehicle_id": f["vehicle_id"]}):
            raise ValidationError("Vehicle does not exist", {"vehicle_id": "Select a registered vehicle"})
        if not q_one(cur, "Mechanic", "*", {"mechanic_id": f["mechanic_id"]}):
            raise ValidationError("Mechanic does not exist", {"mechanic_id": "Select a mechanic"})
        return q_insert(cur, "ServiceRecord", f)


def update_service(service_id, data):
    """Edit job details, reassign mechanic, or move status one step along the lifecycle."""
    f = clean(data, {**SPEC, "status": ("str", False)}, partial=True)
    f.pop("vehicle_id", None)
    with transaction() as cur:
        s = _service(cur, service_id, lock=True)
        if "status" in f and f["status"] != s["status"]:
            new = f["status"]
            if new not in NEXT[s["status"]]:
                raise ValidationError(f"Cannot move from {s['status']} to {new}. Allowed: {', '.join(NEXT[s['status']]) or 'none'}", {"status": "Invalid status change"})
            if new == "Delivered" and not _invoice_of(cur, service_id):
                raise ValidationError("Generate the invoice before delivering the vehicle", {"status": "Invoice missing"})
        else:
            f.pop("status", None)
        if "labor_cost" in f and _invoice_of(cur, service_id):
            raise ValidationError("Labour cost is locked once the invoice is generated", {"labor_cost": "Locked"})
        if "mechanic_id" in f and not q_one(cur, "Mechanic", "*", {"mechanic_id": f["mechanic_id"]}):
            raise ValidationError("Mechanic does not exist", {"mechanic_id": "Select a mechanic"})
        return q_update(cur, "ServiceRecord", f, {"service_id": service_id}) if f else 0


def service_parts(service_id):
    with transaction() as cur:
        return jsonable(q_select(cur, "ServiceParts sp", ["sp.service_id", "sp.part_id", "p.part_name", "sp.quantity",
                         "sp.unit_price", "(sp.quantity * sp.unit_price) AS line_total"],
                         {"sp.service_id": service_id}, ["JOIN Parts p ON sp.part_id = p.part_id"], "p.part_name"))


def add_part(service_id, data):
    f = clean(data, {"part_id": ("int", True), "quantity": ("int", True)})
    if f["quantity"] < 1:
        raise ValidationError("Quantity must be at least 1", {"quantity": "Minimum 1"})
    with transaction() as cur:
        s = _service(cur, service_id, lock=True)
        if _invoice_of(cur, service_id):
            raise ValidationError("Invoice already generated; parts can no longer be changed")
        if s["status"] in ("Received", "Delivered"):
            raise ValidationError(f"Parts cannot be added while the job is '{s['status']}'")
        part = q_one(cur, "Parts", "*", {"part_id": f["part_id"]}, for_update=True)
        if not part:
            raise ValidationError("Part does not exist", {"part_id": "Select a part"})
        if part["quantity_in_stock"] < f["quantity"]:
            raise ValidationError(f"Only {part['quantity_in_stock']} of {part['part_name']} in stock", {"quantity": "Insufficient stock"})
        q_update(cur, "Parts", {"quantity_in_stock": part["quantity_in_stock"] - f["quantity"]}, {"part_id": part["part_id"]})
        used = q_one(cur, "ServiceParts", "*", {"service_id": service_id, "part_id": part["part_id"]})
        if used:
            q_update(cur, "ServiceParts", {"quantity": used["quantity"] + f["quantity"]}, {"service_id": service_id, "part_id": part["part_id"]})
        else:
            q_insert(cur, "ServiceParts", {"service_id": service_id, "part_id": part["part_id"], "quantity": f["quantity"], "unit_price": part["unit_price"]})


def remove_part(service_id, part_id):
    """Undo a part line (wrong entry): stock is returned, only before invoicing."""
    with transaction() as cur:
        _service(cur, service_id, lock=True)
        if _invoice_of(cur, service_id):
            raise ValidationError("Invoice already generated; parts can no longer be changed")
        used = q_one(cur, "ServiceParts", "*", {"service_id": service_id, "part_id": part_id})
        if not used:
            raise ValidationError("Part not used in this service")
        part = q_one(cur, "Parts", "*", {"part_id": part_id}, for_update=True)
        q_update(cur, "Parts", {"quantity_in_stock": part["quantity_in_stock"] + used["quantity"]}, {"part_id": part_id})
        q_delete(cur, "ServiceParts", {"service_id": service_id, "part_id": part_id})


INVOICE_COLS = ["i.invoice_id", "i.service_id", "i.invoice_date", "i.parts_amount", "i.labor_amount", "i.tax_amount",
                "i.total_amount", "i.payment_status", "i.payment_date", "v.registration_no", "c.name AS customer_name", "s.service_type"]
INVOICE_JOINS = ["JOIN ServiceRecord s ON i.service_id = s.service_id", "JOIN Vehicle v ON s.vehicle_id = v.vehicle_id",
                 "JOIN Customer c ON v.customer_id = c.customer_id"]


def list_invoices(search=None, payment_status=None):
    cond = []
    if search:
        cond.append(("OR", [(c, "LIKE", f"%{search}%") for c in ("v.registration_no", "c.name", "s.service_type")]))
    if payment_status: cond.append(("i.payment_status", "=", payment_status))
    with transaction() as cur:
        return jsonable(q_select(cur, "Invoice i", INVOICE_COLS, cond, INVOICE_JOINS, "i.invoice_id DESC"))


def generate_invoice(data):
    """Amounts are computed from ServiceRecord.labor_cost and SUM(ServiceParts), never typed in."""
    sid = clean(data, {"service_id": ("int", True)})["service_id"]
    with transaction() as cur:
        s = _service(cur, sid, lock=True)
        if s["status"] not in ("Completed", "Delivered"):
            raise ValidationError("Invoice can be generated only after the service is Completed", {"service_id": "Job not completed"})
        if _invoice_of(cur, sid):
            raise ValidationError("An invoice already exists for this service", {"service_id": "Duplicate invoice"})
        row = q_one(cur, "ServiceParts", "COALESCE(SUM(quantity * unit_price), 0) AS parts_total", {"service_id": sid})
        parts, labor = round(float(row["parts_total"]), 2), round(float(s["labor_cost"]), 2)
        tax = round((parts + labor) * TAX_RATE, 2)
        return q_insert(cur, "Invoice", {"service_id": sid, "invoice_date": date.today().isoformat(), "parts_amount": parts,
                                         "labor_amount": labor, "tax_amount": tax, "total_amount": round(parts + labor + tax, 2),
                                         "payment_status": "Unpaid"})


def set_payment(invoice_id, data):
    status = clean(data, {"payment_status": ("str", True)})["payment_status"]
    if status not in ("Paid", "Unpaid"):
        raise ValidationError("Payment status must be Paid or Unpaid", {"payment_status": "Invalid"})
    with transaction() as cur:
        if not q_one(cur, "Invoice", "*", {"invoice_id": invoice_id}, for_update=True):
            raise ValidationError("Invoice not found")
        return q_update(cur, "Invoice", {"payment_status": status, "payment_date": date.today().isoformat() if status == "Paid" else None},
                        {"invoice_id": invoice_id})
