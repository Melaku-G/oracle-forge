# Oracle Forge — Adversarial Probe Library

**Minimum required:** 15 probes across 3+ failure categories.
**Status:** 15 / 15 complete — all 4 failure categories covered.

Drivers fill in: Observed Failure, Fix Applied, Post-Fix Score after running each probe.

---

## Failure Category Index

| Category | Probes |
|----------|--------|
| Multi-database routing failure | 001, 005, 006, 007, 015 |
| Ill-formatted join key mismatch | 002, 008, 009 |
| Unstructured text extraction failure | 003, 010, 011 |
| Domain knowledge gap | 004, 012, 013, 014, 015 |

---

## Probe 001: Cross-DB Revenue + Support Ticket Join

**Query:**
> Which customers generated more than $5,000 in revenue last quarter AND submitted more than 3 support tickets in the same period?

**Failure category:** Multi-database routing failure

**Expected failure:** Agent queries only PostgreSQL for revenue and either ignores the MongoDB support database entirely, or attempts a cross-database SQL join that the execution engine cannot run. Returns revenue data only, or throws a query execution error.

**Observed failure:** _(Driver fills)_

**Fix applied:** _(Driver fills)_

**Post-fix score:** _(Driver fills)_

---

## Probe 002: Integer-to-Prefixed-String Join Key

**Query:**
> Show me the average review star rating for each customer alongside their total transaction value.

**Failure category:** Ill-formatted join key mismatch

**Expected failure:** Agent joins `review.user_id` (integer in PostgreSQL) directly with MongoDB's `user_id` (stored as `"USR-12345"` string). Join returns zero rows. Agent reports no matching customers without diagnosing the format mismatch.

**Observed failure:** _(Driver fills)_

**Fix applied:** _(Driver fills)_

**Post-fix score:** _(Driver fills)_

---

## Probe 003: Sentiment Count From Review Text

**Query:**
> How many reviews for businesses in the "Restaurants" category contain a negative mention of wait time?

**Failure category:** Unstructured text extraction failure

**Expected failure:** Agent returns a raw count of reviews containing the word "wait" using a `LIKE` query, regardless of sentiment polarity. Over-counts significantly because "wait was fine" and "not a long wait" both match. No sentiment classification step applied.

**Observed failure:** _(Driver fills)_

**Fix applied:** _(Driver fills)_

**Post-fix score:** _(Driver fills)_

---

## Probe 004: "Active Business" Domain Term Ambiguity

**Query:**
> How many active businesses in Las Vegas have an average rating above 4 stars?

**Failure category:** Domain knowledge gap

**Expected failure:** Agent uses row existence in the `business` table as its definition of "active." Correct definition: a business with at least one review in the last 12 months. Agent returns a count higher than correct and does not flag the ambiguity.

**Observed failure:** _(Driver fills)_

**Fix applied:** _(Driver fills)_

**Post-fix score:** _(Driver fills)_

---

## Probe 005: Three-Database Fan-Out Query

**Query:**
> Which business categories have the highest ratio of 5-star reviews to total support contacts, broken down by city?

**Failure category:** Multi-database routing failure

**Expected failure:** Agent correctly queries PostgreSQL for review stars and business categories but fails to route the "support contacts" sub-query to MongoDB. Either invents a proxy column from the PostgreSQL schema or errors on a non-existent table.

**Observed failure:** _(Driver fills)_

**Fix applied:** _(Driver fills)_

**Post-fix score:** _(Driver fills)_

---

## Probe 006: MongoDB Aggregation Dialect Mismatch

**Query:**
> What is the average number of support tickets per customer segment, grouped by the segment's primary product category?

**Failure category:** Multi-database routing failure

**Expected failure:** Agent writes a SQL `GROUP BY` query and runs it against the MongoDB `support_tickets` collection, which requires an aggregation pipeline (`$group`, `$avg`), not SQL. Query fails at execution with a dialect error. Agent surfaces the raw error or returns no results without recovering.

**Observed failure:** _(Driver fills)_

**Fix applied:** _(Driver fills)_

**Post-fix score:** _(Driver fills)_

---

## Probe 007: DuckDB Analytical Query Routing

**Query:**
> What is the 30-day rolling average revenue per business category over the last 6 months?

**Failure category:** Multi-database routing failure

**Expected failure:** Agent routes to PostgreSQL and attempts a rolling window query using standard SQL. Query should route to DuckDB, which holds the pre-aggregated time-series data and supports native analytical SQL. Result is either slow, incorrect, or fails because the PostgreSQL table does not contain the required data.

**Observed failure:** _(Driver fills)_

**Fix applied:** _(Driver fills)_

**Post-fix score:** _(Driver fills)_

---

## Probe 008: Zero-Padded vs Non-Padded Key

**Query:**
> List all transactions for customer 423 alongside their CRM profile data.

**Failure category:** Ill-formatted join key mismatch

