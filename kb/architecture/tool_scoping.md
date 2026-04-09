# Tool Scoping Philosophy (Claude Code Architecture)

Here is how this works.

The Claude Code source leak revealed that the agent uses 40+ tools with tight domain boundaries. This is not an accident — it is a deliberate architecture decision that directly affects agent reliability. Understanding why tool scoping matters is required before configuring `tools.yaml` for the Oracle Forge agent.

**The core principle.** Each tool should do exactly one thing, be named to describe that one thing precisely, and have a description specific enough that the agent's tool-selection logic cannot confuse it with another tool. A tool named `query_database` is too broad — the agent cannot reliably choose between PostgreSQL, MongoDB, and DuckDB if the tool descriptions overlap. A tool named `postgres_query_yelp_transactions` is scoped correctly.

**Why broad tools cause failures.** When tool descriptions are vague or overlapping, the agent selects tools based on surface-level pattern matching. A query about "customer data" might invoke the MongoDB tool when the correct answer is in PostgreSQL, or vice versa. This produces DAB Failure Category 1 (multi-database routing failure) not because the agent lacks capability but because the tool surface gave it no reliable way to choose.

**The 40+ tool pattern from Claude Code.** Claude Code uses many narrowly scoped tools rather than a few broad ones. Each tool has: a name that is a verb-noun pair specific to one operation (`read_file`, `run_bash`, `search_files`); a description that states exactly what it operates on and what it returns; explicit parameter types with narrow ranges. The agent's tool-selection logic is only as good as the specificity of the tool descriptions it reads.

**Applying this to Oracle Forge `tools.yaml`.** Each database in DAB should have its own set of tools, not a shared generic query tool. Minimum tool set:

- `postgres_query` — executes SQL against PostgreSQL databases; returns rows as JSON
- `mongo_aggregate` — executes MongoDB aggregation pipelines; returns documents as JSON
- `sqlite_query` — executes SQL against SQLite databases; returns rows as JSON
- `duckdb_query` — executes analytical SQL against DuckDB; returns columnar result as JSON
- `cross_db_merge` — merges result sets from two database tools on a specified key after format resolution

**Tool description quality test.** For each tool in `tools.yaml`, ask: if the agent reads only this description, will it call this tool and not another for its intended query type? If the answer is "maybe," the description is too vague. Rewrite it until the answer is "yes, unambiguously."

---

**Injection test question:** Why does Claude Code use 40+ narrowly scoped tools rather than a small number of broad tools, and how does this apply to configuring `tools.yaml` for the Oracle Forge agent?

**Expected answer:** Narrow tool scoping ensures the agent's tool-selection logic can unambiguously choose the correct tool for each operation. Broad or overlapping tool descriptions cause routing errors — the agent pattern-matches on surface keywords and picks the wrong tool. For Oracle Forge, each database type (PostgreSQL, MongoDB, SQLite, DuckDB) must have its own distinct tool with a description specific enough to prevent confusion, plus a separate `cross_db_merge` tool for joining results across systems.