import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "app.db"

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def _ensure_columns(conn: sqlite3.Connection, table: str, required_cols: dict):
    """
    required_cols = {col_name: sql_type_and_constraints}
    Adds missing columns with ALTER TABLE.
    """
    cur = conn.execute(f"PRAGMA table_info({table});")
    existing = {row[1] for row in cur.fetchall()}  # row[1] = column name

    for col, ddl in required_cols.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl};")

def init_db():
    conn = get_conn()

    # Base table (minimal constraints for easy prototype migration)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('user','admin')),
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Add new profile columns (nullable for existing rows / admin seed)
    _ensure_columns(conn, "users", {
        "first_name": "TEXT",
        "last_name": "TEXT",
        "email": "TEXT",
        "vehicle_type": "TEXT",
        "privacy_accepted": "INTEGER DEFAULT 0"
    })

    conn.commit()
    return conn
