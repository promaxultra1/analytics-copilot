import sqlite3

conn = sqlite3.connect("data/olist.db")

def show(label, query):
    print(f"\n--- {label} ---")
    for row in conn.execute(query).fetchall()[:10]:
        print(row)

show("orders columns", "SELECT * FROM orders LIMIT 2")
show("order status values", """
    SELECT order_status, COUNT(*) FROM orders
    GROUP BY order_status ORDER BY COUNT(*) DESC
""")
show("missing delivery dates", """
    SELECT COUNT(*) AS total,
           SUM(CASE WHEN order_delivered_customer_date IS NULL THEN 1 ELSE 0 END) AS no_delivery_date
    FROM orders
""")
show("customer keys", "SELECT * FROM customers LIMIT 3")
show("orders per customer_id", """
    SELECT COUNT(*) FROM (
        SELECT customer_id FROM orders GROUP BY customer_id HAVING COUNT(*) > 1
    )
""")
show("product categories", "SELECT * FROM category_translation LIMIT 5")
show("reviews", """
    SELECT review_score, review_comment_message FROM order_reviews
    WHERE review_comment_message IS NOT NULL LIMIT 3
""")

conn.close()