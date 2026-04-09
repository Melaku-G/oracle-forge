# DAB Failure Categories and Probe Type Mapping

Here is how this works.

This document maps each of DAB's four failure categories to the probe types that test them and the evaluation signals that confirm a failure occurred. Use this when designing new adversarial probes, reviewing harness output, or diagnosing why the agent's score is not improving.

---

## Failure Category 1 — Multi-Database Routing Failure

**What it tests:** Whether the agent can route sub-queries to the correct database system and merge results across systems in a single answer.

**Probe design rule:** The query must require data from at least two different database types (e.g. PostgreSQL + MongoDB). The correct answer is impossible to produce from a single database.

**Signals that confirm failure occurred:**
- Query trace shows only one database was called
- Agent returns an execution error referencing a table that does not exist in the queried database
- Result contains only partial data (e.g. revenue figures with no ticket counts) with no acknowledgement of incompleteness
- Agent attempts a SQL JOIN across databases without using the MCP Toolbox cross-database merge tool

**Fix direction:** Add explicit routing rules to AGENT.md. Ensure `tools.yaml` exposes distinct tools per database type with clear domain boundaries. Add a routing pre-step that inspects which databases are needed before any query is generated.

---

## Failure Category 2 — Ill-Formatted Join Key Mismatch

**What it tests:** Whether the agent detects and resolves format differences in entity identifiers before attempting a join.

**Probe design rule:** The query requires joining two databases where the shared entity key is formatted differently in each (e.g. integer vs. prefixed string). The schema alone does not reveal the mismatch — the agent must detect it at runtime or from the KB.

**Signals that confirm failure occurred:**
- Join returns zero rows despite both databases containing the entity
- Query trace shows a direct equality join on raw key values without format conversion
- Agent reports "no matching records" without diagnosing the reason

**Fix direction:** Add the confirmed format mismatch to `kb/domain/join_keys_glossary.md` and `utils/join_key_resolver.py`. Add a pre-join step that calls `resolve_join_key()` before any cross-database entity match.

---

## Failure Category 3 — Unstructured Text Extraction Failure

**What it tests:** Whether the agent performs extraction on free-text fields before using them in aggregations.

**Probe design rule:** The query requires a count, classification, or comparison that depends on the content of a free-text field. The correct answer cannot be produced by a SQL WHERE clause alone.

**Signals that confirm failure occurred:**
- Agent returns raw text field values instead of a structured count or classification
- Agent uses LIKE or keyword matching on a field that requires sentiment or topic classification
- Result is numerically plausible but wrong because keyword matching over-counts or under-counts

**Fix direction:** Add the field to `kb/domain/unstructured_fields_inventory.md`. Add an extraction sub-step to the agent pipeline that runs before any aggregation involving the flagged field.

---

## Failure Category 4 — Domain Knowledge Gap

**What it tests:** Whether the agent uses the correct domain definition of a business term rather than a naive structural proxy.

**Probe design rule:** The query uses a term (e.g. "active customer", "churn", "recent") that has a domain-specific meaning not encoded in the schema. The naive interpretation produces a plausible-looking but wrong answer.

**Signals that confirm failure occurred:**
- Answer is numerically higher or lower than correct by a predictable factor (e.g. counts all rows instead of date-filtered rows)
- Query trace shows no JOIN to a date or activity table when one is required
- Agent does not flag ambiguity in the term and silently uses a proxy definition

**Fix direction:** Add the term and its correct definition to `kb/domain/domain_terms.md`. Verify the agent loads this document at session start via AGENT.md.

---

**Injection test question:** An agent returns zero rows when joining two databases. Which failure category does this signal, and what should the query trace show to confirm it?

**Expected answer:** Failure Category 2 — ill-formatted join key mismatch. The query trace should show a direct equality join on raw key values with no format conversion step, confirming the agent attempted the join without resolving the identifier format difference between the two databases.