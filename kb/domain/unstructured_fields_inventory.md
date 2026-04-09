# Unstructured Fields Inventory

Here is how this works.

This document lists every field across DAB datasets that contains unstructured or semi-structured text requiring an extraction step before it can be used in a calculation or aggregation. Querying these fields without extraction produces wrong answers — the agent either returns raw text or aggregates over the wrong unit.

**The rule:** Any query that asks for a count, average, classification, or comparison involving a field listed here must include an extraction step before the aggregation step. The extraction step converts free text into a structured fact (a label, a number, a boolean) that can then be counted or grouped.

**Format per entry:** Dataset | Database | Table/Collection | Field | Content type | Required extraction | Example query that needs extraction

---

## Yelp Dataset

| Field | Database | Content Type | Required Extraction | Example Query |
|-------|----------|-------------|--------------------|--------------------|
| `review.text` | PostgreSQL | Free-form customer review prose | Sentiment classification, topic detection, keyword extraction | "How many reviews mention slow service negatively?" |
| `business.categories` | PostgreSQL | Comma-separated category string, e.g. `"Restaurants, Italian, Pizza"` | String split and normalisation before GROUP BY | "How many businesses are in the Restaurants category?" |

**Note on `business.categories`:** This field looks structured but is stored as a single comma-separated string, not a normalised array. A GROUP BY on the raw field will group by the entire string, not by individual category. The agent must split the string before aggregating.

---

## General Extraction Patterns

**Sentiment classification:** Use a secondary LLM call or a lightweight classifier. Do not use keyword matching alone — "not bad" is positive, "wait was fine" may be neutral. The extraction result should be a label (`positive`, `negative`, `neutral`) stored as a structured intermediate before counting.

**Topic detection:** Extract whether a specific topic (e.g. "wait time", "staff friendliness") is mentioned. Return a boolean per review, then count the trues.

**Keyword normalisation:** Some fields contain inconsistent spellings or abbreviations. Normalise before comparing (e.g. `"NY"` vs `"New York"` in location fields).

---

**Drivers:** When a query fails because the agent aggregated over raw text, add the field here and log the failure in `kb/corrections/corrections_log.md`.

---

**Injection test question:** A query asks for the count of Yelp reviews that mention slow service negatively. Which field requires extraction, what type of extraction is needed, and what is wrong with using simple keyword matching?

**Expected answer:** `review.text` in PostgreSQL requires sentiment classification combined with topic detection. Simple keyword matching is insufficient because phrases like "wait was not that bad" contain the keyword "wait" but are not negative — the extraction must classify sentiment in the context of the topic, not match keywords alone.