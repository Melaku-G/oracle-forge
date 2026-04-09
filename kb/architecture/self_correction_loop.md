# Closed-Loop Self-Correction Pattern

> KB v1 — Architecture Layer | Oracle Forge
> Purpose: Give the agent a concrete decision procedure for diagnosing and recovering
> from failures during DAB query execution, without surfacing errors to the user.

---

## The Pattern in One Sentence

When an intermediate result looks wrong, the agent diagnoses WHY it is wrong,
fixes the specific cause, and retries — rather than returning the wrong result
or giving up.

---

## The Execution Loop

```
Query arrives
    ↓
Agent plans sub-queries (which databases, which tables, what joins)
    ↓
Agent executes sub-queries in parallel where possible
    ↓
Agent checks intermediate results ← THIS IS THE CRITICAL STEP
    ↓
Result looks plausible? → proceed to merge and answer
Result looks wrong?     → diagnose failure type → fix → retry
```

---

## Plausibility Checks After Every Join

After every cross-database join, check:

1. Row count = 0
   Diagnosis: join key format mismatch
   Action: inspect both key columns, check for prefix differences, trailing spaces
   Fix: normalize keys using join_key_resolver.py, retry join

2. Row count much higher than expected (e.g., 10x the larger table)
   Diagnosis: many-to-many join producing cartesian product
   Action: add deduplication or change join type
   Fix: use GROUP BY or DISTINCT, retry

3. Key column values look wrong in merged result
   Diagnosis: joined on wrong column
   Action: re-read schema, identify correct join columns
   Fix: change join condition, retry

4. All values in a column are NULL after join
   Diagnosis: wrong column selected, or column exists in one DB but not the other
   Action: check column names in both databases
   Fix: correct column reference, retry

---

## Failure Mode Taxonomy (from DAB Paper)

Use this taxonomy to diagnose failures before retrying:

**FM1 — Fails Before Planning**
Agent returns None or refuses to attempt the query.
Cause: overwhelmed by large result, API error, context overflow.
Fix: reduce query scope, paginate results, simplify first attempt.

**FM2 — Incorrect Plan**
The logical structure of the solution is wrong.
Even perfect execution cannot produce the correct answer.
Examples:
- Averaging per-book averages instead of averaging all ratings directly
- Adding LIMIT 200 when the query requires all rows
- Missing a required filter (e.g., forgetting the "average rating = 5.0" constraint)
Fix: re-read the query carefully, identify what operation is actually required.

**FM3 — Correct Plan, Wrong Data Selection**
The plan is right but the agent queries the wrong column or table.
Example: searching for "English" in the description column instead of details column.
Fix: re-read schema, check which column actually contains the needed information.

**FM4 — Correct Plan and Data, Incorrect Implementation**
The plan is right, the data is right, but the code is wrong.
Examples:
- Regex `\bMALE\b` without word boundary matches inside "FEMALE"
- Year extraction regex matches ISBN numbers as years
- Join condition uses raw IDs instead of normalized IDs
Fix: test the specific operation in isolation, verify output before using in pipeline.

---

## The 85% Rule

From the DAB paper: 85% of wrong answers are FM2 or FM4.
Only 15% are FM3 (wrong data selection).

This means: when the agent gets a wrong answer, the most likely cause is
either a planning error (FM2) or an implementation error (FM4).
The agent is usually looking at the right data — it is computing the wrong thing
or computing it incorrectly.

Implication for self-correction: before assuming the data is wrong,
verify the plan and the implementation first.

---

## Specific Checks for DAB Datasets

### After any bookreview join
Check: do merged rows have both book title and review rating?
If not: join key normalization failed. Strip bid_/bref_ prefixes and retry.

### After any crmarenapro join
Check: are there cases with no matching assignments?
If yes: trailing space in ID field. Apply TRIM() and retry.

### After any text extraction
Check: do extracted values fall in expected range?
Year extraction: values should be between 1800 and 2024.
If you see values like 9780 or 1932 from a book published in 2004: ISBN matched, not year.

### After any stockmarket query
Check: are you using adj_close or close?
Volatility and price comparisons must use adj_close (adjusted for splits/dividends).
Using close will produce wrong results for stocks that split.

---

## Logging Requirement

Every failure that triggers the self-correction loop must be logged.
Format: [what failed] → [diagnosis] → [fix applied] → [result after fix]
Location: kb/corrections/corrections_log.md
Timing: within 2 hours of the mob session where the failure was observed.

This log is what makes the agent improve between Week 8 and Week 9.
Without logging, the same failures repeat. With logging, they do not.
