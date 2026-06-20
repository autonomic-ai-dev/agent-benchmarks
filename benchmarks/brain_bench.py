"""Wraps agent-brain's native benchmark suite and captures structured output.

Runs each bench sub-command, parses the log output, and writes results to
benchmarks/results_brain.md.
"""

import subprocess
import re
import os
import json
import time


BENCH_COMMANDS = {
    "ci_latency": {
        "cmd": ["agent-brain", "bench", "--ci"],
        "desc": "Latency gate (warm route p95)",
    },
    "mcp_tools": {
        "cmd": ["agent-brain", "bench", "--mcp", "--assert"],
        "desc": "MCP tool latency (route, context, token tools, graphify)",
    },
    "graphify": {
        "cmd": ["agent-brain", "bench", "--graphify", "--assert"],
        "desc": "Graphify ingest + code_context route",
    },
    "scale_ann": {
        "cmd": ["agent-brain", "bench", "--scale", "--assert"],
        "desc": "ANN scale at 1k/5k/10k (p95 ≤ 50ms)",
    },
    "supervisor": {
        "cmd": ["agent-brain", "bench", "--supervisor", "--assert"],
        "desc": "Supervisor skill/must_apply/savings",
    },
}


def run_benches():
    """Run all brain bench sub-commands and collect results."""
    results = {}
    for name, spec in BENCH_COMMANDS.items():
        print(f"\n{'='*60}")
        print(f"Running: {spec['desc']}")
        print(f"Command: {' '.join(spec['cmd'])}")
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


def write_report(results):
    """Write results to benchmarks/results_brain.md."""
    os.makedirs("benchmarks", exist_ok=True)
    with open("benchmarks/results_brain.md", "w") as f:
        f.write("# Agent-Brain Benchmark Results\n\n")
        f.write(f"_Generated at: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}_\n\n")

        passed = sum(1 for r in results.values() if r["passed"])
        total = len(results)
        f.write(f"**Overall: {passed}/{total} gates passed**\n\n")

        f.write("| Benchmark | Status | Time (s) | Description |\n")
        f.write("|---|---|---|---|\n")
        for name, r in results.items():
            status = "✓" if r["passed"] else "✗"
            f.write(f"| {name} | {status} | {r['elapsed_s']} | {r['description']} |\n")

        f.write("\n---\n\n")
        for name, r in results.items():
            f.write(f"## {name}\n\n")
            if r["stdout"]:
                f.write(f"```\n{r['stdout'][-800:]}\n```\n\n")

    print(f"\nReport written to benchmarks/results_brain.md")


if __name__ == "__main__":
    results = run_benches()
    write_report(results)

    failed = [n for n, r in results.items() if not r["passed"]]
    if failed:
        print(f"\n✗ {len(failed)} benchmark(s) failed: {', '.join(failed)}")
        exit(1)
    else:
        print(f"\n✓ All {len(results)} benchmarks passed")
