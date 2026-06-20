"""Resource matrix benchmark — tests all organs under different RAM/CPU constraints.

Runs each organ's core operations under constrained Docker containers to produce
a compatibility matrix that developers can use to decide minimum system requirements.

Produces:
  - benchmarks/results_matrix.json  (agent-consumable structured report)
  - benchmarks/results_matrix.md    (human-readable report with grading)
"""

import subprocess
import json
import time
import os
from dataclasses import dataclass, asdict
from typing import Optional

# ---------------------------------------------------------------------------
# Resource profiles
# ---------------------------------------------------------------------------

PROFILES = [
    {"name": "minimal",    "memory": "256m", "cpus": "0.5", "label": "256 MB / 0.5 CPU"},
    {"name": "low",        "memory": "512m", "cpus": "1",   "label": "512 MB / 1 CPU"},
    {"name": "standard",   "memory": "1g",   "cpus": "2",   "label": "1 GB / 2 CPU"},
    {"name": "high",       "memory": "2g",   "cpus": "4",   "label": "2 GB / 4 CPU"},
    {"name": "unlimited",  "memory": "",     "cpus": "",    "label": "Unlimited (host)"},
]

# ---------------------------------------------------------------------------
# Test scenarios per organ
# ---------------------------------------------------------------------------

SCENARIOS = {
    "agent-brain": [
        {
            "id": "brain_index",
            "name": "Reindex local items",
            "cmd": ["agent-brain", "index"],
            "timeout": 60,
        },
        {
            "id": "brain_bench_ci",
            "name": "Latency gate (bench --ci)",
            "cmd": ["agent-brain", "bench", "--ci"],
            "timeout": 120,
        },
        {
            "id": "brain_eval_ci",
            "name": "Recall@3 gate (eval --ci)",
            "cmd": ["agent-brain", "eval", "--ci"],
            "timeout": 120,
        },
        {
            "id": "brain_gc",
            "name": "Garbage collection cycle",
            "cmd": ["agent-brain", "gc"],
            "timeout": 30,
        },
        {
            "id": "brain_stats",
            "name": "Stats computation",
            "cmd": ["agent-brain", "stats"],
            "timeout": 15,
        },
    ],
    "agent-spine": [
        {
            "id": "spine_status",
            "name": "Status report",
            "cmd": ["agent-spine", "status"],
            "timeout": 10,
        },
    ],
    "agent-heart": [
        {
            "id": "heart_gc",
            "name": "GC cycle",
            "cmd": ["agent-heart", "gc"],
            "timeout": 30,
        },
        {
            "id": "heart_status",
            "name": "Status report",
            "cmd": ["agent-heart", "status"],
            "timeout": 10,
        },
    ],
    "agent-nerves": [
        {
            "id": "nerves_status",
            "name": "Status report",
            "cmd": ["agent-nerves", "status"],
            "timeout": 10,
        },
    ],
    "agent-muscle": [
        {
            "id": "muscle_run",
            "name": "Execute echo command",
            "cmd": ["agent-muscle", "run", "echo hello"],
            "timeout": 10,
        },
    ],
    "agent-immune": [
        {
            "id": "immune_status",
            "name": "Status report",
            "cmd": ["agent-immune", "status"],
            "timeout": 10,
        },
    ],
    "agent-eyes": [
        {
            "id": "eyes_status",
            "name": "Status report",
            "cmd": ["agent-eyes", "status"],
            "timeout": 10,
        },
    ],
    "agent-mouth": [
        {
            "id": "mouth_validate",
            "name": "Validate safe command",
            "cmd": ["agent-mouth", "validate", "--command", "echo hello"],
            "timeout": 10,
        },
    ],
}

# ---------------------------------------------------------------------------
# Grading thresholds (latency in seconds)
# ---------------------------------------------------------------------------
# These define realistic developer expectations.
# "exceptional" = delights developers, "acceptable" = minimum for adoption,
# "poor" = needs investigation before release.

GRADE_THRESHOLDS = {
    "exceptional": 2.0,    # < 2s  — near-instant
    "good":        5.0,    # < 5s  — responsive
    "acceptable": 15.0,    # < 15s — tolerable
    # anything above 15s is "poor"
}

GRADE_LABELS = {
    "exceptional": "⭐ Exceptional (< 2s)",
    "good":        "✅ Good (< 5s)",
    "acceptable":  "🟡 Acceptable (< 15s)",
    "poor":        "🔴 Poor (≥ 15s)",
}


def grade_latency(seconds: float) -> str:
    if seconds < GRADE_THRESHOLDS["exceptional"]:
        return "exceptional"
    elif seconds < GRADE_THRESHOLDS["good"]:
        return "good"
    elif seconds < GRADE_THRESHOLDS["acceptable"]:
        return "acceptable"
    return "poor"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    scenario_name: str
    organ: str
    profile_name: str
    profile_label: str
    exit_code: int
    passed: bool
    elapsed_s: float
    grade: str
    stdout_tail: str
    stderr_tail: str
    error_summary: Optional[str]
    fix_suggestion: Optional[str]


