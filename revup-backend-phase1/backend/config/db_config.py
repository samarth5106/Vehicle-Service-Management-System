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

# Add SSL CA only if one is configured (Aiven requires it; local MySQL doesn't)
_ssl_ca = os.getenv("DB_SSL_CA")
if _ssl_ca:
    DB_CONFIG["ssl_ca"] = _ssl_ca
    DB_CONFIG["ssl_verify_cert"] = True

DATABASE_NAME = os.getenv("DB_NAME", "vehicle_service_db")

TAX_RATE = 0.18
LOW_STOCK_LIMIT = 5