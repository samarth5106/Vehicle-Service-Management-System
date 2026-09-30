"""End-to-end check of the whole workshop flow against the real MySQL database (uses Flask's test client)."""
import uuid
from app import app
from db.schema_builder import create_database, create_tables


def call(client, method, url, **kw):
    r = getattr(client, method)(url, **kw)
    return r.status_code, r.get_json()


def main():
    create_database(); create_tables()
    c = app.test_client(); tag = uuid.uuid4().hex[:6].upper()
    _, r = call(c, "post", "/api/customers", json={"name": "Test Owner", "phone": "9876543210", "email": "t@x.com"}); cid = r["id"]
    _, r = call(c, "post", "/api/vehicles", json={"customer_id": cid, "registration_no": f"MH31{tag}", "make": "Honda", "model": "City", "manufacturing_year": 2020}); vid = r["id"]
    _, r = call(c, "post", "/api/mechanics", json={"name": "Rohan Shah", "specialization": "Engine"}); mid = r["id"]
    _, r = call(c, "post", "/api/parts", json={"part_name": f"Oil Filter {tag}", "quantity_in_stock": 5, "unit_price": 350}); pid = r["id"]
    s, r = call(c, "post", "/api/vehicles", json={"customer_id": cid, "registration_no": f"MH31{tag}", "make": "A", "model": "B"}); assert s == 409, "duplicate reg must fail"
    s, r = call(c, "post", "/api/customers", json={"name": "", "phone": "12"}); assert s == 400 and "phone" in r["fields"]
    _, r = call(c, "post", "/api/services", json={"vehicle_id": vid, "mechanic_id": mid, "service_date": "2026-09-30", "service_type": "Full Service", "labor_cost": 2000}); sid = r["id"]
    s, _ = call(c, "post", f"/api/services/{sid}/parts", json={"part_id": pid, "quantity": 1}); assert s == 400, "no parts while Received"
    for st in ["Diagnosing", "In Progress"]:
        assert call(c, "put", f"/api/services/{sid}", json={"status": st})[0] == 200
    assert call(c, "put", f"/api/services/{sid}", json={"status": "Delivered"})[0] == 400, "cannot skip lifecycle"
    assert call(c, "post", f"/api/services/{sid}/parts", json={"part_id": pid, "quantity": 9})[0] == 400, "stock must not go negative"
    assert call(c, "post", f"/api/services/{sid}/parts", json={"part_id": pid, "quantity": 2})[0] == 201
    stock = [p for p in call(c, "get", "/api/parts")[1] if p["part_id"] == pid][0]["quantity_in_stock"]; assert stock == 3, stock
    assert call(c, "post", "/api/invoices", json={"service_id": sid})[0] == 400, "invoice only after Completed"
    call(c, "put", f"/api/services/{sid}", json={"status": "Completed"})
    s, r = call(c, "post", "/api/invoices", json={"service_id": sid}); assert s == 201; iid = r["id"]
    inv = [i for i in call(c, "get", "/api/invoices")[1] if i["invoice_id"] == iid][0]
    assert (inv["parts_amount"], inv["labor_amount"], inv["tax_amount"], inv["total_amount"]) == (700, 2000, 486, 3186), inv
    assert call(c, "post", "/api/invoices", json={"service_id": sid})[0] == 400, "one invoice per service"
    assert call(c, "put", f"/api/invoices/{iid}/payment", json={"payment_status": "Paid"})[0] == 200
    assert call(c, "put", f"/api/services/{sid}", json={"status": "Delivered"})[0] == 200
    hist = call(c, "get", f"/api/vehicles/{vid}/history")[1]; assert hist[0]["status"] == "Delivered" and hist[0]["invoice_id"] == iid
    d = call(c, "get", "/api/dashboard")[1]; assert d["revenue"] >= 3186 and d["customers"] >= 1
    for name in ["services-by-status", "mechanic-workload", "low-stock", "revenue-by-date", "payment-summary", "parts-usage"]:
        assert call(c, "get", f"/api/reports/{name}")[0] == 200, name
    print("ALL WORKFLOW CHECKS PASSED", d)


if __name__ == "__main__":
    main()
