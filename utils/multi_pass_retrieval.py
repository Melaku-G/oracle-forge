"""
multi_pass_retrieval.py
-----------------------
Utility for running multiple retrieval passes with different query vocabulary
against the agent's Knowledge Base, then deduplicating and merging the results.

Why this exists (from AI Agent Internals Probing Strategy doc):
  A single semantic retrieval pass will always miss edge cases where the user
  expresses the same concept with different vocabulary. For example, retrieving
  correction events with a single query for "user corrected" misses cases where
  the correction was phrased as intellectual disagreement ("that's not right,
  actually") rather than explicit error acknowledgement.

  The fix is multiple passes with different query vocabulary, then deduplication.

DAB Failure Categories addressed:
  - Domain knowledge gap (ensures KB entries are found regardless of how the
    query terms the domain concept)
  - Unstructured text extraction failure (finds relevant extraction patterns
    even when the query uses different vocabulary than the KB document)

Usage:
    from utils.multi_pass_retrieval import multi_pass_retrieve

    results = multi_pass_retrieve(
        query="find corrections where agent joined wrong database",
        kb_path="kb/corrections/corrections_log.md",
        pass_queries=[
            "wrong database routed",
            "multi-database routing failure",
            "agent queried only one database",
            "cross-database join failed",
        ]
    )
    # Returns deduplicated list of matching KB entries
"""

import re
from pathlib import Path
from typing import Callable


# ---------------------------------------------------------------------------
# Default vocabulary expansions per DAB failure category.
# Used when the caller does not provide explicit pass_queries.
# ---------------------------------------------------------------------------
CATEGORY_VOCAB: dict[str, list[str]] = {
    "multi_database_routing": [
        "wrong database routed",
        "agent queried only one database",
        "cross-database join failed",
        "routing failure",
        "missing sub-query",
        "tool not called",
    ],
    "join_key_mismatch": [
        "join returned zero rows",
        "format mismatch",
        "integer string mismatch",
        "prefix not resolved",
        "customer id format",
        "key conversion failed",
    ],
    "unstructured_text_extraction": [
        "raw text returned",
        "extraction step skipped",
        "keyword matching insufficient",
        "sentiment not classified",
        "free text aggregation wrong",
        "LIKE query overcounted",
    ],
    "domain_knowledge_gap": [
        "naive interpretation used",
        "wrong definition of active",
        "churn definition wrong",
        "fiscal quarter assumption",
        "domain term not defined",
        "proxy definition used",
    ],
}


def multi_pass_retrieve(
    query: str,
    kb_path: str,
    pass_queries: list[str] | None = None,
    category: str | None = None,
    score_fn: Callable[[str, str], float] | None = None,
    min_score: float = 0.1,
) -> list[dict]:
    """
    Run multiple retrieval passes over a KB document and return deduplicated results.

    Args:
        query:        The original natural language query from the agent.
        kb_path:      Path to the KB file to search (markdown).
        pass_queries: Explicit list of query strings for each pass. If None,
                      uses CATEGORY_VOCAB[category] if category is provided,
                      otherwise falls back to a single pass with the original query.
        category:     DAB failure category key for automatic vocab expansion.
                      One of: "multi_database_routing", "join_key_mismatch",
                      "unstructured_text_extraction", "domain_knowledge_gap".
        score_fn:     Optional scoring function(passage, query) → float.
                      Defaults to simple keyword overlap score.
        min_score:    Minimum score threshold for a passage to be included.

    Returns:
        List of dicts, deduplicated, sorted by score descending:
        [{"passage": str, "score": float, "matched_queries": [str]}, ...]
    """
    # Build the list of query passes
    queries = _build_query_list(query, pass_queries, category)

    # Load KB document
    passages = _load_passages(kb_path)
    if not passages:
        print(f"[multi_pass_retrieval] WARNING: No passages found in {kb_path}")
        return []

    # Score function
    fn = score_fn or _keyword_overlap_score

    # Run passes and collect results
    result_map: dict[str, dict] = {}  # passage → {score, matched_queries}

    for q in queries:
        for passage in passages:
            score = fn(passage, q)
            if score < min_score:
                continue
            if passage not in result_map:
                result_map[passage] = {"passage": passage, "score": score, "matched_queries": [q]}
            else:
                # Keep highest score, accumulate matched queries
                result_map[passage]["score"] = max(result_map[passage]["score"], score)
                if q not in result_map[passage]["matched_queries"]:
                    result_map[passage]["matched_queries"].append(q)

    # Sort by score descending
    results = sorted(result_map.values(), key=lambda x: x["score"], reverse=True)
    return results


