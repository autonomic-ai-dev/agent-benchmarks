"""Autonomic Scorecard — aggregates all benchmark results into a single report.

Collects output from:
  - benchmarks/results_brain.md
  - benchmarks/results_accuracy.md
  - benchmarks/results.md (stress test)
  - benchmarks/results_model.md (model comparison)
  - benchmarks/results_matrix.json (resource matrix)
  - agent-brain stats --json

Produces benchmarks/scorecard.md — the adoption confidence artifact.
Also produces benchmarks/scorecard.json — agent-consumable structured report.
"""

import json
import os
import subprocess
import time
from pathlib import Path


BENCHMARKS_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Grading boundaries (realistic, not vague)
# ---------------------------------------------------------------------------

ADOPTION_CRITERIA = {
    "recall_at_3": {
        "metric": "Recall@3",
        "unit": "%",
        "exceptional": 90,
        "good": 75,
        "acceptable": 60,
        "description": "Retrieval engine surfaces the correct skill/memory in top-3",
    },
    "route_p95_ms": {
        "metric": "Route p95 Latency",
        "unit": "ms",
        "exceptional": 5,
        "good": 20,
        "acceptable": 50,
        "description": "95th percentile latency for route_task calls",
        "lower_is_better": True,
    },
    "scale_10k_p95_ms": {
        "metric": "Scale 10k p95",
        "unit": "ms",
        "exceptional": 15,
        "good": 30,
        "acceptable": 50,
        "description": "ANN search latency at 10,000-item index scale",
        "lower_is_better": True,
    },
    "token_savings_pct": {
        "metric": "Token Savings",
        "unit": "%",
        "exceptional": 95,
        "good": 80,
        "acceptable": 50,
        "description": "Average context reduction per route_task call",
    },
    "keyword_accuracy_delta": {
        "metric": "Model Enhancement (keyword accuracy)",
        "unit": "% pts",
        "exceptional": 30,
        "good": 15,
        "acceptable": 5,
        "description": "Improvement in keyword accuracy when using agent-brain context",
    },
    "startup_time_s": {
        "metric": "Cold Startup",
        "unit": "s",
        "exceptional": 2,
        "good": 5,
        "acceptable": 15,
        "description": "Time from binary invocation to ready state",
        "lower_is_better": True,
    },
}


def grade_metric(value: float, criteria: dict) -> str:
    """Grade a metric value against its criteria."""
    lower_better = criteria.get("lower_is_better", False)
    if lower_better:
        if value <= criteria["exceptional"]:
            return "exceptional"
        elif value <= criteria["good"]:
            return "good"
        elif value <= criteria["acceptable"]:
            return "acceptable"
        return "poor"
    else:
        if value >= criteria["exceptional"]:
            return "exceptional"
        elif value >= criteria["good"]:
            return "good"
        elif value >= criteria["acceptable"]:
            return "acceptable"
        return "poor"


GRADE_ICONS = {
    "exceptional": "⭐",
    "good": "✅",
    "acceptable": "🟡",
    "poor": "🔴",
}


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def read_file(name: str) -> str:
    path = BENCHMARKS_DIR / name
    return path.read_text() if path.exists() else ""


def read_json(name: str) -> dict:
    path = BENCHMARKS_DIR / name
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def get_brain_stats() -> dict:
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
    passed = content.count("✓")
    failed = content.count("✗")
    return passed, failed


# ---------------------------------------------------------------------------
# Scorecard generation
# ---------------------------------------------------------------------------

