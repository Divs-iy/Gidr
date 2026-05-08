import sqlite3
import os

# Same absolute path logic as your database.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "gidr.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Add missing columns — IF NOT EXISTS prevents errors if you run it twice
try:
    cursor.execute("ALTER TABLE invoices ADD COLUMN original_filename TEXT")
    print("✅ Added original_filename to invoices")
except Exception as e:
    print(f"⚠️  invoices.original_filename: {e}")

try:
    cursor.execute("ALTER TABLE line_items ADD COLUMN unit TEXT")
    print("✅ Added unit to line_items")
except Exception as e:
    print(f"⚠️  line_items.unit: {e}")

conn.commit()
conn.close()
print("✅ Migration complete")