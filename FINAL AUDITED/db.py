import psycopg2
from psycopg2.extras import RealDictCursor
import os
from pinecone import Pinecone  

# Update these to your new Postgres credentials
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "****"),
    "database": os.getenv("DB_NAME", "****"),
    "user": os.getenv("DB_USER", "****"),
    "password": os.getenv("DB_PASSWORD", "****"),
    "port": os.getenv("DB_PORT", "****")
}

def get_pg_conn():
    return psycopg2.connect(
        **DB_CONFIG,
        # sslmode='require' # Critical for Supabase!
    )

def get_pg_dict_cursor(conn):
    return conn.cursor(cursor_factory=RealDictCursor)
