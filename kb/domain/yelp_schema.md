# Yelp Dataset Schema (DAB Starting Dataset)

Here is how this works.

The Yelp dataset is the recommended starting point in DAB because it contains multi-source data, nested JSON, missing values, and entity resolution challenges that mirror the full DAB problem space in a contained form. Use it to validate your agent architecture before extending to other datasets.

**Important:** The authoritative schema is in the DAB repository at `github.com/ucbepic/DataAgentBench`. The entries below are derived from the practitioner manual's descriptions and standard Yelp open dataset conventions. Drivers must verify column names and types by running `python eval/list_datasets.py` and inspecting the loaded tables before relying on this document.

**PostgreSQL tables (inferred from DAB documentation):**

- `business` — business_id (integer PK), name, city, state, stars (float), review_count (integer), categories (text, comma-separated)
- `review` — review_id (integer PK), business_id (integer FK), user_id (integer FK), stars (integer), date (date), text (text — **unstructured field**)
- `user` — user_id (integer PK), name, review_count, average_stars

**MongoDB collections (inferred):**

- `reviews` collection — documents keyed on `user_id` as string, e.g. `"USR-00123"`. The exact prefix format must be confirmed by inspection.
- Nested fields likely include: `useful`, `funny`, `cool` reaction counts; `elite` years as array.

**Known join key mismatch (critical):**

The `user_id` field is an integer in the PostgreSQL `user` and `review` tables but is stored as a prefixed string in MongoDB (e.g. `"USR-12345"`). The agent must detect this mismatch and apply format resolution before attempting any cross-database join. Use `utils/join_key_resolver.py` for this.

**Unstructured field requiring extraction:**

`review.text` in PostgreSQL contains free-form customer review text. Any query asking for sentiment, topic mentions, or categorised feedback requires an extraction step before aggregation.

**Action required:** After loading the Yelp dataset, run schema introspection and update this document with confirmed column names, actual MongoDB key format strings, and any additional join key mismatches found.

---

**Injection test question:** Which field in the Yelp dataset requires an extraction step before it can be used in an aggregation query, and why?

**Expected answer:** `review.text` — it is a free-text field containing unstructured customer review content. Aggregating over it (e.g., counting negative sentiment mentions) requires an extraction step to produce structured facts before any counting or grouping can occur.