# DAB Benchmark PR Submission Record

**Target repository:** ucbepic/DataAgentBench  
**Submission date:** 2026-04-18  
**Submitted by:** Natnael Alemseged (Driver 2) on behalf of Team Falcon

---

## PR Title

```
[Team Falcon] - TRP1 FDE Programme, April 2026
```

## PR Body

```markdown
## Oracle Forge — Team Falcon

**Agent name:** Oracle Forge

**Backbone LLM:** gemini/gemini-2.0-flash-001 via OpenRouter (OpenAI-compatible API)

**Dataset hints used:** Yes — three-layer context system:
- Layer 1 (schema): `agent/AGENT.md` — full schema for 8 DAB datasets, join key rules, behavioral rules
- Layer 2 (domain): `kb/domain/` — Yelp field map, join key glossary, query skeletons, anti-patterns (15 entries)
- Layer 3 (corrections): `kb/corrections/corrections_log.md` — 32 structured failure entries read at session start

**Additional notes:**
- Self-correcting execution loop: 4 failure categories (syntax_error, join_key_format, wrong_table, domain_knowledge_gap), retry up to 3×
- Best result: 100% pass@1 on Yelp (7/7 queries, 5 trials), 33% on Bookreview
- Architecture: MCP Toolbox JSON-RPC server routing to PostgreSQL, MongoDB, SQLite, DuckDB
- Code: https://github.com/Natnael-Alemseged/oracle-forge
```

---

## Submission Evidence

- Results JSON: `results/dab_submission.json`
- Score progression log: `eval/score_log.md` (66 dated run entries, Apr 11–18 2026)
- Best yelp benchmark: `eval/run_logs/benchmark_yelp_20260415_183320.json` (7/7 queries, 5 trials, 100% pass@1)
- Evaluation harness: `eval/run_benchmark.py`

## Datasets Submitted

| Dataset | Queries | Best pass@1 | Runs |
|---------|---------|-------------|------|
| yelp | 7 | 100% | 5 |
| bookreview | 3 | 33% | 1 |
| GITHUB_REPOS | 4 | 0% | 1 |
| stockmarket | 5 | 0% | 1 |

**Total queries submitted:** 19 of 54 DAB queries (datasets where DB connections were established and agent ran to completion).

## Notes on Remaining Datasets

The following DAB datasets were attempted but full benchmark files could not be generated due to DB loading time constraints:
- crmarenapro (13 queries) — partial runs in `eval/run_logs/`; best 2/13 (15%)
- DEPS_DEV_V1 (2 queries) — partial runs; best 1/2 (50%)  
- PANCANCER_ATLAS (3 queries) — 0% (requires Git LFS 280MB pull)
- googlelocal (4 queries) — 0% (connection issues)
- music_brainz_20k and remaining datasets — not reached within sprint timeline
