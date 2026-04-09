# Ill-Formatted Join Key Glossary

Here is how this works.

This glossary documents every confirmed join key format mismatch found across DAB datasets. A join key mismatch means the same real-world entity is stored with differently formatted identifiers in different database systems. The agent must detect the mismatch and resolve it before attempting any cross-database join. Attempting the join on raw values returns zero results.

**How to use this document.** Before writing any cross-database join, check this glossary for the databases and entity type involved. If a rule exists, pass the raw key through `utils/join_key_resolver.py` with the confirmed prefix and padding values. If no rule exists, add one after inspecting the actual loaded data — do not guess the format.

**Format per entry:** Entity | PostgreSQL format | MongoDB format | SQLite format | DuckDB format | Resolver rule

---

## Yelp Dataset

| Entity | PostgreSQL | MongoDB | Resolver Rule |
|--------|-----------|---------|---------------|
| user_id | integer, e.g. `12345` | string, e.g. `"USR-12345"` (prefix TBC — verify by inspection) | `resolve_join_key(val, "postgresql", "mongodb")` |
| business_id | integer PK | string (format TBC) | Verify by running schema introspection |

**Action required:** After loading the Yelp dataset, run the following and update this table with confirmed formats:

```bash
# PostgreSQL — check user_id type and sample values
psql -c "SELECT user_id FROM review LIMIT 5;"

# MongoDB — check user_id format in reviews collection
mongo --eval "db.reviews.findOne({}, {user_id: 1})"
```

---

## General Rules (apply across datasets)

- Integer-to-prefixed-string is the most common mismatch pattern. The prefix varies per dataset — never assume it is `"USR-"` without confirming.
- Zero-padding varies: some datasets use `"CUST-00123"` (5-digit padded), others use `"CUST-123"` (no padding). The `pad_width` field in `FORMAT_REGISTRY` controls this.
- MongoDB ObjectId fields are never directly joinable to SQL integer keys — these require a separate lookup step, not a direct format conversion.

---

**Drivers:** Every new mismatch discovered must be added here AND to `FORMAT_REGISTRY` in `utils/join_key_resolver.py` AND logged in `kb/corrections/corrections_log.md` with the probe that surfaced it.

---

**Injection test question:** Before attempting a join between PostgreSQL `review.user_id` and MongoDB `reviews.user_id`, what must the agent do and where does it find the rule?

**Expected answer:** The agent must check this glossary for the confirmed format of both fields, then pass the raw key through `utils/join_key_resolver.py` using the registered rule. It must not attempt the join on raw values, as PostgreSQL stores the ID as an integer while MongoDB stores it as a prefixed string.