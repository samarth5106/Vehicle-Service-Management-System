"""Master-data entities: Customer, Vehicle, Mechanic, Parts (list/search/create/update)."""
from modules.common import ValidationError, clean, jsonable, q_insert, q_select, q_update, q_one, transaction

ENTITIES = {
    "customers": dict(table="Customer", pk="customer_id", order="customer_id DESC",
                      search=["name", "phone", "email"],
                      spec={"name": ("str", True), "phone": ("phone", True), "email": ("email", False), "address": ("str", False)}),
    "vehicles": dict(table="Vehicle v", base="Vehicle", pk="v.vehicle_id", order="v.vehicle_id DESC",
                     search=["v.registration_no", "v.make", "v.model", "c.name"],
                     columns=["v.vehicle_id", "v.customer_id", "c.name AS customer_name", "v.registration_no",
                              "v.make", "v.model", "v.manufacturing_year"],
                     joins=["JOIN Customer c ON v.customer_id = c.customer_id"],
                     spec={"customer_id": ("int", True), "registration_no": ("reg", True), "make": ("str", True),
                           "model": ("str", True), "manufacturing_year": ("year", False)}),
    "mechanics": dict(table="Mechanic", pk="mechanic_id", order="mechanic_id DESC", search=["name", "specialization"],
                      spec={"name": ("str", True), "phone": ("phone", False), "specialization": ("str", False)}),
    "parts": dict(table="Parts", pk="part_id", order="part_name", search=["part_name"],
                  spec={"part_name": ("str", True), "quantity_in_stock": ("int", True), "unit_price": ("money", True)}),
}


def list_entity(name, search=None):
    e = ENTITIES[name]
    cond = [("OR", [(c, "LIKE", f"%{search}%") for c in e["search"]])] if search else None
    with transaction() as cur:
        return jsonable(q_select(cur, e["table"], e.get("columns", "*"), cond, e.get("joins"), e["order"]))


def create_entity(name, data):
    e = ENTITIES[name]
    with transaction() as cur:
        _check_fk(cur, name, data)
        return q_insert(cur, e.get("base", e["table"]), clean(data, e["spec"]))


def update_entity(name, record_id, data):
    e = ENTITIES[name]
    fields = clean(data, e["spec"], partial=True)
    if not fields:
        raise ValidationError("Nothing to update")
    with transaction() as cur:
        _check_fk(cur, name, data)
        pk = e["pk"].split(".")[-1]
        if not q_one(cur, e.get("base", e["table"]), "*", {pk: record_id}):
            raise ValidationError("Record not found")
        q_update(cur, e.get("base", e["table"]), fields, {pk: record_id})
    return 1


def _check_fk(cur, name, data):
    if name == "vehicles" and data.get("customer_id") not in (None, ""):
        if not q_one(cur, "Customer", "*", {"customer_id": int(data["customer_id"])}):
            raise ValidationError("Customer does not exist", {"customer_id": "Select a registered customer"})
