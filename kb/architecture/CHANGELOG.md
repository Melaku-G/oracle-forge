# CHANGELOG — kb/architecture/

All changes to architecture knowledge base documents are recorded here.
Format: `[DATE] | [DOCUMENT] | [CHANGE TYPE] | [WHAT CHANGED] | [REASON]`
Change types: ADDED | UPDATED | REMOVED | INJECTION-TEST-RESULT

Maintained by: Intelligence Officers
Reviewed at: every mob session

---

## 2026-04-08

| Date | Document | Change Type | What Changed | Reason |
|------|----------|-------------|--------------|--------|
| 2026-04-08 | `claude_code_memory.md` | ADDED | Initial document created. Covers three-layer MEMORY.md architecture (index → topic files → session transcripts), injection test added. | Required KB v1 deliverable before Drivers write first agent code. |
| 2026-04-08 | `openai_context_layers.md` | ADDED | Initial document created. Covers all six context layers, identifies Layer 2 (table enrichment) as hardest sub-problem, injection test added. | Required KB v1 deliverable. |
| 2026-04-08 | `autodream_consolidation.md` | ADDED | Initial document created. Covers consolidation trigger conditions, three entry types (facts, corrections, patterns), link to corrections log. | Required KB v1 deliverable. |
| 2026-04-08 | `tool_scoping.md` | ADDED | Initial document created. Covers Claude Code 40+ narrow-tool philosophy, tool description quality test, minimum tool set for Oracle Forge. | Required KB v1 deliverable. Needed before Drivers configure tools.yaml. |
| 2026-04-08 | `self_correction_loop.md` | ADDED | Initial document created. Covers four-step loop (execute → diagnose → recover → log), four failure types and recovery actions, harness integration note. | Required KB v1 deliverable. |
| 2026-04-08 | `dab_failure_modes.md` | ADDED | Initial document created. Covers all four DAB failure categories with detection signals and fix directions. | Required KB v1 deliverable. Must exist before first probe is run. |
| 2026-04-08 | `ddb_failure_modes.md` | ADDED | Initial document created. Covers four DuckDB-specific failure modes: wrong DB routed, dialect mismatch, schema assumption mismatch, wrong MCP tool called. | Required KB v1 deliverable. DuckDB is one of four DAB database types. |

---

## Instructions for Future Entries

- Add a row every time any document in this directory is created, updated, or removed.
- If an injection test fails after an agent update, add an INJECTION-TEST-RESULT row describing what changed and how the document was revised.
- If a document becomes outdated because the agent or database changed, mark it REMOVED and explain why — do not silently delete without a log entry.
- Growth without removal is noise. If a document fails its injection test twice in a row, remove it and log the removal here.