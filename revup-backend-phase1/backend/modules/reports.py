"""Dashboard numbers and reports. Every value is an SQL aggregate over live tables."""
from config.db_config import LOW_STOCK_LIMIT
from modules.common import jsonable, q_one, q_select, transaction

ACTIVE = ["Received", "Diagnosing", "In Progress", "Waiting for Parts"]


def dashboard():
    with transaction() as cur:
        n = lambda t, c="COUNT(*) AS n", cond=None: q_one(cur, t, c, cond)["n"]
        revenue = q_one(cur, "Invoice", "COALESCE(SUM(total_amount), 0) AS n", {"payment_status": "Paid"})["n"]
        outstanding = q_one(cur, "Invoice", "COALESCE(SUM(total_amount), 0) AS n", {"payment_status": "Unpaid"})["n"]
        data = {
            "customers": n("Customer"), "vehicles": n("Vehicle"), "mechanics": n("Mechanic"),
            "vehicles_under_service": n("ServiceRecord", "COUNT(DISTINCT vehicle_id) AS n", [("status", "IN", ACTIVE)]),
            "pending_jobs": n("ServiceRecord", cond=[("status", "IN", ["Received", "Diagnosing"])]),
            "completed_services": n("ServiceRecord", cond=[("status", "IN", ["Completed", "Delivered"])]),
            "low_stock_parts": n("Parts", cond=[("quantity_in_stock", "<=", LOW_STOCK_LIMIT)]),
            "unpaid_invoices": n("Invoice", cond={"payment_status": "Unpaid"}),
            "revenue": float(revenue), "outstanding": float(outstanding),
        }
    return data


def report(name, **arg):
    with transaction() as cur:
        if name == "services-by-status":
            rows = q_select(cur, "ServiceRecord", "status, COUNT(*) AS jobs", group_by="status", order_by="jobs DESC")
        elif name == "mechanic-workload":
            rows = q_select(cur, "Mechanic m", ["m.mechanic_id", "m.name", "m.specialization",
                            "COUNT(s.service_id) AS total_jobs",
                            "SUM(CASE WHEN s.status IN ('Received','Diagnosing','In Progress','Waiting for Parts') THEN 1 ELSE 0 END) AS active_jobs"],
                            joins=["LEFT JOIN ServiceRecord s ON s.mechanic_id = m.mechanic_id"],
                            group_by="m.mechanic_id, m.name, m.specialization", order_by="active_jobs DESC, m.name")
        elif name == "low-stock":
            rows = q_select(cur, "Parts", "*", [("quantity_in_stock", "<=", LOW_STOCK_LIMIT)], order_by="quantity_in_stock, part_name")
        elif name == "revenue-by-date":
            rows = q_select(cur, "Invoice", ["payment_date", "COUNT(*) AS invoices", "SUM(total_amount) AS revenue"],
                            {"payment_status": "Paid"}, group_by="payment_date", order_by="payment_date DESC")
        elif name == "payment-summary":
            rows = q_select(cur, "Invoice", ["payment_status", "COUNT(*) AS invoices", "SUM(total_amount) AS amount"], group_by="payment_status")
        elif name == "parts-usage":
            rows = q_select(cur, "Parts p", ["p.part_name", "p.quantity_in_stock", "COALESCE(SUM(sp.quantity), 0) AS total_used"],
                            joins=["LEFT JOIN ServiceParts sp ON sp.part_id = p.part_id"], group_by="p.part_id, p.part_name, p.quantity_in_stock",
                            order_by="total_used DESC")
        else:
            return None
        return jsonable(rows)
