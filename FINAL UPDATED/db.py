import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Update these to your new Postgres credentials
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "quality_auditor"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgre"),
    "port": os.getenv("DB_PORT", "5432")
}

def get_pg_conn():
    return psycopg2.connect(
        **DB_CONFIG,
        # sslmode='require' # Critical for Supabase!
    )

def get_pg_dict_cursor(conn):
    return conn.cursor(cursor_factory=RealDictCursor)