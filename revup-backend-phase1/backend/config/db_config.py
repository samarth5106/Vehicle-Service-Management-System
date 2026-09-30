import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "port": int(os.getenv("DB_PORT", "3306")),
}

DATABASE_NAME = os.getenv("DB_NAME", "vehicle_service_db")

TAX_RATE = 0.18          # GST on (parts + labour)
LOW_STOCK_LIMIT = 5      # parts at or below this quantity are "low stock"
