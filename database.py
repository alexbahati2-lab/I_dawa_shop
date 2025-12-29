import sqlite3
import os

DB_PATH = "data/i_dawa.db"

def get_connection():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH)

def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    return column_name in columns

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # =========================
    # Medicines table
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        strength TEXT,
        form TEXT,
        unit_type TEXT,
        units_per_pack INTEGER,
        units_in_stock INTEGER DEFAULT 0,
        expiry_date TEXT,
        buy_price REAL,
        sell_price REAL,
        sale_policy TEXT
    )
    """)

    # Safely add missing columns
    for col_name, col_type in [("batch_no", "TEXT"), ("barcode", "TEXT")]:
        if not column_exists(cursor, "medicines", col_name):
            cursor.execute(f"ALTER TABLE medicines ADD COLUMN {col_name} {col_type}")

    # =========================
    # Sales table
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_id INTEGER,
        quantity INTEGER,
        sale_type TEXT,
        total_price REAL,
        sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # =========================
    # Purchases table
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_id INTEGER,
        quantity INTEGER,
        buy_price REAL,
        supplier TEXT,
        expiry_date TEXT,
        purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
