# KB Architecture CHANGELOG

> Records all additions, modifications, and injection test results for KB v1.
> Every document must pass injection test before being marked COMMITTED.

---

## v1.0 — 2026-04-08 (Initial KB v1 Release)

### Added

#### claude_code_memory.md
- Content: Three-layer memory system (index, topic files, session transcripts) + autoDream
- Injection test Q1: "What is Layer 1 in Claude Code memory?"
  Expected: pointer/index file, not content file
  Status: [x] PASS — 2026-04-08
- Injection test Q2: "When does autoDream trigger?"
  Expected: token threshold exceeded OR /dream command OR session end
  Status: [x] PASS — 2026-04-08
- Injection test Q3: "What is the Oracle Forge equivalent of session transcripts?"
  Expected: kb/corrections/corrections_log.md
  Status: [x] PASS — 2026-04-08
- Injection test Q4: "Why are topic files limited to ~400 words?"
  Expected: must be self-contained, injected alone
  Status: [x] PASS — 2026-04-08
- Tested by: IO — 2026-04-08 (all 4 confirmed)

#### openai_data_agent_context.md
- Content: Six-layer context architecture, table enrichment problem, self-learning loop
- Injection test Q1: "What is the hardest sub-problem in OpenAI's data agent?"
  Expected: finding the right table, not writing the query
  Status: [x] PASS — 2026-04-08
- Injection test Q2: "What should the agent do when a cross-database join returns zero rows?"
  Expected: investigate join key format mismatch, do not return empty result
  Status: [x] PASS — 2026-04-08
- Injection test Q3: "What score does PromptQL achieve vs raw Gemini-3-Pro on DAB?"
  Expected: 51% vs 38% — 13 point gap from context engineering alone
  Status: [x] PASS — 2026-04-08
- Injection test Q4: "What is Layer 3 and its Oracle Forge equivalent?"
  Expected: Organizational Context Layer → kb/domain/domain_terms.md
  Status: [x] PASS — 2026-04-08
- Tested by: IO — 2026-04-08 (all 4 confirmed)

#### self_correction_loop.md
- Content: FM1-FM4 taxonomy, plausibility checks, dataset-specific checks, logging requirement
- Injection test Q1: "What does FM2 mean and give one example from DAB?"
  Expected: incorrect plan — even perfect execution cannot produce correct answer
  Status: [x] PASS — 2026-04-08
- Injection test Q2: "What is the most common failure mode in DAB?"
  Expected: FM2+FM4 together = 85%, FM3 = 15%
  Status: [x] PASS — 2026-04-08
- Injection test Q3: "What should the agent check after every cross-database join?"
  Expected: row count — zero=key mismatch, too high=cartesian, NULL=wrong column
  Status: [x] PASS — 2026-04-08
- Injection test Q4: "Specific fix for bookreview zero-row join?"
  Expected: strip bid_/bref_ prefixes, join on numeric suffix
  Status: [x] PASS — 2026-04-08
- Injection test Q5: "What is required after every failure in the self-correction loop?"
  Expected: log to corrections_log.md, format [failed]→[diagnosis]→[fix]→[result], within 2 hours
  Status: [x] PASS — 2026-04-08
- Tested by: IO — 2026-04-08 (all 5 confirmed)

#### tool_scoping_and_parallelism.md
- Content: One-tool-one-job principle, concurrency rules, MCP Toolbox pattern, 20% exploration rule
- Injection test Q1: "Can PostgreSQL and MongoDB queries run in parallel?"
  Expected: yes — queries to different databases are concurrency-safe
  Status: [x] PASS — 2026-04-08
- Injection test Q2: "What percentage of tool calls should be exploratory?"
  Expected: ~20% — less than 10% misses schema details, more than 25% wastes budget
  Status: [x] PASS — 2026-04-08
- Injection test Q3: "What is the MCP Toolbox pattern and what does it hide?"
  Expected: tools.yaml logical names, hides connection strings/passwords/paths
  Status: [x] PASS — 2026-04-08
- Injection test Q4: "Correct execution order for bookreview two-database query?"
  Expected: parallel DB queries first, then execute_python to merge
  Status: [x] PASS — 2026-04-08
- Tested by: IO — 2026-04-08 (all 4 confirmed)

#### dab_failure_modes.md
- Content: FM1-FM4 definitions with DAB examples, patents 0% explanation, quick reference table
- Injection test Q1: "Why does the patents dataset score 0% for all agents?"
  Expected: regex cannot handle varied natural language date formats; use dateutil/LLM
  Status: [x] PASS — 2026-04-08
- Injection test Q2: "What is the difference between FM3 and FM4?"
  Expected: FM3=wrong data source, FM4=wrong code on correct data
  Status: [x] PASS — 2026-04-08
- Injection test Q3: "Count of 50,000 when expecting 500 — what FM and fix?"
  Expected: FM4, many-to-many join, add deduplication
  Status: [x] PASS — 2026-04-08
- Injection test Q4: "Quick fix for FM1(no_tool_call)?"
  Expected: reduce scope, load from file path, simplify first step
  Status: [x] PASS — 2026-04-08
- Injection test Q5: "Competitive advantage of using dateutil for patents?"
  Expected: only agent in benchmark that solves patents queries
  Status: [x] PASS — 2026-04-08
- Tested by: IO — 2026-04-08 (all 5 confirmed)

---

## v1.1 — 2026-04-08 (AGENT.md added)

### Added

#### AGENT.md (kb/AGENT.md)
- Content: Memory index — always-load files, conditional load rules, 8 critical rules
- Injection test Q1: "Which files should the agent always load at session start?"
  Expected: corrections_log.md (first) + schema_overview.md
  Status: [x] PASS — 2026-04-08
- Injection test Q2: "Intraday volatility query — which additional file to load?"
  Expected: kb/domain/domain_terms.md — volatility is a business term
  Status: [x] PASS — 2026-04-08
- Injection test Q3: "List all 8 critical rules that are always active"
  Expected: all 8 rules including patents/dateutil, crmarenapro TRIM, bookreview prefixes,
            adj_close, word boundaries, parallel queries, 20% exploration
  Status: [x] PASS — 2026-04-08
- Tested by: IO — 2026-04-08 (all 3 confirmed)

---

## KB v1 COMPLETE — 2026-04-08

All 6 documents fully injection-tested and confirmed. KB v1 is ready to commit.

| Document | Tests | Result |
|---|---|---|
| claude_code_memory.md | Q1-Q4 | PASS |
| openai_data_agent_context.md | Q1-Q4 | PASS |
| self_correction_loop.md | Q1-Q5 | PASS |
| tool_scoping_and_parallelism.md | Q1-Q4 | PASS |
| dab_failure_modes.md | Q1-Q5 | PASS |
| AGENT.md | Q1-Q3 | PASS |

claude_code_memory.md Q3 + Q4 confirmed PASS — 2026-04-08. All documents fully tested.

## KB v1 FULLY COMPLETE — ALL TESTS PASSED — 2026-04-08

1. Open a FRESH LLM session (Claude.ai, ChatGPT, or Gemini — no prior context)
2. Paste ONLY the document text as your first message
3. Ask the test question listed above
4. Grade: PASS if answered correctly from document alone, FAIL if not
5. Update this CHANGELOG with result and your name + date
6. If FAIL: revise the document and re-test before committing

## Commit Policy

No KB document is committed to the team repository until:
- All injection tests for that document show PASS
- This CHANGELOG is updated with test results
- At least one other team member has reviewed the document
