# Domain Term Definitions

Here is how this works.

This document defines business and domain terms that appear in DAB queries but are not defined in any database schema. These are the terms that cause DAB Failure Category 4 (domain knowledge gap) — the agent uses a naive proxy definition when the correct definition is domain-specific. Every term here has a naive interpretation (what the agent will assume without this document) and a correct interpretation (what the term actually means in this dataset's domain).

**The rule:** Before generating a query that uses any term listed here, the agent must substitute the correct interpretation, not the naive one. If a term is not listed here and is ambiguous, the agent must flag the ambiguity in its response rather than silently use a proxy.

---

## Yelp Dataset Terms

**Active business**
- Naive interpretation: any row in the `business` table
- Correct interpretation: a business with at least one review dated within the last 12 months
- Query implication: requires a JOIN to `review` with a date filter; row existence alone is not sufficient

**High-rated business**
- Naive interpretation: `stars >= 4` in the `business` table
- Correct interpretation: `stars >= 4` AND `review_count >= 10` — businesses with fewer than 10 reviews are statistically unreliable and excluded in standard Yelp analysis
- Query implication: always add `AND review_count >= 10` when filtering by rating

**Recent review**
- Naive interpretation: any row in the `review` table
- Correct interpretation: a review with `date` within the last 90 days relative to the query date
- Query implication: requires a date filter using the current date as reference

**Repeat customer**
- Naive interpretation: a user with more than one row in the `review` table
- Correct interpretation: a user who has reviewed businesses in the same category more than once — single-category repeat engagement, not total review count
- Query implication: requires grouping by user AND business category before counting

---

## General Cross-Dataset Terms

**Churn** (retail, telecom domains)
- Correct interpretation: a customer who has not made a purchase or used the service within the domain-defined inactivity window (typically 90 days for retail, 30 days for telecom). Never defined by account closure alone.

**Active account** (finance, telecom domains)
- Correct interpretation: an account with at least one transaction in the last 30 days. Not equivalent to account status field being "active" — status fields are often stale.

**Fiscal quarter**
- Correct interpretation: varies by organisation. Do not assume calendar quarters (Jan–Mar, Apr–Jun, etc.) unless the dataset schema confirms it. Check for a `fiscal_calendar` table or note in the dataset README.

---

**Injection test question:** A DAB query asks for the count of "active businesses" in a city. What is the naive interpretation an agent would use, what is the correct interpretation, and what does the correct query require?

**Expected answer:** The naive interpretation is any row in the `business` table (i.e., all businesses). The correct interpretation is a business with at least one review dated within the last 12 months. The correct query requires a JOIN between `business` and `review` with a date filter on `review.date`, not a simple SELECT COUNT from `business`.