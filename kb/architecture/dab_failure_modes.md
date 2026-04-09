# DAB Failure Mode Taxonomy

> KB v1 — Architecture Layer | Oracle Forge
> Source: DataAgentBench paper (arxiv.org/html/2603.20576), Section 3.3
> Purpose: Give the agent a precise vocabulary for diagnosing its own failures,
> so it can apply the correct fix rather than retrying blindly.

---

## Why This Document Exists

85% of wrong answers in DAB come from FM2 (incorrect plan) or FM4 (incorrect implementation).
Only 15% come from FM3 (wrong data selection).
Agents are usually looking at the right data — they are computing the wrong thing.

Knowing which failure mode you are in determines which fix to apply.
Retrying without diagnosis wastes iterations and produces the same wrong answer.

---

## FM1 — Fails Before Planning

**Definition:** The agent makes no attempt to solve the query.

**Variants:**
- FM1(no_tool_call): agent returns None in the tool-call field → execution terminates immediately
- FM1(other): agent calls return_answer immediately with "I cannot solve this"

**Causes in DAB:**
- Large tool result returned → agent overwhelmed → returns None
- Context window exceeded → agent cannot process next step
- API error (503, 400) → execution terminated

**Fix:**
- Reduce query scope (add LIMIT, paginate)
- Load full result from file path instead of inline context
- Retry with simplified first step

**Frequency:** Significant only for Gemini-2.5-Flash (63.4% of its failures are FM1).
For other models: rare (<5% of failures).

---

## FM2 — Incorrect Plan

**Definition:** The logical structure of the solution is wrong.
Even if all steps execute perfectly, the plan cannot produce the correct answer.

**Examples from DAB:**
1. Computing decade average by averaging per-book averages
   (correct: average ALL ratings within the decade directly)
2. Adding LIMIT 200 when the query requires all rows
3. Missing the "average rating = 5.0" constraint entirely
4. Stopping after finding books in a category without checking the rating filter

**How to detect FM2:**
Re-read the query. Ask: "If I execute my plan perfectly, does it answer what was asked?"
If the answer is "no" or "not exactly" → FM2.

**Fix:**
Re-read the query carefully. Identify the exact operation required.
Write out the plan in plain English before writing any code.
Check: does the plan handle ALL constraints in the query?

**Frequency:** ~40% of completed-but-wrong trajectories.

---

## FM3 — Correct Plan, Wrong Data Selection

**Definition:** The plan is logically correct but the agent queries the wrong
column, table, collection, or database.

**Examples from DAB:**
1. Searching for "English" in the description column instead of the details column
2. Using raw close price instead of adjusted close for volatility
3. Querying the wrong table for a metric that exists in a different table

**How to detect FM3:**
The plan is right but the result is wrong.
Check: are you querying the column that actually contains the needed information?
Verify against schema_overview.md and unstructured_fields.md.

**Fix:**
Re-read schema_overview.md for the dataset.
Check unstructured_fields.md for which column contains the needed value.
Correct the column reference and retry.

**Frequency:** ~15% of completed-but-wrong trajectories. Least common failure mode.

---

## FM4 — Correct Plan and Data, Incorrect Implementation

**Definition:** The plan is right, the data selection is right, but the code is wrong.

**Examples from DAB:**
1. Regex `\b(19\d{2}|20\d{2})\b` matches ISBN numbers as years
2. Regex `MALE` matches inside "FEMALE" (missing word boundary)
3. Join on raw IDs without normalizing prefix differences → zero rows
4. Averaging averages instead of computing overall average
5. Incorrect date parsing for varied natural language date formats

**How to detect FM4:**
The plan is right, the data is right, but the output is wrong.
Test the specific operation in isolation with known inputs.
Verify: does the regex/join/calculation produce the expected output on a sample?

**Fix:**
Test the specific failing operation with a small sample.
For regex: test against 5 sample values manually.
For joins: check that merged rows look correct before aggregating.
For calculations: verify formula against a known example.

**Frequency:** ~45% of completed-but-wrong trajectories. Most common failure mode.

---

## The Patents Dataset — Why It Scores 0%

The patents dataset achieves 0% pass@1 for ALL five frontier models tested.
Root cause: FM4 — every agent uses regex for date extraction.
The date formats in patents cannot be handled by regex:
- "dated 5th March 2019"
- "March the 18th, 2019"
- "filed on the fifth day of March, two thousand and nineteen"

Fix: use LLM-based date extraction or dateutil.parser, NOT regex.
```python
from dateutil import parser
date = parser.parse("5th March 2019")  # Works
date = parser.parse("March the 18th, 2019")  # Works
```

If Oracle Forge uses LLM/dateutil for patents dates, it will be the ONLY agent
in the benchmark that solves patents queries. This is a significant score opportunity.

---

## Quick Reference: Failure Diagnosis

| Symptom | Most Likely FM | First Check |
|---|---|---|
| Zero rows after join | FM4 | Join key format mismatch |
| Wrong count (too high) | FM4 | Many-to-many join, add deduplication |
| Wrong count (too low) | FM2 or FM3 | Missing filter or wrong column |
| Correct structure, wrong values | FM4 | Regex or calculation error |
| Missing required items in result | FM2 | Plan missing a constraint |
| Extra items in result | FM2 | Plan has extra/wrong constraint |
| Empty result on patents | FM4 | Using regex for date parsing |