def run_scenario_in_profile(organ: str, scenario: dict, profile: dict) -> ScenarioResult:
    """Run a single scenario under a specific resource profile."""
    docker_cmd = ["docker", "run", "--rm"]
    if profile["memory"]:
        docker_cmd += [f"--memory={profile['memory']}"]
    if profile["cpus"]:
        docker_cmd += [f"--cpus={profile['cpus']}"]
    docker_cmd += [
        "-v", f"{os.path.expanduser('~')}/.autonomic:/root/.autonomic",
        "autonomic-benchmarks:latest",
    ]
    docker_cmd += scenario["cmd"]

    start = time.perf_counter()
    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True, text=True,
            timeout=scenario["timeout"],
        )
        elapsed = time.perf_counter() - start
        passed = result.returncode == 0

        error_summary = None
        fix_suggestion = None
        if not passed:
            error_summary = _extract_error(result.stderr, result.stdout)
            fix_suggestion = _suggest_fix(scenario["id"], error_summary, profile)

        return ScenarioResult(
            scenario_id=scenario["id"],
            scenario_name=scenario["name"],
            organ=organ,
            profile_name=profile["name"],
            profile_label=profile["label"],
            exit_code=result.returncode,
            passed=passed,
            elapsed_s=round(elapsed, 3),
            grade=grade_latency(elapsed) if passed else "poor",
            stdout_tail=result.stdout[-500:] if result.stdout else "",
            stderr_tail=result.stderr[-500:] if result.stderr else "",
            error_summary=error_summary,
            fix_suggestion=fix_suggestion,
        )
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        return ScenarioResult(
            scenario_id=scenario["id"],
            scenario_name=scenario["name"],
            organ=organ,
            profile_name=profile["name"],
            profile_label=profile["label"],
            exit_code=124,
            passed=False,
            elapsed_s=round(elapsed, 3),
            grade="poor",
            stdout_tail="",
            stderr_tail="TIMEOUT",
            error_summary=f"Command timed out after {scenario['timeout']}s",
            fix_suggestion=f"The {organ} operation '{scenario['name']}' exceeded the {scenario['timeout']}s timeout under {profile['label']}. "
                           f"Consider increasing the resource allocation or profiling the operation for memory/CPU bottlenecks.",
        )


def _extract_error(stderr: str, stdout: str) -> str:
    """Extract a concise error summary from command output."""
    for line in (stderr + stdout).split("\n"):
        lower = line.lower()
        if any(kw in lower for kw in ["error", "panic", "fatal", "failed", "oom", "killed"]):
            return line.strip()[:200]
    return stderr[-200:].strip() if stderr else "Unknown error"


def _suggest_fix(scenario_id: str, error: str, profile: dict) -> str:
    """Generate an agent-consumable fix suggestion based on the failure."""
    error_lower = error.lower()

    if "oom" in error_lower or "killed" in error_lower or "memory" in error_lower:
        return (
            f"Out of memory under {profile['label']}. "
            f"Action: Increase --memory limit or optimize memory usage in the {scenario_id} code path. "
            f"Check for large allocations, unbounded caches, or leaked buffers."
        )
    if "timeout" in error_lower:
        return (
            f"Operation timed out under {profile['label']}. "
            f"Action: Profile the {scenario_id} code path for CPU-bound bottlenecks. "
            f"Consider adding early termination, pagination, or reducing index scan scope."
        )
    if "not found" in error_lower or "no such" in error_lower:
        return (
            f"Missing dependency or file. "
            f"Action: Ensure the Docker image includes all required binaries and config files. "
            f"Check the Dockerfile.agent and install-all-organs.sh script."
        )
    return (
        f"Unexpected failure: {error[:100]}. "
        f"Action: Inspect the {scenario_id} source code for the error pattern. "
        f"Run locally with RUST_LOG=debug for detailed diagnostics."
    )


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def write_json_report(results: list[ScenarioResult]):
    """Write agent-consumable JSON report."""
    os.makedirs("benchmarks", exist_ok=True)
    data = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "profiles": PROFILES,
        "grade_thresholds": GRADE_THRESHOLDS,
        "results": [asdict(r) for r in results],
        "failures": [
            {
                "scenario_id": r.scenario_id,
                "organ": r.organ,
                "profile": r.profile_name,
                "error": r.error_summary,
                "fix_suggestion": r.fix_suggestion,
            }
            for r in results
            if not r.passed
        ],
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
            "grades": {
                g: sum(1 for r in results if r.grade == g)
                for g in ["exceptional", "good", "acceptable", "poor"]
            },
        },
    }
    with open("benchmarks/results_matrix.json", "w") as f:
        json.dump(data, f, indent=2)
    print("JSON report: benchmarks/results_matrix.json")


