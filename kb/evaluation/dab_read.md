# DAB Evaluation Method: pass@1, Trials, Submission

Here is how this works.

DataAgentBench evaluates agents using a specific protocol. Understanding the protocol exactly is required before running any evaluation — deviating from it produces scores that cannot be compared to the leaderboard.

**The query set.** DAB contains 54 queries across 12 datasets. The datasets span 9 domains including retail, telecom, healthcare, finance, and anti-money laundering. Each query is tagged with the database types it requires and the failure categories it tests.

**The scoring method: pass@1.** A query is scored as passed if the agent returns the correct answer on its first attempt in a given trial. There is no partial credit. The pass@1 score is the fraction of queries answered correctly across all trials. The current best score on DAB is 38% pass@1, achieved by Gemini 2.5 Pro — this is the baseline to beat.

**Trial count.** Each query must be run a minimum of 5 times (n ≥ 5 trials). This accounts for non-determinism in LLM outputs. The reported pass@1 score is computed across all trials for all queries.

**Running the evaluation.** The DAB repository provides `eval/run_benchmark.py`. The agent must accept a structured input `{question, available_databases, schema_info}` and return `{answer, query_trace, confidence}`. The query trace is required — a result without a trace is not a valid submission.

**Submission method.** Results are submitted as a GitHub Pull Request to `ucbepic/DataAgentBench`. The PR must include: (1) a results JSON file at `submission/team_[name]_results.json`, (2) an `AGENT.md` describing the agent architecture, key design decisions, what worked, and what did not. The PR title format is `[Team Name] — TRP1 FDE Programme, April 2026`.

**Harness requirement.** Teams must also maintain an internal evaluation harness that produces scores at any point in development — not just at final submission. The harness must show measurable score improvement between the Week 8 baseline and the final submission.

---

**Injection test question:** What is the minimum number of trials per query required for a valid DAB submission, and what does pass@1 mean in this context?

**Expected answer:** A minimum of 5 trials per query (n ≥ 5). Pass@1 means the agent must return the correct answer on its first attempt within each trial; there is no partial credit, and the score is the fraction of queries passed across all trials.