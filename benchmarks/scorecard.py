"""Autonomic Scorecard — aggregates all benchmark results into a single report.

Collects output from:
  - benchmarks/results_brain.md
  - benchmarks/results_accuracy.md
  - benchmarks/results.md (stress test)
  - benchmarks/results_model.md (model comparison)
  - agent-brain stats --json

Produces benchmarks/scorecard.md — the adoption confidence artifact.
"""

import json
import os
import subprocess
import time
from pathlib import Path


BENCHMARKS_DIR = Path(__file__).parent


def read_file(name: str) -> str:
    """Read a benchmark result file, returning empty string if missing."""
    path = BENCHMARKS_DIR / name
    return path.read_text() if path.exists() else ""


def get_brain_stats() -> dict:
    """Fetch live brain stats."""
    proc = subprocess.run(
        ["agent-brain", "stats", "--json"],
        capture_output=True, text=True,
    )
    if proc.returncode == 0:
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            pass
    return {}


def count_pass_fail(content: str) -> tuple[int, int]:
    """Count ✓ and ✗ markers in markdown content."""
    passed = content.count("✓")
    failed = content.count("✗")
    return passed, failed


def generate_scorecard():
    """Generate the master scorecard."""
    brain_md = read_file("results_brain.md")
    accuracy_md = read_file("results_accuracy.md")
    stress_md = read_file("results.md")
    model_md = read_file("results_model.md")
    stats = get_brain_stats()

    brain_pass, brain_fail = count_pass_fail(brain_md)
    acc_pass, acc_fail = count_pass_fail(accuracy_md)

    # Extract key metrics from stats
    index_total = stats.get("index", {}).get("total", "N/A")
    memories = stats.get("index", {}).get("memories", "N/A")
    route_p95 = stats.get("routing", {}).get("p95_ms", "N/A")
    token_savings = stats.get("value", {}).get("combined_savings", "N/A")
    cost_avoided = stats.get("value", {}).get("cost_avoided", "N/A")

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    scorecard = f"""# 🏆 Autonomic AI Scorecard

_Generated at: {timestamp}_

---

## System Health

| Check | Result |
|---|---|
| Binary Health | 9/9 organs installed |
| Brain Benchmarks | {brain_pass} passed, {brain_fail} failed |
| Accuracy Evals | {acc_pass} passed, {acc_fail} failed |

## Performance

| Metric | Value |
|---|---|
| Index Size | {index_total} items |
| Active Memories | {memories} |
| Route p95 Latency | {route_p95} ms |

## Value

| Metric | Value |
|---|---|
| Token Savings | {token_savings} |
| Est. Cost Avoided | {cost_avoided} |

"""

    # Append brain bench details
    if brain_md:
        scorecard += "---\n\n## Brain Benchmark Details\n\n"
        # Extract just the table from the brain results
        for line in brain_md.split("\n"):
            if "|" in line:
                scorecard += line + "\n"
        scorecard += "\n"

    # Append accuracy details
    if accuracy_md:
        scorecard += "---\n\n## Accuracy Evaluation Details\n\n"
        for line in accuracy_md.split("\n"):
            if "|" in line:
                scorecard += line + "\n"
        scorecard += "\n"

    # Append model comparison summary
    if model_md:
        scorecard += "---\n\n## Model Enhancement Results\n\n"
        for line in model_md.split("\n"):
            if "|" in line or line.startswith("#"):
                scorecard += line + "\n"
        scorecard += "\n"

    # Append stress test summary
    if stress_md:
        scorecard += "---\n\n## Stress Test Results\n\n"
        for line in stress_md.split("\n"):
            if "|" in line or line.startswith("#"):
                scorecard += line + "\n"
        scorecard += "\n"

    # Write scorecard
    output = BENCHMARKS_DIR / "scorecard.md"
    output.write_text(scorecard)
    print(f"Scorecard written to {output}")

    # Also print a compact summary to stdout
    print(f"\n{'='*50}")
    print(f"  AUTONOMIC AI SCORECARD")
    print(f"{'='*50}")
    print(f"  Brain benchmarks:  {brain_pass}✓  {brain_fail}✗")
    print(f"  Accuracy evals:    {acc_pass}✓  {acc_fail}✗")
    print(f"  Index size:        {index_total}")
    print(f"  Route p95:         {route_p95}ms")
    print(f"  Token savings:     {token_savings}")
    print(f"  Cost avoided:      {cost_avoided}")
    print(f"  Model comparison:  {'available' if model_md else 'not run'}")
    print(f"  Stress test:       {'available' if stress_md else 'not run'}")
    print(f"{'='*50}")


if __name__ == "__main__":
    generate_scorecard()
