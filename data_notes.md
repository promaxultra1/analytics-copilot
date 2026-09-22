# Olist data notes

Known quirks in the Olist dataset that affect whether an answer is correct.
Each was verified directly against `data/olist.db` (see `explore_olist.py`).

Status: **not** in the system prompt. Deliberately withheld so Phase 3b can
measure how often the agent gets these wrong unaided. These notes are the
planned content for the Phase 5 definitions knowledge base and the seed of the
Phase 7 golden questions.

---

## 1. Two customer identifiers — only one is a person

`customers` has both `customer_id` and `customer_unique_id`.

- `customer_id` is **per order**. A repeat buyer gets a new one each time.
- `customer_unique_id` is **the person**, stable across orders.

Verified: zero `customer_id` values appear in more than one order, across 99,441
orders. Counting customers with `customer_id` therefore returns 99,441 and makes
every repeat buyer look new.

**Rule:** count, segment, and identify customers with `customer_unique_id`.
Use `customer_id` only to join `orders` to `customers`.

**Failure mode:** silent. The query runs and returns a plausible number.

## 2. Not every order was delivered

`orders.order_status` values (of 99,441 total):

| status | orders |
|---|---|
| delivered | 96,478 |
| shipped | 1,107 |
| canceled | 625 |
| unavailable | 609 |
| invoiced | 314 |
| processing | 301 |
| created | 5 |
| approved | 2 |

2,965 orders have a NULL `order_delivered_customer_date`.

**Rule:** any question about delivery time, lateness, or fulfilment should filter
to `order_status = 'delivered'`, or at minimum require
`order_delivered_customer_date IS NOT NULL`.

**Failure mode:** averages computed over a partial population, with no warning.

## 3. Timestamps are stored as text

All date columns are strings like `'2017-10-02 10:56:33'`, not date types.

- String comparison and `BETWEEN` work for ranges.
- Date arithmetic needs `julianday()`.

**Rule:** days late =
`julianday(order_delivered_customer_date) - julianday(order_estimated_delivery_date)`
(positive = late).

## 4. Product categories are in Portuguese

`products.product_category_name` holds Portuguese names
(`beleza_saude`, `cama_mesa_banho`, ...). `category_translation` (71 rows) maps
them to English.

**Rule:** join through `category_translation` before showing a category to a user.

**Note:** 71 translations for 32,951 products — check whether every category in
`products` has a match, and whether `product_category_name` is ever NULL.

## 5. Review comments are Portuguese free text

`order_reviews.review_comment_message` is untranslated customer writing, and
many rows are NULL.

Two consequences:

- **Search:** English keyword matching (`LIKE '%late%'`) finds nothing. Matching
  requires Portuguese terms, or an approach that isn't keyword matching.
- **Untrusted input:** this text enters the model's context straight from the
  database, and nothing stops a customer from writing instructions in a review.
  This is the injection risk flagged in Phase 2. Contained by the read-only
  connection, not by the prompt.

## 6. Row cap limits rows, not size

`run_sql` caps results at 50 rows. Review comments are long, so 50 rows of
review text is far more context than 50 rows of Chinook invoice lines.
Watch input token counts on any query that returns comment text.

---

## Open questions to verify

- Does every `products.product_category_name` have a translation?
- Are there orders with no matching rows in `order_items` or `order_payments`?
- Do multiple payment rows per order inflate revenue when joined to
  `order_items`? (Classic double-count: one order, several payment rows.)
- Is `order_items.price` per unit or per line, and where does `freight_value`
  belong in a revenue definition?
