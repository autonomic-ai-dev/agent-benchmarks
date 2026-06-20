"""Accuracy evaluation — wraps agent-brain eval commands.

Runs Recall@3 gates, BEAM harness, and token savings measurement.
Produces benchmarks/results_accuracy.md.
"""

import subprocess
import json
import os
import time


EVAL_COMMANDS = {
    "recall_at_3": {
        "cmd": ["agent-brain", "eval", "--ci"],
        "desc": "Recall@3 gate (isolated fixture, threshold ≥ 60%)",
    },
    "skills_sh_recall": {
        "cmd": ["agent-brain", "eval", "--skills-sh"],
        "desc": "skills.sh Recall@3 (~2000-item index)",
    },
    "beam_harness": {
        "cmd": ["agent-brain", "eval", "--beam"],
        "desc": "BEAM memory + routing end-to-end harness",
    },
}


def run_evals():
    """Run all eval sub-commands."""
    results = {}
    for name, spec in EVAL_COMMANDS.items():
        print(f"\n{'='*60}")
        print(f"Running: {spec['desc']}")
        print(f"{'='*60}")

        start = time.perf_counter()
        proc = subprocess.run(spec["cmd"], capture_output=True, text=True)
        elapsed = time.perf_counter() - start

        results[name] = {
            "description": spec["desc"],
            "exit_code": proc.returncode,
            "passed": proc.returncode == 0,
            "elapsed_s": round(elapsed, 2),
            "stdout": proc.stdout[-2000:] if proc.stdout else "",
            "stderr": proc.stderr[-1000:] if proc.stderr else "",
        }

        status = "✓ PASS" if proc.returncode == 0 else "✗ FAIL"
        print(f"{status} ({elapsed:.2f}s)")

    return results


def get_token_savings():
    """Fetch token savings from agent-brain stats --json."""
    proc = subprocess.run(
        ["agent-brain", "stats", "--json"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def write_report(eval_results, stats):
    """Write combined accuracy report."""
    os.makedirs("benchmarks", exist_ok=True)
    with open("benchmarks/results_accuracy.md", "w") as f:
        f.write("# Accuracy & Value Evaluation Results\n\n")
        f.write(f"_Generated at: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}_\n\n")

        # Eval gates table
        passed = sum(1 for r in eval_results.values() if r["passed"])
        total = len(eval_results)
        f.write(f"## Eval Gates — {passed}/{total} passed\n\n")
        f.write("| Evaluation | Status | Time (s) | Description |\n")
        f.write("|---|---|---|---|\n")
        for name, r in eval_results.items():
            status = "✓" if r["passed"] else "✗"
            f.write(f"| {name} | {status} | {r['elapsed_s']} | {r['description']} |\n")

        # Token savings
        if stats:
            f.write("\n## Token Savings & Value\n\n")
            f.write(f"```json\n{json.dumps(stats, indent=2)}\n```\n")

        # Detailed output
        f.write("\n---\n\n")
        for name, r in eval_results.items():
            f.write(f"## {name}\n\n")
            if r["stdout"]:
                f.write(f"```\n{r['stdout'][-800:]}\n```\n\n")
            if not r["passed"] and r["stderr"]:
                f.write(f"**Stderr:**\n```\n{r['stderr'][-1000:]}\n```\n\n")

    print(f"\nReport written to benchmarks/results_accuracy.md")


if __name__ == "__main__":
    eval_results = run_evals()
    stats = get_token_savings()
    write_report(eval_results, stats)

    failed = [n for n, r in eval_results.items() if not r["passed"]]
    if failed:
        print(f"\n✗ {len(failed)} eval(s) failed: {', '.join(failed)}")
        exit(1)
    else:
        print(f"\n✓ All {len(eval_results)} evals passed")
