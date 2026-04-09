# DuckDB in DAB: Evaluation-Specific Notes

Here is how this works.

DuckDB is one of the four database systems in DAB. From an evaluation perspective, DuckDB queries have specific properties that affect how the harness scores them and how the agent must structure its responses. This document covers what is different about DuckDB queries in the evaluation context — the general DuckDB failure modes are in `kb/architecture/ddb_failure_modes.md`.

**Which DAB queries involve DuckDB.** DuckDB appears in DAB datasets that require analytical workloads — rolling averages, time-series aggregations, percentile calculations, and large-scale columnar scans. When `eval/list_datasets.py` outputs a dataset with DuckDB as one of its database types, assume at least some queries in that dataset require DuckDB-specific handling.

**Evaluation input format.** The agent receives `{question, available_databases, schema_info}`. When DuckDB is in `available_databases`, the agent must include DuckDB in its routing plan before generating any query. Agents that ignore DuckDB in the routing plan will fail all queries that require it — these are scored as failures across all 5+ trials.

**Query trace requirement.** For DuckDB queries, the trace must show: (1) which MCP tool was called (`duckdb_query`); (2) the exact analytical SQL sent; (3) the raw result returned before any post-processing. A result without this trace is not a valid submission for DuckDB-involving queries.

**Common scoring pitfalls specific to DuckDB.**

- *Pre-aggregated tables:* DuckDB datasets often contain pre-aggregated tables (e.g. `daily_revenue_summary`). An agent that re-aggregates from raw transaction tables will get the right shape of answer but potentially wrong numbers if the pre-aggregated table uses different business logic (e.g. a different definition of "revenue"). Always check the DuckDB schema for pre-aggregated tables before writing aggregation queries from scratch.

- *Floating point results:* DuckDB returns high-precision floats for analytical calculations. The DAB scorer applies a tolerance threshold for numerical answers — answers within ±0.01 of the correct value are accepted. Do not round intermediate results; only round the final output to 2 decimal places.

- *Result ordering:* Some DuckDB queries return unordered columnar results. If the expected answer is an ordered list, the agent must apply `ORDER BY` explicitly — the scorer does not sort before comparing.

**Harness setup for DuckDB.** Confirm the DuckDB MCP tool is live before running evaluations:

```bash
curl http://localhost:5000/v1/tools | python3 -m json.tool | grep duckdb
# Expected: "duckdb_query" appears in the tool list
```

If it does not appear, check `mcp/tools.yaml` for the DuckDB source definition and restart the toolbox.

---

**Injection test question:** A DuckDB query returns a floating point result of `1432.7891`. The correct answer is `1432.80`. Will the DAB scorer accept this, and what should the agent do with the result before returning it?

**Expected answer:** Yes — the scorer applies a ±0.01 tolerance, and `1432.7891` is within that range of `1432.80`. The agent should round the final output to 2 decimal places (`1432.79`) before returning it, but must not round intermediate calculations, as that would propagate rounding error into the final result.