# DuckDB Failure Modes in Multi-Database Agent Contexts

Here is how this works.

DuckDB is one of the four database systems in DAB. It is an in-process analytical SQL engine optimised for columnar, OLAP-style queries — rolling averages, window functions, large aggregations. It is not a transactional database. Agents that treat DuckDB like PostgreSQL will produce wrong results or execution errors.

**Failure Mode 1 — Wrong database routed.** The agent sends an analytical query (rolling averages, percentiles, time-series aggregations) to PostgreSQL instead of DuckDB. PostgreSQL can run window functions but is slower and may not have the pre-aggregated time-series tables that DAB's DuckDB datasets contain. Result: query runs but returns wrong data because the tables don't exist in PostgreSQL, or the agent silently queries the wrong dataset.

**Failure Mode 2 — SQL dialect mismatch.** DuckDB supports analytical SQL extensions not available in standard PostgreSQL — for example `QUALIFY`, `PIVOT`, `UNPIVOT`, and certain `ASOF JOIN` syntax. If the agent generates standard SQL and executes it against DuckDB, some queries fail with syntax errors. The reverse is also true: DuckDB-specific syntax sent to PostgreSQL will fail.

**Failure Mode 3 — Schema assumption mismatch.** DuckDB datasets in DAB are often pre-aggregated or structured for analytical access — wide tables with many columns, denormalised. Agents trained on normalised PostgreSQL schemas may attempt joins that are unnecessary (the data is already joined) or miss columns that exist only in DuckDB.

**Failure Mode 4 — MCP tool not called.** The agent generates a DuckDB-compatible query but calls the PostgreSQL MCP tool instead of the DuckDB tool defined in `tools.yaml`. This is a tool selection error, not a query error. The query trace will show the correct SQL but the wrong tool invocation.

**Detection:** Check the query trace. If a DuckDB analytical query (window function, rolling average, time-series) was routed through `postgres_query` instead of `duckdb_query`, this is Failure Mode 4. If the tool was correct but results are wrong, check for schema assumption mismatch.

**Fix direction:** Add explicit routing rules to AGENT.md: analytical queries involving rolling windows, percentiles, or time-series must route to DuckDB. Ensure `tools.yaml` defines a `duckdb_query` tool with a clear description that the agent's tool-selection logic can match.

---

**Injection test question:** An agent runs a 30-day rolling average query and gets a syntax error. The query trace shows it called `postgres_query`. Which DuckDB failure mode is this and what is the fix?

**Expected answer:** This is Failure Mode 4 — the correct MCP tool was not called. The agent routed an analytical query to the PostgreSQL tool instead of the DuckDB tool. The fix is to add a routing rule to AGENT.md specifying that rolling window and time-series queries must invoke `duckdb_query`, and to verify the DuckDB tool description in `tools.yaml` is specific enough for the agent's tool-selection logic to match it.