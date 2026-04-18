# Results — Oracle Forge (Team Falcon)

This directory contains benchmark evaluation results from Oracle Forge runs against the UC Berkeley DataAgentBench (DAB) benchmark suite, plus the GitHub PR submission evidence.

## Contents

| File | Description |
|------|-------------|
| `dab_submission.json` | DAB-formatted results JSON — best trial answers per query, used for PR submission |
| `PR_SUBMISSION.md` | PR submission evidence — title, body, and submission record for ucbepic/DataAgentBench |

## Benchmark Summary

| Dataset | Queries | Best pass@1 | Trials Run |
|---------|---------|-------------|------------|
| yelp | 7 | 100% | 5 |
| bookreview | 3 | 33% | 1 |
| GITHUB_REPOS | 4 | 0% | 1 |
| stockmarket | 5 | 0% | 1 |

Full score progression (25+ dated runs) is in [`eval/score_log.md`](../eval/score_log.md).

## Submission Format

Each entry in `dab_submission.json` follows the DAB required structure:

```json
{
  "dataset": "<dataset_name>",
  "query_id": "<query_id>",
  "run": <run_number>,
  "answer": "<agent_generated_answer>"
}
```

## How to Reproduce

```bash
# Run a full 5-trial benchmark for any dataset
python eval/run_benchmark.py --dataset yelp --trials 5

# Results are saved to eval/run_logs/benchmark_<dataset>_<timestamp>.json
# Convert to DAB submission format
python eval/score.py --results eval/run_logs/benchmark_yelp_<timestamp>.json
```
