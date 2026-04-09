# Agent Corrections Log

**Purpose:** Running structured log of agent failures. Written by Drivers after every observed failure. Read by the agent at session start. This is the self-learning loop — the mechanism by which the agent improves from its own errors without retraining.

**Format:** Each row documents one failure instance. The Fix Applied column must be specific enough to reproduce the fix. Post-Fix Score is the pass@1 score on this query after the fix was applied.

| ID | Date | Query | Failure Category | What Was Expected | What Agent Returned | Fix Applied | Post-Fix Score |
|----|------|-------|-----------------|-------------------|---------------------|-------------|----------------|
| COR-001 | 2026-04-08 | "Which customers generated >$5k revenue AND >3 support tickets last quarter?" | Multi-database routing failure | Agent routes revenue sub-query to PostgreSQL `transactions` table and ticket sub-query to MongoDB `support_tickets` collection, then merges on resolved customer ID | Agent queried only PostgreSQL; returned revenue data with no ticket count; join to MongoDB never attempted | Added explicit routing rule to AGENT.md: queries containing "support tickets" or "CRM" must always route a sub-query to MongoDB before attempting result merge. Updated `tools.yaml` to expose `mongo_support_query` tool with higher priority for support-domain terms. | 1.0 |

---

**Instructions for Drivers:**
1. After every observed agent failure during a mob session, add a row immediately — do not batch.
2. The "What Agent Returned" column must describe the actual output, not a summary of the failure category.
3. Intelligence Officers review this log before each mob session and update `kb/architecture` or `kb/domain` documents if the failure reveals a gap in the Knowledge Base.
4. Entries are never deleted — if a fix is later superseded, add a new row referencing the old COR ID.