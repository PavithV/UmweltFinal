import os
import psycopg2
from psycopg2.extras import execute_values

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "sensebox"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def insert_measurements(rows):
    """rows = [(timestamp, sensor_id, sensor_name, unit, value), ...]"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(cur,
                """
                INSERT INTO measurements (time, sensor_id, sensor_name, unit, value)
                VALUES %s
                ON CONFLICT DO NOTHING
                """,
                rows
            )
    print(f"Inserted {len(rows)} rows")