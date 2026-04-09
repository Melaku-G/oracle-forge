# utils/ — Shared Utility Library

This directory contains reusable modules for the Oracle Forge data agent. Every module is documented, tested, and importable by any team member. Drivers use these in the agent implementation. Intelligence Officers maintain the documentation here and in the relevant KB documents.

---

## Modules

### `join_key_resolver.py`

**Purpose:** Resolves ill-formatted join key mismatches across heterogeneous databases (DAB Failure Category 2).

**Problem it solves:** Entity IDs are formatted differently across database systems. A customer ID stored as integer `12345` in PostgreSQL may appear as `"USR-12345"` in MongoDB. Attempting a join on the raw values returns zero results. This module converts keys from one format to another using a registry of confirmed format rules.

**Usage:**

```python
from utils.join_key_resolver import resolve_join_key

# PostgreSQL integer → MongoDB string
mongo_id = resolve_join_key(12345, source_db="postgresql", target_db="mongodb")
# Returns: "USR-12345"

# MongoDB string → PostgreSQL integer
pg_id = resolve_join_key("USR-12345", source_db="mongodb", target_db="postgresql")
# Returns: 12345
```

**When the resolver returns `None`:** No format rule is registered for that database pair. Add the missing rule to `FORMAT_REGISTRY` in `join_key_resolver.py` and document the exact format string in `kb/domain/yelp_schema.md` (or the relevant dataset doc). Do not add a rule without first confirming the format by inspecting the actual loaded data.

**Running the smoke test:**

```bash
python utils/join_key_resolver.py
# Expected: join_key_resolver: all smoke tests passed.
```

**Adding new format rules:** Edit `FORMAT_REGISTRY` in `join_key_resolver.py`. Each entry key is a `(source_db, target_db)` tuple. Add a corresponding entry to the relevant `kb/domain/` document and update `kb/corrections/corrections_log.md` if the rule was discovered via an agent failure.

---

---

### `schema_introspector.py`

**Purpose:** Introspects all four DAB database types (PostgreSQL, MongoDB, SQLite, DuckDB) and returns a unified schema description the agent can inject into its context window. Also detects potential join key format mismatches across databases.

**Usage:**

```python
from utils.schema_introspector import introspect_all, format_for_kb

connections = [
    {"db_type": "postgresql", "name": "yelp_postgres", "params": {...}},
    {"db_type": "mongodb",    "name": "yelp_mongo",    "params": {...}},
    {"db_type": "sqlite",     "name": "dab_sqlite",    "params": {...}},
    {"db_type": "duckdb",     "name": "dab_duckdb",    "params": {...}},
]
result = introspect_all(connections)
print(format_for_kb(result))  # paste output into kb/domain/yelp_schema.md
```

**When to run:** Run after loading any new DAB dataset. Paste the `format_for_kb()` output into the relevant `kb/domain/` document and update `kb/domain/CHANGELOG.md`.

**Driver action required:** Replace the placeholder `_introspect_postgres`, `_introspect_mongo`, `_introspect_sqlite`, and `_introspect_duckdb` functions with real database connections (psycopg2, pymongo, sqlite3, duckdb).

**Running the smoke test:**

```bash
python utils/schema_introspector.py
# Expected: prints schema summary and "smoke test passed."
```

---

### `multi_pass_retrieval.py`

**Purpose:** Runs multiple retrieval passes with different query vocabulary over KB documents, then deduplicates and merges results. Prevents the single-pass retrieval failure where a KB entry is missed because the query uses different vocabulary than the document.

**Usage:**

```python
from utils.multi_pass_retrieval import multi_pass_retrieve, retrieve_corrections, retrieve_domain_term

# Retrieve corrections for a failure category using full vocab expansion
results = retrieve_corrections("join_key_mismatch", kb_path="kb/corrections/corrections_log.md")

# Retrieve a domain term definition with paraphrase handling
definition = retrieve_domain_term("active customer", kb_path="kb/domain/domain_terms.md")

# Custom passes
results = multi_pass_retrieve(
    query="agent joined wrong database",
    kb_path="kb/corrections/corrections_log.md",
    pass_queries=["routing failure", "only one database queried", "cross-db join failed"],
)
```

**Running the smoke test:**

```bash
python utils/multi_pass_retrieval.py
# Expected: multi_pass_retrieval: all smoke tests passed.
```

---

### `benchmark_harness_wrapper.py`

**Purpose:** Wraps the DAB evaluation loop with structured trace logging, pass@1 score computation, score progression tracking across runs, and regression detection. Produces the results JSON required for DAB GitHub PR submission.

**Usage:**

```python
from utils.benchmark_harness_wrapper import BenchmarkHarness

harness = BenchmarkHarness(
    agent_fn=your_agent,       # must accept AgentInput, return AgentOutput
    output_dir="results/",
    trials=5,                  # DAB minimum — do not reduce
    run_label="week8-baseline",
)
harness.load_queries()         # loads from eval/expected_answers.json
harness.run_all()
harness.record_score()         # appends to results/score_log.json
harness.save_results()         # saves results/results_week8-baseline.json
harness.print_score_progression()

# Check for regressions after making a change
harness2 = BenchmarkHarness(agent_fn=updated_agent, run_label="week9-final", ...)
harness2.run_all()
harness2.check_regressions(baseline_label="week8-baseline")
```

**Running the smoke test:**

```bash
python utils/benchmark_harness_wrapper.py
# Expected: benchmark_harness_wrapper: all smoke tests passed.
```

---

## Adding New Modules

Each new module must include:

- A module-level docstring stating its purpose and the DAB failure category it addresses.
- A usage example in this README under a new `###` heading.
- A smoke test runnable via `python utils/<module>.py`.
- A corresponding entry in the relevant `kb/domain/` or `kb/architecture/` document.