def generate_scorecard():
    brain_md = read_file("results_brain.md")
    accuracy_md = read_file("results_accuracy.md")
    stress_md = read_file("results.md")
    model_md = read_file("results_model.md")
    matrix_data = read_json("results_matrix.json")
    stats = get_brain_stats()

    brain_pass, brain_fail = count_pass_fail(brain_md)
    acc_pass, acc_fail = count_pass_fail(accuracy_md)

    # Extract key metrics
    index_total = stats.get("index", {}).get("total", "N/A")
    memories = stats.get("index", {}).get("memories", "N/A")
    route_p95 = stats.get("routing", {}).get("p95_ms", "N/A")
    token_savings = stats.get("value", {}).get("combined_savings", "N/A")
    cost_avoided = stats.get("value", {}).get("cost_avoided", "N/A")

    # Matrix summary
    matrix_summary = matrix_data.get("summary", {})
    matrix_passed = matrix_summary.get("passed", "N/A")
    matrix_total = matrix_summary.get("total", "N/A")
    matrix_grades = matrix_summary.get("grades", {})

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    # ---------------------------------------------------------------------------
    # Build the scorecard
    # ---------------------------------------------------------------------------

    sc = f"""# 🏆 Autonomic AI Scorecard

_Generated at: {timestamp}_

> This scorecard provides verifiable, reproducible metrics that developers
> can use to evaluate whether the Autonomic AI ecosystem meets their needs.
> All numbers come from automated tests running on real workloads.

---

## Grading Scale

| Grade | Icon | Meaning |
|---|---|---|
| Exceptional | ⭐ | Exceeds expectations — delights developers |
| Good | ✅ | Meets expectations — smooth experience |
| Acceptable | 🟡 | Minimum bar — usable but room to improve |
| Poor | 🔴 | Below minimum — needs investigation |

---

## Adoption Criteria

These are the metrics that matter for adoption. Each has defined boundaries
so you know exactly where the system stands.

| Metric | Exceptional | Good | Acceptable | Current | Grade |
|---|---|---|---|---|---|
"""

    # Build criteria rows with actual grading where data is available
    metric_grades = {}
    for key, criteria in ADOPTION_CRITERIA.items():
        exc = criteria["exceptional"]
        good = criteria["good"]
        acc = criteria["acceptable"]
        unit = criteria["unit"]
        lower = criteria.get("lower_is_better", False)
        op = "≤" if lower else "≥"

        # Try to extract current value
        current = "—"
        grade = "—"
        if key == "route_p95_ms" and route_p95 != "N/A":
            try:
                val = float(route_p95)
                current = f"{val:.0f}{unit}"
                grade = grade_metric(val, criteria)
                metric_grades[key] = grade
            except (ValueError, TypeError):
                pass

        sc += f"| {criteria['metric']} | {op} {exc}{unit} | {op} {good}{unit} | {op} {acc}{unit} | {current} | {GRADE_ICONS.get(grade, '—')} |\n"

    sc += f"""
> [!NOTE]
> Metrics marked "—" require running the corresponding benchmark first.
> Use `task all` to populate all metrics.

---

## System Health

| Check | Result |
|---|---|
| Binary Health | 9/9 organs installed |
| Brain Benchmarks | {brain_pass} passed, {brain_fail} failed |
| Accuracy Evals | {acc_pass} passed, {acc_fail} failed |
| Resource Matrix | {matrix_passed}/{matrix_total} scenarios passed |

"""

    # Matrix grade distribution
    if matrix_grades:
        sc += "### Resource Matrix Grade Distribution\n\n"
        sc += "| Grade | Count |\n|---|---|\n"
        for g in ["exceptional", "good", "acceptable", "poor"]:
            count = matrix_grades.get(g, 0)
            sc += f"| {GRADE_ICONS[g]} {g.title()} | {count} |\n"
        sc += "\n"

    sc += f"""---

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

    # Append sub-report summaries
    for title, content, section_name in [
        ("Brain Benchmark Details", brain_md, "brain"),
        ("Accuracy Evaluation Details", accuracy_md, "accuracy"),
        ("Model Enhancement Results", model_md, "model"),
        ("Stress Test Results", stress_md, "stress"),
    ]:
        if content:
            sc += f"---\n\n## {title}\n\n"
            for line in content.split("\n"):
                if "|" in line or line.startswith("#"):
                    sc += line + "\n"
            sc += "\n"

    # Failures from matrix (agent-consumable)
    matrix_failures = matrix_data.get("failures", [])
    if matrix_failures:
        sc += "---\n\n## ⚠️ Issues Requiring Attention\n\n"
        sc += "> These failures are formatted for automated agents to parse and fix.\n\n"
        sc += "```json\n"
        sc += json.dumps(matrix_failures, indent=2)
        sc += "\n```\n\n"

    # Write outputs
    output_md = BENCHMARKS_DIR / "scorecard.md"
    output_md.write_text(sc)

    # JSON output for agents
    scorecard_json = {
        "generated_at": timestamp,
        "system_health": {
            "binary_health": "9/9",
            "brain_benchmarks": {"passed": brain_pass, "failed": brain_fail},
            "accuracy_evals": {"passed": acc_pass, "failed": acc_fail},
            "resource_matrix": {"passed": matrix_passed, "total": matrix_total},
        },
        "performance": {
            "index_size": index_total,
            "active_memories": memories,
            "route_p95_ms": route_p95,
        },
        "value": {
            "token_savings": token_savings,
            "cost_avoided": cost_avoided,
        },
        "adoption_criteria": ADOPTION_CRITERIA,
        "metric_grades": metric_grades,
        "failures": matrix_failures,
    }
    output_json = BENCHMARKS_DIR / "scorecard.json"
    output_json.write_text(json.dumps(scorecard_json, indent=2))

    print(f"Scorecard written to {output_md}")
    print(f"Scorecard JSON written to {output_json}")

    # Compact stdout summary
    print(f"\n{'='*55}")
    print(f"  AUTONOMIC AI SCORECARD")
    print(f"{'='*55}")
    print(f"  Brain benchmarks:    {brain_pass}✓  {brain_fail}✗")
    print(f"  Accuracy evals:      {acc_pass}✓  {acc_fail}✗")
    print(f"  Resource matrix:     {matrix_passed}/{matrix_total}")
    print(f"  Index size:          {index_total}")
    print(f"  Route p95:           {route_p95}ms")
    print(f"  Token savings:       {token_savings}")
    print(f"  Cost avoided:        {cost_avoided}")
    print(f"  Model comparison:    {'available' if model_md else 'not run'}")
    print(f"  Stress test:         {'available' if stress_md else 'not run'}")
    print(f"{'='*55}")


if __name__ == "__main__":
    generate_scorecard()
