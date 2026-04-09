# IO → Driver Probe Handoff Template

**Purpose:** Intelligence Officers use this template to hand off a specific adversarial probe to Drivers for execution during a mob session. One handoff document per probe. File naming: `handoff_[PROBE_ID]_[date].md`.

---

## Handoff: [PROBE ID]

**Date:** YYYY-MM-DD

**Prepared by:** [IO name]

**Target mob session:** [e.g., Week 9 Day 2]

---

### Probe Details

**Probe ID:** (e.g., Probe 003)

**Query to run against the agent:**
> (Paste the exact natural language query here — do not paraphrase)

**Failure category:** (One of: Multi-database routing failure | Ill-formatted join key mismatch | Unstructured text extraction failure | Domain knowledge gap)

---

### KB Context to Inject

**KB document to load into agent context before running this probe:**
(Filename, e.g., `kb/domain/yelp_schema.md`)

**Reason this document is relevant:**
(One sentence: what knowledge does this document give the agent that is needed to handle this query correctly?)

**Additional KB documents (if any):**
(List filenames)

---

### Expected Failure

**What the agent will likely do wrong:**
(Be specific — describe the incorrect output, not just the category name)

**How to confirm the failure occurred:**
(What to look for in the query trace or output that proves this failure mode was triggered)

---

### Fix to Apply

**Proposed fix:**
(Specific and actionable: e.g., "Add routing rule to AGENT.md", "Update join_key_resolver.py to handle USR- prefix", "Add 'active business' definition to kb/domain/yelp_schema.md")

**KB update required?** Yes / No
If yes: (Which document, what to add)

---

### Post-Fix Validation

**Post-fix score expected:** (e.g., 1.0 if query should now pass consistently)

**Regression check:** Confirm the fix does not break these previously-passing probes: (list Probe IDs)

---

**Driver sign-off:** (Driver initials + date after probe is run and result logged in corrections_log.md)