import sqlite3

conn = sqlite3.connect("data/chinook.db")
cur = conn.cursor()

# List every table and its row count
tables = cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()

for (name,) in tables:
    count = cur.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
    print(f"{name}: {count} rows")

# Look at the columns of one table
print("\nInvoice columns:")
for col in cur.execute('PRAGMA table_info("Invoice")').fetchall():
    print(f"  {col[1]} ({col[2]})")

conn.close()