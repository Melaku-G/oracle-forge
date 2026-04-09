# OpenAI In-House Data Agent: Context Layer Architecture

Here is how this works.

OpenAI's internal data agent uses a six-layer context architecture to answer questions against large-scale enterprise data (reportedly 70,000+ tables). The bottleneck is not query generation — it is supplying the agent with the right context before any query is written. Each layer addresses a different type of ignorance the agent would otherwise have.

**Layer 1 — Schema and metadata index.** All connected databases are pre-indexed: table names, column names, types, and row counts are loaded before the agent answers its first question. The agent never discovers schema at query time.

**Layer 2 — Table enrichment via Codex.** Identified as the hardest sub-problem. A secondary model (Codex) generates natural-language descriptions of what each table contains and what business questions it can answer. This is how the agent knows that `txn_ledger` means "revenue transactions" without being told.

**Layer 3 — Institutional and domain knowledge.** What "revenue" means in this organisation's data model. Which tables are authoritative versus deprecated. Fiscal year boundaries. Status code meanings. This layer is the equivalent of what a new analyst learns in their first month.

**Layer 4 — Closed-loop self-correction.** When a query fails or returns a suspicious result, the agent diagnoses the failure type (wrong table, bad join key, type mismatch) and retries without surfacing the error to the user.

**Layer 5 — Interaction memory.** Corrections the user has made in previous sessions, successful query patterns, user preferences. This is the self-learning loop — the agent improves from its own history.

**Layer 6 — Retrieved examples.** At query time, semantically similar past queries with their confirmed correct answers are injected. The agent sees "here is how a similar question was answered before."

For the Oracle Forge challenge, the minimum requirement is three demonstrably working layers: schema/metadata (Layer 1), institutional knowledge (Layer 3), and interaction memory / corrections log (Layer 5).

---

**Injection test question:** What does OpenAI's data agent identify as the hardest sub-problem in its context architecture, and which layer addresses it?

**Expected answer:** Table enrichment — generating natural-language descriptions of what each table contains — is the hardest sub-problem. It is addressed by Layer 2, powered by Codex.