**Expected failure:** Agent looks up MongoDB for `"CUST-423"` (no padding) when the actual format is `"CUST-00423"` (5-digit zero-padded). Join returns zero results. Agent does not detect the padding discrepancy and does not flag the empty result as suspicious.

**Observed failure:** _(Driver fills)_

**Fix applied:** _(Driver fills)_

**Post-fix score:** _(Driver fills)_

---

## Probe 009: Reversed Key Direction

**Query:**
> For each MongoDB support ticket, show me the customer's total lifetime spend from the transaction database.

**Failure category:** Ill-formatted join key mismatch

**Expected failure:** Agent correctly converts PostgreSQL integer IDs to MongoDB string format but does not handle the reverse — converting MongoDB string IDs back to PostgreSQL integers when starting from MongoDB. The join fails because only one direction of the format rule is registered in `join_key_resolver.py`.

**Observed failure:** _(Driver fills)_

**Fix applied:** _(Driver fills)_

**Post-fix score:** _(Driver fills)_

---

## Probe 010: Nested JSON Field Extraction

**Query:**
> How many Yelp users have received more than 100 "useful" votes across all their reviews?

**Failure category:** Unstructured text extraction failure

**Expected failure:** The `useful` vote count is stored as a nested field inside MongoDB review documents — `{"useful": 12, "funny": 3, "cool": 1}`. Agent attempts to query it as a flat column, fails to traverse the nested structure, and returns zero results or an execution error. No document traversal step is applied before aggregating.

**Observed failure:** _(Driver fills)_

**Fix applied:** _(Driver fills)_

**Post-fix score:** _(Driver fills)_

---

## Probe 011: Compound Sentiment — Two Topics

**Query:**
> How many reviews mention both slow service AND poor food quality negatively?

**Failure category:** Unstructured text extraction failure

**Expected failure:** Agent runs two separate `LIKE` queries (`text LIKE '%slow%'` AND `text LIKE '%food%'`) on `review.text`. Over-counts — reviews that say "not slow" or "actually good food" match the keywords but are positive. No per-topic sentiment classification applied. Count is significantly inflated.

**Observed failure:** _(Driver fills)_

**Fix applied:** _(Driver fills)_

**Post-fix score:** _(Driver fills)_

---

## Probe 012: "Churn" Without Domain Definition

**Query:**
> Which customer segments have the highest churn rate this quarter?

**Failure category:** Domain knowledge gap

**Expected failure:** Agent defines "churn" as customers whose account status field is `"inactive"` or `"closed."` Correct definition: customers who have not made a purchase in 90 days, regardless of account status (which is frequently stale). Agent understates churn in segments where accounts remain open but customers are inactive. Result is numerically plausible but wrong.

**Observed failure:** _(Driver fills)_

**Fix applied:** _(Driver fills)_

**Post-fix score:** _(Driver fills)_

---

## Probe 013: Fiscal Quarter vs Calendar Quarter

**Query:**
> Compare revenue in Q1 this year versus Q1 last year.

**Failure category:** Domain knowledge gap

**Expected failure:** Agent assumes Q1 = January–March (calendar quarter). The dataset uses a fiscal calendar where Q1 = April–June. Agent generates correct-looking SQL date filters (`BETWEEN '2026-01-01' AND '2026-03-31'`) that silently return the wrong period. Result is plausible but off by one quarter in both years.

**Observed failure:** _(Driver fills)_

**Fix applied:** _(Driver fills)_

**Post-fix score:** _(Driver fills)_

---

## Probe 014: "High-Rated" Without Review Count Floor

**Query:**
> List the top 10 highest-rated businesses in Phoenix.

**Failure category:** Domain knowledge gap

**Expected failure:** Agent runs `SELECT * FROM business WHERE city = 'Phoenix' ORDER BY stars DESC LIMIT 10`. Returns businesses with 5-star ratings that have only 1–2 reviews — statistically meaningless but schema-valid. Correct query requires `AND review_count >= 10`. Result is dominated by businesses with almost no reviews.

**Observed failure:** _(Driver fills)_

**Fix applied:** _(Driver fills)_

**Post-fix score:** _(Driver fills)_

---

## Probe 015: Cross-DB Entity Resolution + Domain Term (Compound)

**Query:**
> Which active customers in the high-value segment had more than 5 negative support interactions last month?

**Failure category:** Multi-database routing failure *(also tests Domain knowledge gap)*

**Expected failure:** Two failure modes tested simultaneously.

1. Agent must route to both PostgreSQL (transaction history to confirm "active" = purchased in last 90 days) and MongoDB (support ticket sentiment). Most likely only one database is queried.
2. "High-value segment" is not defined in any schema. Agent either ignores it, invents a proxy (e.g. top revenue decile), or errors without flagging the ambiguity.

Most common observed pattern: agent queries only one database and uses row existence as the definition of "active."

**Observed failure:** _(Driver fills)_

**Fix applied:** _(Driver fills)_

**Post-fix score:** _(Driver fills)_