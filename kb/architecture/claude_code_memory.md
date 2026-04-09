# Claude Code Three-Layer Memory System

> KB v1 — Architecture Layer | Oracle Forge
> Purpose: Give the agent working knowledge of how production AI agents manage memory
> so it applies the same patterns to its own context management during DAB queries.

---

## The Core Problem This Solves

A data agent answering complex queries across multiple databases cannot load everything
into context at once. It must decide what to load, when to load it, and what to discard.
Claude Code solved this at production scale with 512,000 lines of TypeScript.
We apply the same three-layer architecture to Oracle Forge.

---

## Layer 1: MEMORY.md — The Index File

A single file loaded at the start of every session.
It is NOT a content file. It is a pointer file — a table of contents.
It tells the agent what knowledge exists and where to find it.
The agent reads this first, then decides which topic files to load for the current query.

Example structure:
```
# Agent Memory Index
- schema_overview.md     → schemas for all 12 DAB datasets
- join_key_glossary.md   → cross-database join key format mismatches
- domain_terms.md        → business term definitions not in schemas
- corrections_log.md     → past failures and their fixes (always load)
```

Oracle Forge equivalent: AGENT.md loaded at session start.
AGENT.md lists all KB files and what each one contains.
A query about stock volatility → agent loads domain_terms.md.
A query about bookreview → agent loads join_key_glossary.md.

---

## Layer 2: Topic Files — On-Demand Knowledge

Individual markdown files, each covering exactly one domain.
Loaded only when the agent determines it needs that knowledge.
Maximum ~400 words per file. Written as declarative facts, not explanations.

Design rule: each file must be self-contained.
Paste a topic file into a fresh LLM context with no other information.
The LLM must answer questions about that topic correctly from the file alone.
If it cannot, the file is too vague and must be rewritten.

Oracle Forge topic files:
- kb/domain/schema_overview.md → loaded for any query (always needed)
- kb/domain/join_key_glossary.md → loaded when query involves cross-database join
- kb/domain/domain_terms.md → loaded when query uses business terminology
- kb/corrections/corrections_log.md → loaded at session start (always needed)

---

## Layer 3: Session Transcripts — Searchable History

JSONL logs of past agent sessions stored on disk.
The agent searches these semantically to recall past corrections and successful patterns.
In Claude Code: ~/.claude/projects/<hash>/sessions/<session-id>.jsonl

Oracle Forge equivalent: kb/corrections/corrections_log.md
Structured log of past failures and their fixes.
Agent reads it at session start to avoid repeating known mistakes.

---

## autoDream Consolidation — Memory Compression

Background subagent that runs when context fills up or on /dream command.
Reads recent session transcripts → produces compressed summaries → replaces verbose history.

Trigger conditions:
1. Token count exceeds threshold (context window filling up)
2. Explicit /dream command
3. Session end (consolidate before closing)

Output: compact summary prepended to session, old messages marked [compacted].

Oracle Forge application:
When corrections_log.md exceeds ~2000 words:
- Entries marked "fixed and confirmed" → compress to one-line summaries in ## Resolved
- Active entries (recent failures, unresolved patterns) → keep in full detail

---

## Oracle Forge Mapping Table

| Claude Code Component     | Oracle Forge Equivalent              |
|---------------------------|--------------------------------------|
| MEMORY.md index file      | AGENT.md loaded at session start     |
| Topic files (on-demand)   | kb/domain/*.md files                 |
| Session transcripts       | kb/corrections/corrections_log.md    |
| autoDream consolidation   | Periodic compression of corrections  |
| conversation_search tool  | utils/multi_pass_retriever.py        |
