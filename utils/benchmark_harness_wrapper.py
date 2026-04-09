"""
benchmark_harness_wrapper.py
-----------------------------
Wrapper around the DAB evaluation harness (eval/run_benchmark.py) that adds:
  - Structured trace logging per query and trial
  - pass@1 score computation
  - Score progression tracking across runs (for measurable improvement evidence)
  - Regression detection against a held-out baseline

DAB evaluation requirement (from challenge doc):
  - 54 queries, minimum 5 trials each
  - Agent must accept: {question, available_databases, schema_info}
  - Agent must return: {answer, query_trace, confidence}
  - Results submitted as JSON via GitHub PR

Usage:
    from utils.benchmark_harness_wrapper import BenchmarkHarness

    harness = BenchmarkHarness(
        agent_fn=your_agent_function,
        output_dir="results/",
        trials=5,
    )
    harness.run_all()
    harness.save_results()
    print(harness.pass_at_1_score())
"""

import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Any


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
AgentInput  = dict[str, Any]   # {question, available_databases, schema_info}
AgentOutput = dict[str, Any]   # {answer, query_trace, confidence}
AgentFn     = Callable[[AgentInput], AgentOutput]


# ---------------------------------------------------------------------------
# BenchmarkHarness
# ---------------------------------------------------------------------------
class BenchmarkHarness:
    """
    Wraps the DAB evaluation loop with structured logging, pass@1 scoring,
    and regression detection.

    Args:
        agent_fn:       The agent function to evaluate. Must accept AgentInput
                        and return AgentOutput.
        output_dir:     Directory for results JSON and score log. Created if missing.
        trials:         Number of trials per query (minimum 5 for valid DAB submission).
        expected_file:  Path to held-out expected answers JSON. Format:
                        [{"query_id": str, "question": str, "expected_answer": Any, ...}]
        run_label:      Human-readable label for this run (e.g. "week8-baseline").
                        Appears in score log for progression tracking.
    """

    def __init__(
        self,
        agent_fn: AgentFn,
        output_dir: str = "results/",
        trials: int = 5,
        expected_file: str = "eval/expected_answers.json",
        run_label: str = "",
    ):
        if trials < 5:
            raise ValueError(
                f"trials={trials} is below the DAB minimum of 5. "
                "Submissions with fewer than 5 trials per query are invalid."
            )
        self.agent_fn     = agent_fn
        self.output_dir   = Path(output_dir)
        self.trials       = trials
        self.expected_file = Path(expected_file)
        self.run_label    = run_label or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._queries: list[dict]  = []
        self._results: list[dict]  = []
        self._score_log: list[dict] = self._load_score_log()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_queries(self, queries: list[dict] | None = None) -> None:
        """
        Load queries to evaluate. If queries is None, loads from expected_file.

        Each query dict must have at minimum:
          {"query_id": str, "question": str, "available_databases": list,
           "schema_info": dict, "expected_answer": Any}
        """
        if queries is not None:
            self._queries = queries
            return

        if not self.expected_file.exists():
            raise FileNotFoundError(
                f"Expected answers file not found: {self.expected_file}. "
                "Create eval/expected_answers.json or pass queries directly."
            )
        with open(self.expected_file) as f:
            self._queries = json.load(f)
        print(f"[harness] Loaded {len(self._queries)} queries from {self.expected_file}")

    def run_all(self) -> list[dict]:
        """
        Run all loaded queries for the configured number of trials.
        Returns the full results list.
        """
        if not self._queries:
            raise RuntimeError("No queries loaded. Call load_queries() first.")

        self._results = []
        total = len(self._queries)

        for i, query in enumerate(self._queries):
            print(f"[harness] Query {i+1}/{total}: {query.get('query_id', '?')} — "
                  f"{query['question'][:60]}...")
            result = self._run_query(query)
            self._results.append(result)

        return self._results

    def run_single(self, query: dict) -> dict:
        """Run a single query for all trials. Useful for probe testing."""
        return self._run_query(query)

    def pass_at_1_score(self) -> float:
        """
        Compute pass@1 score across all results.
        pass@1 = fraction of (query, trial) pairs where the agent returned
        the correct answer on the first attempt.

        Returns float between 0.0 and 1.0.
        """
        if not self._results:
            return 0.0

        total_trials = 0
        passed_trials = 0

        for result in self._results:
            for trial in result["trials"]:
                total_trials += 1
                if trial["passed"]:
                    passed_trials += 1

        return passed_trials / total_trials if total_trials > 0 else 0.0

    def save_results(self, filename: str | None = None) -> Path:
        """
        Save results to a JSON file in output_dir.
        Filename defaults to: results_<run_label>.json

        The saved file is the DAB submission format:
        list of {query_id, question, trials: [{answer, query_trace, passed}]}
        """
        fname = filename or f"results_{self.run_label}.json"
        out_path = self.output_dir / fname
        with open(out_path, "w") as f:
            json.dump(self._results, f, indent=2)
        print(f"[harness] Results saved to {out_path}")
        return out_path

    def record_score(self) -> None:
        """
        Append the current pass@1 score to the score log for progression tracking.
        The score log is used as evidence of measurable improvement (required by rubric).
        """
        entry = {
            "run_label":    self.run_label,
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "pass_at_1":    self.pass_at_1_score(),
            "total_queries": len(self._results),
            "trials_per_query": self.trials,
        }
        self._score_log.append(entry)
        self._save_score_log()
        print(f"[harness] Score recorded: pass@1 = {entry['pass_at_1']:.3f} "
              f"(run: {self.run_label})")

    def check_regressions(self, baseline_label: str) -> list[dict]:
        """
        Compare current results against a previous run (by label) and return
        any queries that passed before but fail now.

        Args:
            baseline_label: The run_label of the baseline run to compare against.

        Returns:
            List of regressed query dicts with keys: query_id, baseline_pass_rate,
            current_pass_rate.
        """
        baseline_file = self.output_dir / f"results_{baseline_label}.json"
        if not baseline_file.exists():
            print(f"[harness] WARNING: Baseline file not found: {baseline_file}. "
                  "Cannot check regressions.")
            return []

        with open(baseline_file) as f:
            baseline = json.load(f)

        baseline_rates = {
            r["query_id"]: self._pass_rate(r["trials"])
            for r in baseline
        }
        current_rates = {
            r["query_id"]: self._pass_rate(r["trials"])
            for r in self._results
        }

        regressions = []
        for qid, b_rate in baseline_rates.items():
            c_rate = current_rates.get(qid, 0.0)
            if c_rate < b_rate:
                regressions.append({
                    "query_id":         qid,
                    "baseline_pass_rate": b_rate,
                    "current_pass_rate":  c_rate,
                })

        if regressions:
            print(f"[harness] ⚠ {len(regressions)} regression(s) detected vs baseline "
                  f"'{baseline_label}'")
        else:
            print(f"[harness] ✓ No regressions vs baseline '{baseline_label}'")

        return regressions

    def print_score_progression(self) -> None:
        """Print the score log showing improvement across runs."""
        if not self._score_log:
            print("[harness] No score history recorded yet.")
            return
        print("\n=== Score Progression ===")
        for entry in self._score_log:
            print(f"  {entry['timestamp'][:10]}  {entry['run_label']:<30} "
                  f"pass@1 = {entry['pass_at_1']:.3f}")
        print("=========================\n")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_query(self, query: dict) -> dict:
        trials_results = []
        for t in range(self.trials):
            trial_result = self._run_single_trial(query, trial_num=t + 1)
            trials_results.append(trial_result)

        return {
            "query_id":  query.get("query_id", _hash(query["question"])),
            "question":  query["question"],
            "trials":    trials_results,
            "pass_rate": self._pass_rate(trials_results),
        }

    def _run_single_trial(self, query: dict, trial_num: int) -> dict:
        agent_input: AgentInput = {
            "question":            query["question"],
            "available_databases": query.get("available_databases", []),
            "schema_info":         query.get("schema_info", {}),
        }

        start = time.monotonic()
        error = None
        agent_output: AgentOutput = {"answer": None, "query_trace": [], "confidence": 0.0}

        try:
            agent_output = self.agent_fn(agent_input)
        except Exception as e:
            error = str(e)
            print(f"[harness]   Trial {trial_num} ERROR: {error}")

        elapsed = time.monotonic() - start
        passed = self._check_answer(
            agent_output.get("answer"),
            query.get("expected_answer"),
        )

        return {
            "trial":       trial_num,
            "passed":      passed,
            "answer":      agent_output.get("answer"),
            "expected":    query.get("expected_answer"),
            "query_trace": agent_output.get("query_trace", []),
            "confidence":  agent_output.get("confidence", 0.0),
            "latency_s":   round(elapsed, 3),
            "error":       error,
        }

    @staticmethod
    def _check_answer(actual: Any, expected: Any) -> bool:
        """
        Check whether the agent's answer matches the expected answer.
        Applies DAB float tolerance (±0.01) for numerical answers.
        Drivers: extend this method for domain-specific answer matching
        (e.g. set equality for list answers, case-insensitive string match).
        """
        if actual is None or expected is None:
            return False
        # Numerical tolerance (DAB requirement: ±0.01)
        try:
            return abs(float(actual) - float(expected)) <= 0.01
        except (TypeError, ValueError):
            pass
        # String comparison (case-insensitive, stripped)
        if isinstance(actual, str) and isinstance(expected, str):
            return actual.strip().lower() == expected.strip().lower()
        # Set equality for list answers (order-independent)
        if isinstance(actual, list) and isinstance(expected, list):
            return set(str(x) for x in actual) == set(str(x) for x in expected)
        return actual == expected

    @staticmethod
    def _pass_rate(trials: list[dict]) -> float:
        if not trials:
            return 0.0
        return sum(1 for t in trials if t.get("passed")) / len(trials)

    def _score_log_path(self) -> Path:
        return self.output_dir / "score_log.json"

    def _load_score_log(self) -> list[dict]:
        p = self._score_log_path()
        if p.exists():
            with open(p) as f:
                return json.load(f)
        return []

    def _save_score_log(self) -> None:
        with open(self._score_log_path(), "w") as f:
            json.dump(self._score_log, f, indent=2)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:8]


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Stub agent that always returns the expected answer for testing
    def stub_agent(inp: AgentInput) -> AgentOutput:
        return {
            "answer":      "42",
            "query_trace": [{"step": "stub", "db": "postgresql", "query": "SELECT 42"}],
            "confidence":  1.0,
        }

    sample_queries = [
        {
            "query_id":            "q001",
            "question":            "What is the total revenue?",
            "available_databases": ["postgresql"],
            "schema_info":         {},
            "expected_answer":     "42",
        },
        {
            "query_id":            "q002",
            "question":            "How many active businesses are in Phoenix?",
            "available_databases": ["postgresql", "mongodb"],
            "schema_info":         {},
            "expected_answer":     "wrong_answer",   # stub will fail this
        },
    ]

    harness = BenchmarkHarness(
        agent_fn=stub_agent,
        output_dir="/tmp/harness_test/",
        trials=5,
        run_label="smoke-test",
    )
    harness.load_queries(sample_queries)
    harness.run_all()

    score = harness.pass_at_1_score()
    assert 0.0 <= score <= 1.0, f"Score out of range: {score}"

    # q001 should pass (answer matches), q002 should fail
    q1 = next(r for r in harness._results if r["query_id"] == "q001")
    q2 = next(r for r in harness._results if r["query_id"] == "q002")
    assert all(t["passed"] for t in q1["trials"]), "q001 should pass all trials"
    assert not any(t["passed"] for t in q2["trials"]), "q002 should fail all trials"

    harness.record_score()
    harness.print_score_progression()
    harness.save_results()

    print("benchmark_harness_wrapper: all smoke tests passed.")