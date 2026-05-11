# import sqlite3
# import os

# # Same absolute path logic as your database.py
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DB_PATH = os.path.join(BASE_DIR, "gidr.db")

# conn = sqlite3.connect(DB_PATH)
# cursor = conn.cursor()

# # Add missing columns — IF NOT EXISTS prevents errors if you run it twice
# try:
#     cursor.execute("ALTER TABLE invoices ADD COLUMN original_filename TEXT")
#     print("✅ Added original_filename to invoices")
# except Exception as e:
#     print(f"⚠️  invoices.original_filename: {e}")

# try:
#     cursor.execute("ALTER TABLE line_items ADD COLUMN unit TEXT")
#     print("✅ Added unit to line_items")
# except Exception as e:
#     print(f"⚠️  line_items.unit: {e}")

# try:
#     cursor.execute("ALTER TABLE invoices ADD COLUMN terms_and_conditions TEXT")
#     print("✅ Added terms_and_conditions")
# except Exception as e:
#     print(f"⚠️ {e}")

# cursor.execute("""
#     CREATE TABLE IF NOT EXISTS audit_reports (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         user_id INTEGER NOT NULL,
#         quote_filename TEXT,
#         invoice_filename TEXT,
#         created_at DATETIME DEFAULT CURRENT_TIMESTAMP
#     )
# """)
# cursor.execute("""
#     CREATE TABLE IF NOT EXISTS audit_items (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         report_id INTEGER REFERENCES audit_reports(id),
#         description TEXT,
#         quoted_price REAL,
#         invoiced_price REAL,
#         status TEXT,
#         reason TEXT,
#         action TEXT,
#         comment TEXT
#     )
# """)
# conn.commit()
# conn.close()
# print("✅ Audit tables created")

# conn.commit()
# conn.close()
# print("✅ Migration complete")

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "gidr.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Enable foreign keys
cursor.execute("PRAGMA foreign_keys = ON")

def safe_add_column(query, success_msg):
    try:
        cursor.execute(query)
        print(f"✅ {success_msg}")
    except sqlite3.OperationalError as e:
        print(f"⚠️ {e}")

# Add columns
safe_add_column(
    "ALTER TABLE invoices ADD COLUMN original_filename TEXT",
    "Added original_filename to invoices"
)

safe_add_column(
    "ALTER TABLE line_items ADD COLUMN unit TEXT",
    "Added unit to line_items"
)

safe_add_column(
    "ALTER TABLE invoices ADD COLUMN terms_and_conditions TEXT",
    "Added terms_and_conditions to invoices"
)

# Create audit_reports
cursor.execute("""
CREATE TABLE IF NOT EXISTS audit_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    quote_filename TEXT,
    invoice_filename TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Create audit_items
cursor.execute("""
CREATE TABLE IF NOT EXISTS audit_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER,
    description TEXT,
    quoted_price REAL,
    invoiced_price REAL,
    status TEXT,
    reason TEXT,
    action TEXT,
    comment TEXT,
    FOREIGN KEY(report_id) REFERENCES audit_reports(id)
)
""")

conn.commit()
conn.close()

print("✅ Migration complete")