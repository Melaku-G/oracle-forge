# Self-Correcting Execution Loop

Here is how this works.

The self-correcting execution loop is the mechanism by which the Oracle Forge agent recovers from query failures without surfacing errors to the user. It is described in both the Claude Code architecture (closed-loop correction) and the OpenAI data agent writeup (closed-loop self-correction). Both converge on the same pattern — the agent must diagnose the failure type before deciding how to recover.

**The loop has four steps.**

**Step 1 — Execute.** The agent sends a query to the appropriate database tool and receives a result or an error.

**Step 2 — Diagnose.** If the result is an error or is suspiciously empty (zero rows when rows are expected), the agent classifies the failure into one of four types: (a) wrong database routed — the table does not exist in the queried database; (b) join key format mismatch — the join returned zero rows despite both tables containing the entity; (c) query syntax error — the SQL or aggregation pipeline is malformed for this database dialect; (d) data quality issue — the query ran correctly but the data contains nulls, duplicates, or unexpected formats that corrupt the result.

**Step 3 — Recover.** Each failure type has a specific recovery action: (a) re-route to the correct database; (b) call `resolve_join_key()` and retry the join; (c) rewrite the query in the correct dialect; (d) add a cleaning step (null filter, deduplication) and retry.

**Step 4 — Log.** Whether recovery succeeded or failed, the agent writes an entry to `kb/corrections/corrections_log.md`: what query was attempted, what failure was diagnosed, what recovery was applied, and whether it worked. This is the autoDream consolidation input — it feeds the self-learning loop.

**What "without surfacing errors" means.** The user should never see a raw database error message. If the agent cannot recover after two retry attempts, it returns a structured response: "I was unable to complete this query. The failure was [diagnosis]. You may want to check [specific thing]." This is more useful than a stack trace and does not require the user to understand database internals.

**Harness integration.** The evaluation harness must capture the full execution trace including retry attempts. A query that required two retries before succeeding is a pass@1 only if it succeeded on the first attempt of the trial. Retries within a single trial do not affect the pass@1 score but are logged for diagnosis.

---

**Injection test question:** An agent joins PostgreSQL and MongoDB on customer ID and gets zero rows. Walk through the four steps of the self-correction loop for this failure.

**Expected answer:** Step 1 — execute the join, receive zero rows. Step 2 — diagnose: zero rows on a join is a join key format mismatch signal (not a routing error, because both databases were reached). Step 3 — recover: call `resolve_join_key()` to convert the PostgreSQL integer ID to the MongoDB string format, then retry the join. Step 4 — log the mismatch, the format conversion applied, and whether the retry succeeded in `kb/corrections/corrections_log.md`.