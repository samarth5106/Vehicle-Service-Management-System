import mysql.connector
from config.db_config import DB_CONFIG


def get_connection(database=None):
    config = DB_CONFIG.copy()
    if database:
        config["database"] = database
    return mysql.connector.connect(**config)