def retrieve_corrections(
    failure_category: str,
    kb_path: str = "kb/corrections/corrections_log.md",
) -> list[dict]:
    """
    Convenience wrapper: retrieve all corrections log entries matching a
    given DAB failure category using the full category vocabulary expansion.

    Args:
        failure_category: One of the four DAB failure category keys.
        kb_path:          Path to the corrections log.

    Returns:
        Deduplicated list of matching correction entries.
    """
    vocab = CATEGORY_VOCAB.get(failure_category)
    if not vocab:
        print(f"[multi_pass_retrieval] WARNING: Unknown category '{failure_category}'. "
              f"Valid options: {list(CATEGORY_VOCAB)}")
        vocab = [failure_category]

    return multi_pass_retrieve(
        query=failure_category,
        kb_path=kb_path,
        pass_queries=vocab,
    )


def retrieve_domain_term(
    term: str,
    kb_path: str = "kb/domain/domain_terms.md",
) -> list[dict]:
    """
    Convenience wrapper: retrieve the definition of a domain term using
    multiple vocabulary passes to handle paraphrasing.

    Example: retrieve_domain_term("active customer") will also search for
    "active account", "customer activity", "inactivity window", etc.

    Args:
        term:    The domain term to look up (e.g. "active customer").
        kb_path: Path to the domain terms KB document.

    Returns:
        Deduplicated list of matching passages from the domain terms doc.
    """
    # Generate vocabulary expansions from the term itself
    words = term.lower().split()
    expansions = [
        term,
        " ".join(reversed(words)),           # reversed word order
        f"definition of {term}",
        f"correct interpretation of {term}",
        f"naive interpretation {words[0]}",  # catches "naive vs correct" entries
    ]
    return multi_pass_retrieve(query=term, kb_path=kb_path, pass_queries=expansions)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _build_query_list(
    query: str,
    pass_queries: list[str] | None,
    category: str | None,
) -> list[str]:
    if pass_queries:
        return [query] + pass_queries
    if category and category in CATEGORY_VOCAB:
        return [query] + CATEGORY_VOCAB[category]
    return [query]


def _load_passages(kb_path: str) -> list[str]:
    """
    Load a markdown KB file and split it into passages at heading boundaries.
    Each heading (## or ###) starts a new passage.
    """
    path = Path(kb_path)
    if not path.exists():
        print(f"[multi_pass_retrieval] WARNING: KB file not found: {kb_path}")
        return []

    text = path.read_text(encoding="utf-8")
    # Split on markdown headings (## or ###), keep the heading with its content
    raw = re.split(r"(?=^#{2,3} )", text, flags=re.MULTILINE)
    passages = [p.strip() for p in raw if p.strip()]
    return passages


def _keyword_overlap_score(passage: str, query: str) -> float:
    """
    Simple keyword overlap scorer.
    Score = number of query words found in passage / total query words.
    Case-insensitive. Strips punctuation.

    Replace with a semantic similarity function (e.g. sentence-transformers)
    for higher recall on paraphrased entries.
    """
    query_words = set(re.sub(r"[^\w\s]", "", query.lower()).split())
    passage_lower = passage.lower()
    if not query_words:
        return 0.0
    matches = sum(1 for w in query_words if w in passage_lower)
    return matches / len(query_words)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import tempfile, os

    # Create a temporary KB file for testing
    sample_kb = """## Active Business Definition

Active business means a business with at least one review in the last 12 months.
Naive interpretation: any row in the business table.
Correct interpretation: JOIN to review with date filter.

## Churn Definition

Churn means a customer has not purchased in the last 90 days.
Naive interpretation: account status field is inactive.
Domain knowledge gap failure occurs when agent uses account status as proxy.

## High-Rated Business

High-rated requires stars >= 4 AND review_count >= 10.
Agents that omit review_count floor return misleading results.
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(sample_kb)
        tmp_path = f.name

    try:
        # Test 1: multi_pass_retrieve finds domain knowledge gap entries
        results = multi_pass_retrieve(
            query="active customer definition",
            kb_path=tmp_path,
            category="domain_knowledge_gap",
        )
        assert len(results) > 0, "Expected at least one result"
        assert any("Active Business" in r["passage"] for r in results), \
            "Expected Active Business passage in results"

        # Test 2: retrieve_domain_term finds term with paraphrasing
        results2 = retrieve_domain_term("churn", kb_path=tmp_path)
        assert len(results2) > 0, "Expected churn definition to be found"
        assert any("Churn" in r["passage"] for r in results2), \
            "Expected Churn passage in results"

        # Test 3: missing file returns empty list without crash
        results3 = multi_pass_retrieve("anything", kb_path="/nonexistent/path.md")
        assert results3 == [], "Expected empty list for missing file"

        print("multi_pass_retrieval: all smoke tests passed.")
    finally:
        os.unlink(tmp_path)