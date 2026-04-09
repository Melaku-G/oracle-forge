# autoDream Memory Consolidation Pattern

Here is how this works.

autoDream is the memory consolidation pattern used in the Claude Code architecture. It runs automatically at the end of a session (or when context pressure is detected) and converts raw session transcripts into structured, reusable memory entries. The name comes from the analogy to sleep-phase memory consolidation in humans — the system "dreams" over what happened and extracts durable knowledge from it.

**The problem it solves.** Raw session transcripts are too large to inject into future context windows whole. But discarding them loses everything the agent learned. autoDream sits between the two extremes: it compresses transcripts into structured summaries that are small enough to inject but specific enough to be useful.

**How consolidation works.** At session end, the agent reviews its own transcript and extracts three types of entries: (1) facts learned — new schema details, confirmed join key formats, domain term definitions; (2) corrections received — queries that failed and the fix that worked; (3) successful patterns — query structures that produced correct results and can be reused.

**Output format.** Each consolidated entry is written to the corrections log (`kb/corrections/corrections_log.md`) or the relevant domain KB document. The MEMORY.md index is updated to point to the new entries. Raw transcripts are stored but not injected — only the consolidated summaries are loaded at session start.

**Trigger conditions.** Consolidation runs: (a) at the end of every mob session, (b) when the context window is more than 70% full, (c) manually when a Driver observes a significant failure or breakthrough.

**What this means for Oracle Forge.** After every mob session, the Driver on keyboard must run the consolidation step before closing the session. New entries go into `kb/corrections/corrections_log.md`. Intelligence Officers review and promote entries to the appropriate KB document (domain, architecture, or evaluation) before the next session starts.

**The compounding effect.** Each session starts with a richer context than the last. The agent does not repeat mistakes it has already made and had consolidated. This is the mechanism behind measurable score improvement between Week 8 and Week 9.

---

**Injection test question:** When does autoDream consolidation trigger, and what three types of entries does it extract from a session transcript?

**Expected answer:** Consolidation triggers at session end, at 70%+ context window fill, or manually. It extracts: (1) facts learned (schema, join key formats, domain terms), (2) corrections received (failed queries and their fixes), and (3) successful query patterns that can be reused.