import sqlite3
from pathlib import Path
import pandas as pd

CSV_DIR = Path("data/olist")
DB_PATH = Path("data/olist.db")

TABLES = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

DB_PATH.unlink(missing_ok=True)  # rebuild from scratch each run
conn = sqlite3.connect(DB_PATH)
for table, filename in TABLES.items():
    df = pd.read_csv(CSV_DIR / filename, encoding="utf-8-sig")
    df.to_sql(table, conn, index=False)
    print(f"{table}: {len(df):,} rows")
conn.close()