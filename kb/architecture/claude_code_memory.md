# Claude Code — Architectural Patterns

> Source-verified analysis of key architectural patterns in the Claude Code codebase.

---

## Table of Contents

1. [Three-Layer Memory Architecture](#1-three-layer-memory-architecture)
2. [Tool Scoping Philosophy](#2-tool-scoping-philosophy)
3. [Worktree Isolation & Parallelism](#3-worktree-isolation--parallelism)
4. [Self-Correction Loop](#4-self-correction-loop)

---

## 1. Three-Layer Memory Architecture

Claude Code uses a three-layer memory system to persist knowledge across sessions.

### Layer 1 — MEMORY.md (The Index)

| Property | Value |
|---|---|
| File | `src/memdir/memdir.ts` |
| Constant | `ENTRYPOINT_NAME = 'MEMORY.md'` |
| Max lines | 200 (`MAX_ENTRYPOINT_LINES`) |
| Max bytes | 25,000 (`MAX_ENTRYPOINT_BYTES`) |

- Loaded automatically into **every** session context
- Contains **one-line pointers only** — no actual memory content is stored here
- Overflow is truncated by `truncateEntrypointContent()` with a warning appended

```
- [user_role.md](user_role.md) — user is a senior backend engineer focused on Go
- [feedback_testing.md](feedback_testing.md) — always use real DB, never mocks
```

### Layer 2 — Topic Files (`.claude/memory/*.md`)

Defined in `src/memdir/memoryTypes.ts` — four typed categories:

| Type | Purpose |
|---|---|
| `user` | Role, preferences, knowledge level |
| `feedback` | Corrections and confirmed approaches |
| `project` | Ongoing work, goals, incidents, deadlines |
| `reference` | Pointers to external systems (Linear, Grafana, etc.) |

Each file uses YAML frontmatter:

```yaml
---
name: Testing approach
description: Use real DB, never mocks — prevents prod/test divergence
type: feedback
---

Always hit a real database in tests. Mocks masked a broken migration last quarter.

**Why:** Prior incident where mock/prod divergence caused a failed prod migration.
**How to apply:** Never use jest.mock() or equivalent for DB calls in this repo.
```

Files older than 1 day are flagged stale by `memoryFreshnessText()` in `src/memdir/memoryAge.ts`. Up to 200 files are scanned (newest-first) by `scanMemoryFiles()` in `src/memdir/memoryScan.ts`.

### Layer 3 — Session Transcripts (JSONL)

- Stored per-project in `getProjectDir(getOriginalCwd())`
- **Never loaded directly into context**
- Only accessed by the autoDream consolidation process via `listSessionsTouchedSince()`

### How autoDream Consolidates Sessions

Source: `src/services/autoDream/autoDream.ts`

autoDream is a background process that distills session learnings into topic files. It runs through four gates before doing any work:

```
Session ends
     │
     ▼
Gate 1: Time check ──── < 24h since last run? ──► Skip
     │
     ▼
Gate 2: Scan throttle ── scanned < 10min ago? ──► Skip
     │
     ▼
Gate 3: Session count ── < 5 new sessions? ──────► Skip
     │
     ▼
Gate 4: Mutex lock ───── another process running? ► Skip
     │
     ▼
Fork sub-agent (4 phases: orient → gather → consolidate → prune/index)
     │
     ├── Success → advance lock mtime (= new lastConsolidatedAt)
     └── Failure → rollbackConsolidationLock(priorMtime) → retry next session
```

The forked sub-agent (`runForkedAgent()` in `src/utils/forkedAgent.ts`) is constrained to:
- Read-only Bash
- FileEdit/FileWrite **only within the memory directory**

Thresholds (`minHours`, `minSessions`) are remotely configurable via GrowthBook flag `tengu_onyx_plover`.

### Knowledge Check

> **Q:** What are the three memory layers and the role of MEMORY.md?

**A:** (1) **MEMORY.md** — index only, 200-line/25KB cap, loaded every session. (2) **Topic files** — typed `.md` files with YAML frontmatter in `.claude/memory/`. (3) **Session JSONL transcripts** — raw session data, never loaded directly, only scanned by autoDream. MEMORY.md is an index — it holds one-line pointers to topic files, never content itself.

---

## 2. Tool Scoping Philosophy

### How Many Tools?

`getAllBaseTools()` in `src/tools.ts:193` is the source of truth. There are **40 tool directories** in `src/tools/` (excluding `shared/`, `testing/`, `utils.ts`).

**Always-on core tools:**

| Tool | Purpose |
|---|---|
| `AgentTool` | Spawn sub-agents |
| `BashTool` | Execute shell commands |
| `GlobTool` | File pattern matching |
| `GrepTool` | Content search |
| `FileReadTool` | Read files |
| `FileEditTool` | Edit files |
| `FileWriteTool` | Write files |
| `WebFetchTool` | Fetch URLs |
| `WebSearchTool` | Search the web |
| `TodoWriteTool` | Manage task lists |
| `AskUserQuestionTool` | Ask the user a question |
| `EnterPlanModeTool` | Enter planning mode |
| `SkillTool` | Invoke user-defined skills |

Additional tools are gated by feature flags or `USER_TYPE === 'ant'` (Anthropic-internal only).

### What Defines a Tool's Boundary?

The `Tool<Input, Output, P>` interface in `src/Tool.ts:362` defines the contract. Every tool must implement:

```
Tool
 ├── inputSchema          — Zod schema; strict typed validation
 ├── isReadOnly(input)    — Can this run in parallel with other reads?
 ├── isDestructive(input) — Is this irreversible? (default: false)
 ├── checkPermissions()   — Tool-specific permission logic
 ├── validateInput()      — Pre-permission validation; error goes to model
 └── call()               — The implementation; isolated from other tools
```

`buildTool()` (line 783) applies **fail-closed defaults** where methods are omitted — security-sensitive tools must explicitly override.

### How Concurrency Works

`src/services/tools/toolOrchestration.ts` partitions tool calls before execution:

```
Tool calls in a batch
        │
        ▼
  Is isReadOnly() true for all?
        │
   Yes  │  No
        │   └─► runToolsSerially() — one at a time
        ▼
  runToolsConcurrently() — all in parallel
        │
        ▼
  Context mutations queued and applied in order
```

### Knowledge Check

> **Q:** What two methods on the Tool interface determine parallel execution eligibility?

**A:** `isReadOnly(input)` and `isConcurrencySafe(input)`. The `toolOrchestration.ts` `partitionToolCalls()` uses these to group calls — consecutive read-only tools run concurrently; the first non-read-only tool forces a serial batch boundary.

---

## 3. Worktree Isolation & Parallelism

Source: `src/utils/worktree.ts`, `src/utils/forkedAgent.ts`

### Branch Isolation via Git Worktrees

Each sub-agent gets its own isolated git worktree:

```
.claude/
  worktrees/
    feature+auth/        ← slug "feature/auth" flattened to "feature+auth"
    bugfix+login/
    refactor+db/
```

Key mechanics in `getOrCreateWorktree(repoRoot, slug)`:

| Mechanism | Detail |
|---|---|
| Path | `.claude/worktrees/<slug>` |
| Branch name | `worktree-<slug>` (via `-B` flag — resets if exists) |
| Slug flattening | `/` → `+` to avoid D/F conflicts in git refs |
| Path traversal guard | `validateWorktreeSlug()` rejects `..` — each segment must match `/^[a-zA-Z0-9._-]+$/` |
| Fast-resume | `readWorktreeHeadSha()` reads `.git` pointer directly (~0ms vs ~15ms spawn) |

### Process-Level Isolation

`createSubagentContext()` in `src/utils/forkedAgent.ts:345` isolates all mutable state:

| State | Isolation method |
|---|---|
| `readFileState` | Cloned — no shared read cache |
| `abortController` | New child (parent abort propagates; child abort does not) |
| `setAppState` | No-op — sub-agent cannot mutate parent's React state |
| `contentReplacementState` | Cloned — stable cache-key decisions |
| `queryTracking` | New `chainId` + incremented `depth` |

### How Results Are Merged Back

There is **no automatic merge**. The pattern is task-scoped isolation with human-directed merge:

- `WorktreeSession` returns `{ originalBranch, worktreeBranch, worktreePath }` — caller creates the PR or runs `git merge`
- For forked sub-agents (e.g., autoDream): results returned as `ForkedAgentResult.messages`; success advances the consolidation lock mtime; failure calls `rollbackConsolidationLock(priorMtime)`

### Knowledge Check

> **Q:** What prevents two concurrent worktree agents from stepping on the same git branch?

**A:** Each worktree gets a unique `worktree-<slug>` branch. The slug is validated to reject `..` and flattened (`/` → `+`). Sub-agent context is fully isolated — cloned `readFileState`, no-op `setAppState`, new abort controller — via `createSubagentContext()` in `forkedAgent.ts`.

---

## 4. Self-Correction Loop

Claude Code implements self-correction at four distinct layers.

### Layer 1 — API Retry with Model-Swapping

Source: `src/services/api/withRetry.ts`

The `withRetry<T>()` generator handles API-level failures with targeted fixes:

| Error | Fix Applied |
|---|---|
| 401 Unauthorized | `handleOAuth401Error()` → refresh token → new client |
| 403 Token revoked | `clearApiKeyHelperCache()` → new client |
| Context overflow (400) | `parseMaxTokensContextOverflowError()` → compute `adjustedMaxTokens` → retry |
| 529 Overloaded (3x) | `FallbackTriggeredError` → model downgrade |
| ECONNRESET / EPIPE | `disableKeepAlive()` → reconnect |

Backoff: exponential with jitter (500ms base → 32s max). `CLAUDE_CODE_UNATTENDED_RETRY` mode retries indefinitely with a 5-minute cap and heartbeat messages every 30s.

### Layer 2 — Tool Error Feedback

Source: `src/services/tools/toolExecution.ts`

```
Tool call received
       │
       ▼
validateInput()  ──── fail ──► <tool_use_error> returned as user message
       │                        Model reads error, diagnoses, retries
       ▼
checkPermissions()
       │
       ▼
call() ──────────── fail ──► <tool_use_error> returned as user message
```

Special case — deferred tool with missing schema: `buildSchemaNotSentHint()` appends an explicit recovery instruction:
> *"This tool's schema was not sent to the API. Call ToolSearch with `select:<toolname>`, then retry."*

### Layer 3 — Verification Agent

Source: `src/tools/AgentTool/built-in/verificationAgent.ts`

A dedicated `agentType: 'verification'` sub-agent that checks implementation correctness:

```
Implementation complete
        │
        ▼
Verification agent spawned
 ├── Runs: builds, tests, linters, type-checkers
 ├── Runs: adversarial probes (concurrency, boundary values, idempotency)
 └── Cannot modify files (FileEditTool, FileWriteTool in disallowedTools)
        │
        ▼
Structured report:
  ### Check: <description>
  **Command run:** <command>
  **Output observed:** <output>
  **Result: PASS / FAIL**
        │
        ▼
Single verdict: PASS | FAIL | PARTIAL
(PARTIAL only for environmental limitations, never uncertainty)
```

Anti-rationalization rule in the system prompt: **"Reading code is not verification — run it."**

### Layer 4 — autoDream Failure Rollback

In `autoDream.ts`, a failed consolidation fork calls `rollbackConsolidationLock(priorMtime)` — rewinding the lock file's mtime so the time-gate re-opens on the next session. The 10-minute scan throttle provides backoff.

### Full Cycle Summary

```
Failure detected
      │
      ▼
Diagnose (classify error type, status code, schema mismatch)
      │
      ▼
Fix (refresh auth / adjust params / load schema / downgrade model)
      │
      ▼
Verify (retry with corrected params OR run verification agent)
      │
      ├── Pass → continue
      └── Fail → backoff → repeat (up to max retries)
```

### Knowledge Check

> **Q:** When a deferred tool's schema wasn't sent to the API and validation fails, what recovery hint is injected?

**A:** `buildSchemaNotSentHint()` appends: call `ToolSearch` with `select:<toolname>` to load the schema, then retry. Without the schema, parameters are serialized as strings and fail Zod client-side parsing — the hint closes the self-correction loop by giving the model an exact recovery path.

---

*All findings are source-verified against `/Users/aman/Downloads/claude-code-source-code-full-main`. No guessing — if a pattern was not found in source, it is noted as such.*
