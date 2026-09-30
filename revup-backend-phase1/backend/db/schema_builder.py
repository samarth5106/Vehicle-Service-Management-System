import mysql.connector
from config.db_config import DB_CONFIG, DATABASE_NAME
from query_engine.create_query import build_create

TABLE_DEFINITIONS = [
    ("Customer", {
        "customer_id": "INT AUTO_INCREMENT PRIMARY KEY",
        "name": "VARCHAR(100) NOT NULL",
        "phone": "VARCHAR(15) NOT NULL",
        "email": "VARCHAR(100)",
        "address": "VARCHAR(255)"
    }, []),
    ("Vehicle", {
        "vehicle_id": "INT AUTO_INCREMENT PRIMARY KEY",
        "customer_id": "INT NOT NULL",
        "registration_no": "VARCHAR(20) NOT NULL UNIQUE",
        "make": "VARCHAR(50) NOT NULL",
        "model": "VARCHAR(50) NOT NULL",
        "manufacturing_year": "INT"
    }, [
        "FOREIGN KEY (customer_id) REFERENCES Customer(customer_id) ON DELETE RESTRICT"
    ]),
    ("Mechanic", {
        "mechanic_id": "INT AUTO_INCREMENT PRIMARY KEY",
        "name": "VARCHAR(100) NOT NULL",
        "phone": "VARCHAR(15)",
        "specialization": "VARCHAR(100)"
    }, []),
    ("ServiceRecord", {
        "service_id": "INT AUTO_INCREMENT PRIMARY KEY",
        "vehicle_id": "INT NOT NULL",
        "mechanic_id": "INT NOT NULL",
        "service_date": "DATE NOT NULL",
        "service_type": "VARCHAR(100) NOT NULL",
        "description": "TEXT",
        "labor_cost": "DECIMAL(10,2) NOT NULL DEFAULT 0",
        "status": "VARCHAR(30) NOT NULL DEFAULT 'Received'"
    }, [
        "FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id) ON DELETE RESTRICT",
        "FOREIGN KEY (mechanic_id) REFERENCES Mechanic(mechanic_id) ON DELETE RESTRICT",
        "CHECK (status IN ('Received','Diagnosing','In Progress','Waiting for Parts','Completed','Delivered'))",
        "CHECK (labor_cost >= 0)"
    ]),
    ("Parts", {
        "part_id": "INT AUTO_INCREMENT PRIMARY KEY",
        "part_name": "VARCHAR(100) NOT NULL UNIQUE",
        "quantity_in_stock": "INT NOT NULL DEFAULT 0",
        "unit_price": "DECIMAL(10,2) NOT NULL"
    }, ["CHECK (quantity_in_stock >= 0)", "CHECK (unit_price >= 0)"]),
    ("ServiceParts", {
        "service_id": "INT NOT NULL",
        "part_id": "INT NOT NULL",
        "quantity": "INT NOT NULL",
        "unit_price": "DECIMAL(10,2) NOT NULL"
    }, [
        "CHECK (quantity > 0)",
        "PRIMARY KEY (service_id, part_id)",
        "FOREIGN KEY (service_id) REFERENCES ServiceRecord(service_id) ON DELETE CASCADE",
        "FOREIGN KEY (part_id) REFERENCES Parts(part_id) ON DELETE RESTRICT"
    ]),
    ("Invoice", {
        "invoice_id": "INT AUTO_INCREMENT PRIMARY KEY",
        "service_id": "INT NOT NULL UNIQUE",
        "invoice_date": "DATE NOT NULL",
        "parts_amount": "DECIMAL(10,2) NOT NULL DEFAULT 0",
        "labor_amount": "DECIMAL(10,2) NOT NULL DEFAULT 0",
        "tax_amount": "DECIMAL(10,2) NOT NULL DEFAULT 0",
        "total_amount": "DECIMAL(10,2) NOT NULL DEFAULT 0",
        "payment_status": "VARCHAR(30) NOT NULL DEFAULT 'Unpaid'",
        "payment_date": "DATE NULL"
    }, [
        "FOREIGN KEY (service_id) REFERENCES ServiceRecord(service_id) ON DELETE RESTRICT",
        "CHECK (payment_status IN ('Unpaid','Paid'))"
    ])
]

INDEXES = [
    "CREATE INDEX idx_vehicle_customer ON Vehicle(customer_id)",
    "CREATE INDEX idx_service_vehicle ON ServiceRecord(vehicle_id)",
    "CREATE INDEX idx_service_mechanic ON ServiceRecord(mechanic_id)",
    "CREATE INDEX idx_service_date ON ServiceRecord(service_date)",
    "CREATE INDEX idx_service_status ON ServiceRecord(status)",
    "CREATE INDEX idx_invoice_date ON Invoice(invoice_date)",
]


def create_database():
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}")
    connection.commit()
    cursor.close()
    connection.close()


def create_tables():
    config = DB_CONFIG.copy()
    config["database"] = DATABASE_NAME
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    for table, columns, constraints in TABLE_DEFINITIONS:
        query = build_create(table, columns, constraints)
        print("Executing:", query)
        cursor.execute(query)

    for query in INDEXES:
        try:
            cursor.execute(query)
        except mysql.connector.Error as exc:
            if exc.errno != 1061:
                raise

    connection.commit()
    cursor.close()
    connection.close()


if __name__ == "__main__":
    create_database()
    create_tables()
    print(f"Database '{DATABASE_NAME}' and all tables/indexes are ready.")