def write_markdown_report(results: list[ScenarioResult]):
    """Write human-readable markdown report with grading."""
    os.makedirs("benchmarks", exist_ok=True)

    # Group by profile
    by_profile = {}
    for r in results:
        by_profile.setdefault(r.profile_name, []).append(r)

    with open("benchmarks/results_matrix.md", "w") as f:
        f.write("# Resource Matrix Benchmark Results\n\n")
        f.write(f"_Generated at: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}_\n\n")

        # Summary
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        f.write(f"**Overall: {passed}/{total} scenarios passed**\n\n")

        # Grade legend
        f.write("### Grading Scale\n\n")
        f.write("| Grade | Criteria | Developer Impact |\n")
        f.write("|---|---|---|\n")
        f.write("| ⭐ Exceptional | < 2s | Near-instant — delights developers |\n")
        f.write("| ✅ Good | < 5s | Responsive — smooth workflow |\n")
        f.write("| 🟡 Acceptable | < 15s | Tolerable — usable but noticeable |\n")
        f.write("| 🔴 Poor | ≥ 15s or failed | Frustrating — blocks adoption |\n\n")

        # Matrix table
        f.write("---\n\n## Compatibility Matrix\n\n")
        profile_names = [p["name"] for p in PROFILES]
        scenario_ids = sorted(set(r.scenario_id for r in results))

        f.write(f"| Scenario | " + " | ".join(p["label"] for p in PROFILES) + " |\n")
        f.write(f"|---|" + "|".join("---" for _ in PROFILES) + "|\n")

        for sid in scenario_ids:
            row = f"| {sid} |"
            for pname in profile_names:
                match = [r for r in results if r.scenario_id == sid and r.profile_name == pname]
                if match:
                    r = match[0]
                    icon = {"exceptional": "⭐", "good": "✅", "acceptable": "🟡", "poor": "🔴"}[r.grade]
                    row += f" {icon} {r.elapsed_s}s |"
                else:
                    row += " — |"
            f.write(row + "\n")

        # Failures section (agent-consumable)
        failures = [r for r in results if not r.passed]
        if failures:
            f.write("\n---\n\n## ⚠️ Failures & Fix Suggestions\n\n")
            f.write("> These are structured for automated agents to consume and act on.\n\n")
            for r in failures:
                f.write(f"### `{r.scenario_id}` on `{r.profile_label}`\n\n")
                f.write(f"- **Organ:** `{r.organ}`\n")
                f.write(f"- **Exit Code:** `{r.exit_code}`\n")
                f.write(f"- **Error:** `{r.error_summary}`\n")
                f.write(f"- **Fix:** {r.fix_suggestion}\n")
                if r.stderr_tail:
                    f.write(f"\n```\n{r.stderr_tail}\n```\n\n")

        # Per-profile detail
        f.write("\n---\n\n## Detailed Results by Profile\n\n")
        for profile in PROFILES:
            pname = profile["name"]
            f.write(f"### {profile['label']}\n\n")
            f.write("| Organ | Scenario | Status | Time | Grade |\n")
            f.write("|---|---|---|---|---|\n")
            for r in by_profile.get(pname, []):
                status = "✓" if r.passed else "✗"
                icon = {"exceptional": "⭐", "good": "✅", "acceptable": "🟡", "poor": "🔴"}[r.grade]
                f.write(f"| {r.organ} | {r.scenario_name} | {status} | {r.elapsed_s}s | {icon} |\n")
            f.write("\n")

    print("Markdown report: benchmarks/results_matrix.md")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Resource Matrix Benchmark")
    parser.add_argument("--profiles", nargs="*", default=None,
                        help="Profile names to test (default: all)")
    parser.add_argument("--organs", nargs="*", default=None,
                        help="Organs to test (default: all)")
    args = parser.parse_args()

    profiles = PROFILES
    if args.profiles:
        profiles = [p for p in PROFILES if p["name"] in args.profiles]

    scenarios = SCENARIOS
    if args.organs:
        scenarios = {k: v for k, v in SCENARIOS.items() if k in args.organs}

    results: list[ScenarioResult] = []
    total = sum(len(s) for s in scenarios.values()) * len(profiles)
    current = 0

    for organ, organ_scenarios in scenarios.items():
        for scenario in organ_scenarios:
            for profile in profiles:
                current += 1
                print(f"\n[{current}/{total}] {scenario['id']} @ {profile['label']}")
                r = run_scenario_in_profile(organ, scenario, profile)
                results.append(r)
                status = "✓" if r.passed else "✗"
                icon = {"exceptional": "⭐", "good": "✅", "acceptable": "🟡", "poor": "🔴"}[r.grade]
                print(f"  {status} {icon} {r.elapsed_s}s")

    write_json_report(results)
    write_markdown_report(results)

    # Print compact summary
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    print(f"\n{'='*50}")
    print(f"  MATRIX COMPLETE: {passed}✓  {failed}✗  ({len(results)} total)")
    print(f"{'='*50}")

    if failed > 0:
        exit(1)


if __name__ == "__main__":
    main()
