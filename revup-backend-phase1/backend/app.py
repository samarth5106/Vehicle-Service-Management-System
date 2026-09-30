from flask import Flask, jsonify, request
from flask_cors import CORS
from mysql.connector import Error, errorcode

from db.schema_builder import create_database, create_tables
from modules import crud, reports, workflow
from modules.common import ValidationError

app = Flask(__name__)
CORS(app)


@app.errorhandler(ValidationError)
def on_validation(exc):
    return jsonify({"error": str(exc), "fields": exc.fields}), 400


@app.errorhandler(Error)
def on_db_error(exc):
    if exc.errno == errorcode.ER_DUP_ENTRY:
        return jsonify({"error": "This record already exists (duplicate registration number or part name)"}), 409
    if exc.errno in (errorcode.ER_ROW_IS_REFERENCED_2, errorcode.ER_NO_REFERENCED_ROW_2):
        return jsonify({"error": "This record is linked to other records"}), 409
    if exc.errno == errorcode.ER_CHECK_CONSTRAINT_VIOLATED:
        return jsonify({"error": "Value violates a database rule (e.g. negative stock)"}), 400
    return jsonify({"error": "Database error", "detail": str(exc)}), 500


@app.get("/api/health")
def health():
    reports.dashboard()
    return jsonify({"status": "ok"})


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("JSON object expected")
    return data


for _name in crud.ENTITIES:
    def _list(n=_name):
        return jsonify(crud.list_entity(n, request.args.get("q")))
    def _create(n=_name):
        return jsonify({"message": "Saved successfully", "id": crud.create_entity(n, body())}), 201
    def _update(record_id, n=_name):
        crud.update_entity(n, record_id, body())
        return jsonify({"message": "Updated successfully"})
    app.add_url_rule(f"/api/{_name}", f"list_{_name}", _list, methods=["GET"])
    app.add_url_rule(f"/api/{_name}", f"create_{_name}", _create, methods=["POST"])
    app.add_url_rule(f"/api/{_name}/<int:record_id>", f"update_{_name}", _update, methods=["PUT"])


@app.get("/api/services")
def services():
    a = request.args
    return jsonify(workflow.list_services(a.get("q"), a.get("status"), a.get("vehicle_id", type=int), a.get("customer_id", type=int)))


@app.post("/api/services")
def service_create():
    return jsonify({"message": "Service job created", "id": workflow.create_service(body())}), 201


@app.put("/api/services/<int:service_id>")
def service_update(service_id):
    workflow.update_service(service_id, body())
    return jsonify({"message": "Service job updated"})


@app.get("/api/services/<int:service_id>/parts")
def service_parts(service_id):
    return jsonify(workflow.service_parts(service_id))


@app.post("/api/services/<int:service_id>/parts")
def service_part_add(service_id):
    workflow.add_part(service_id, body())
    return jsonify({"message": "Part added; stock updated"}), 201


@app.delete("/api/services/<int:service_id>/parts/<int:part_id>")
def service_part_remove(service_id, part_id):
    workflow.remove_part(service_id, part_id)
    return jsonify({"message": "Part removed; stock restored"})


@app.get("/api/invoices")
def invoices():
    return jsonify(workflow.list_invoices(request.args.get("q"), request.args.get("payment_status")))


@app.post("/api/invoices")
def invoice_create():
    return jsonify({"message": "Invoice generated", "id": workflow.generate_invoice(body())}), 201


@app.put("/api/invoices/<int:invoice_id>/payment")
def invoice_payment(invoice_id):
    workflow.set_payment(invoice_id, body())
    return jsonify({"message": "Payment status updated"})


@app.get("/api/vehicles/<int:vehicle_id>/history")
def vehicle_history(vehicle_id):
    return jsonify(workflow.list_services(vehicle_id=vehicle_id))


@app.get("/api/customers/<int:customer_id>/history")
def customer_history(customer_id):
    return jsonify(workflow.list_services(customer_id=customer_id))


@app.get("/api/dashboard")
def dashboard():
    return jsonify({**reports.dashboard(), "recent_services": workflow.list_services(limit=8)})


@app.get("/api/reports/<name>")
def report(name):
    data = reports.report(name)
    if data is None:
        return jsonify({"error": "Unknown report"}), 404
    return jsonify(data)


if __name__ == "__main__":
    create_database()
    create_tables()
    app.run(debug=True, port=5000)
