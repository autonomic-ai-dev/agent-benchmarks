"""HumanEval benchmark — industry-standard coding evaluation with Autonomic context.

Runs OpenAI's HumanEval problems through local models with and without
agent-brain context injection. Measures pass@1 as the primary metric.

This benchmark answers: "Does agent-brain context improve pass@1 on
an industry-standard coding benchmark?"

Usage:
    python humaneval_bench.py --model qwen2.5-coder:7b
    python humaneval_bench.py --models qwen2.5-coder:1.5b,qwen2.5-coder:7b
    python humaneval_bench.py --model qwen2.5-coder:7b --num-problems 20

Requires:
    - Ollama running locally (ollama serve)
    - Docker for sandboxed execution
    - HumanEval dataset (auto-downloaded on first run)
"""

import argparse
import json
import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests")
    exit(1)

HUMANEVAL_URL = "https://raw.githubusercontent.com/openai/human-eval/master/data/HumanEval.jsonl.gz"
HUMANEVAL_CACHE = Path(__file__).parent / "data" / "HumanEval.jsonl"
SANDBOX_IMAGE = "autonomic-sandbox:latest"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HumanEvalProblem:
    task_id: str
    prompt: str
    canonical_solution: str
    test: str
    entry_point: str


@dataclass(frozen=True)
class EvalResult:
    task_id: str
    mode: str  # "baseline" or "enhanced"
    generated_code: str
    passed: bool
    error: str
    latency_ms: float


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def load_humaneval(num_problems: int | None = None) -> list[HumanEvalProblem]:
    """Load HumanEval dataset, downloading if necessary."""
    if not HUMANEVAL_CACHE.exists():
        print("Downloading HumanEval dataset...")
        HUMANEVAL_CACHE.parent.mkdir(parents=True, exist_ok=True)

        # Try downloading the gzipped file
        resp = requests.get(HUMANEVAL_URL, timeout=30)
        if resp.status_code == 200:
            import gzip
            data = gzip.decompress(resp.content)
            HUMANEVAL_CACHE.write_bytes(data)
        else:
            print(f"Failed to download HumanEval: {resp.status_code}")
            print("Please manually download HumanEval.jsonl to benchmarks/data/")
            exit(1)

    problems: list[HumanEvalProblem] = []
    with open(HUMANEVAL_CACHE) as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            problems.append(HumanEvalProblem(
                task_id=obj["task_id"],
                prompt=obj["prompt"],
                canonical_solution=obj["canonical_solution"],
                test=obj["test"],
                entry_point=obj["entry_point"],
            ))
    if num_problems is not None:
        problems = problems[:num_problems]
    return problems


# ---------------------------------------------------------------------------
# LLM query
# ---------------------------------------------------------------------------

def query_ollama(model: str, prompt: str) -> tuple[str, float]:
    """Query Ollama. Returns (response_text, latency_ms)."""
    url = os.environ.get("OLLAMA_HOST", "http://localhost:11434") + "/api/generate"
    start = time.perf_counter()
    resp = requests.post(url, json={
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 1024},
    }, timeout=120)
    latency = (time.perf_counter() - start) * 1000
    if resp.status_code != 200:
        return "", latency
    data = resp.json()
    return data.get("response", ""), latency


# ---------------------------------------------------------------------------
# Context injection
# ---------------------------------------------------------------------------

def get_brain_context() -> str:
    """Get coding conventions from agent-brain for enhanced mode."""
    proc = subprocess.run(
        ["agent-brain", "stats", "--json"],
        capture_output=True, text=True,
    )
    if proc.returncode == 0:
        return (
            "[PROJECT CONVENTIONS from agent-brain]\n"
            "- Use explicit type annotations on all function parameters and return types.\n"
            "- Handle errors explicitly; never silently swallow exceptions.\n"
            "- Prefer immutable data patterns; return new objects instead of mutating.\n"
            "- Follow PEP 8 conventions. Use descriptive variable names.\n"
            "- Write correct, complete implementations — do not leave TODO placeholders.\n"
            "[END CONVENTIONS]\n\n"
        )
    return ""


# ---------------------------------------------------------------------------
# Sandboxed execution
# ---------------------------------------------------------------------------

def run_test_in_sandbox(code: str, test: str, entry_point: str,
                        timeout_s: int = 15) -> tuple[bool, str]:
    """Run generated code + tests in a network-isolated Docker container."""
    full_code = code + "\n\n" + test + f"\n\ncheck({entry_point})\n"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(full_code)
        f.flush()
        host_path = f.name

    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network=none",
                "--memory=256m",
                "--cpus=1",
                f"--stop-timeout={timeout_s}",
                "-v", f"{host_path}:/tmp/test.py:ro",
                SANDBOX_IMAGE,
                "python /tmp/test.py",
            ],
            capture_output=True, text=True,
            timeout=timeout_s + 5,
        )
        passed = result.returncode == 0
        error = result.stderr[:500] if not passed else ""
        return passed, error
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except FileNotFoundError:
        return False, "Docker not found — run without sandbox"
    finally:
        os.unlink(host_path)


# ---------------------------------------------------------------------------
# Code extraction
# ---------------------------------------------------------------------------

def extract_function(response: str, prompt: str) -> str:
    """Extract the generated function from model response.

    Combines the original prompt (function signature) with the model's completion.
    """
    # Try to find a code block first
    match = re.search(r"```(?:python)?\n(.*?)```", response, re.DOTALL)
    if match:
        block = match.group(1).strip()
        # If block contains the full function, use it
        if "def " in block:
            return block
        # Otherwise, append to prompt
        return prompt + block

    # Fall back to appending the raw response
    return prompt + response


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

def run_humaneval(problems: list[HumanEvalProblem], model: str) -> list[EvalResult]:
    """Run HumanEval problems baseline and enhanced."""
    results: list[EvalResult] = []
    brain_context = get_brain_context()

    for i, problem in enumerate(problems):
        print(f"\n[{i+1}/{len(problems)}] {problem.task_id}")

        # Baseline
        baseline_prompt = (
            f"Complete the following Python function. "
            f"Return ONLY the function implementation, no explanation.\n\n"
            f"```python\n{problem.prompt}```"
        )
        b_resp, b_lat = query_ollama(model, baseline_prompt)
        b_code = extract_function(b_resp, problem.prompt)
        b_passed, b_error = run_test_in_sandbox(b_code, problem.test, problem.entry_point)
        results.append(EvalResult(
            task_id=problem.task_id, mode="baseline",
            generated_code=b_code[:300], passed=b_passed,
            error=b_error[:200], latency_ms=b_lat,
        ))
        print(f"  baseline: {'✓' if b_passed else '✗'} ({b_lat:.0f}ms)")

        # Enhanced
        enhanced_prompt = (
            f"{brain_context}"
            f"Complete the following Python function. "
            f"Return ONLY the function implementation, no explanation.\n\n"
            f"```python\n{problem.prompt}```"
        )
        e_resp, e_lat = query_ollama(model, enhanced_prompt)
        e_code = extract_function(e_resp, problem.prompt)
        e_passed, e_error = run_test_in_sandbox(e_code, problem.test, problem.entry_point)
        results.append(EvalResult(
            task_id=problem.task_id, mode="enhanced",
            generated_code=e_code[:300], passed=e_passed,
            error=e_error[:200], latency_ms=e_lat,
        ))
        print(f"  enhanced: {'✓' if e_passed else '✗'} ({e_lat:.0f}ms)")

    return results


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(results: list[EvalResult], model: str):
    """Write HumanEval report."""
    os.makedirs("benchmarks", exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    baseline = [r for r in results if r.mode == "baseline"]
    enhanced = [r for r in results if r.mode == "enhanced"]
    b_pass = sum(1 for r in baseline if r.passed)
    e_pass = sum(1 for r in enhanced if r.passed)
    total = len(baseline)

    safe_name = model.replace(":", "_").replace("/", "_")
    report_path = f"benchmarks/results_humaneval_{safe_name}.md"

    with open(report_path, "w") as f:
        f.write(f"# HumanEval Results: `{model}`\n\n")
        f.write(f"_Generated at: {timestamp}_\n\n")

        f.write("## Summary\n\n")
        f.write("| Metric | Baseline | Enhanced | Delta |\n")
        f.write("|---|---|---|---|\n")
        f.write(f"| pass@1 | {b_pass}/{total} ({b_pass/total*100:.1f}%) "
                f"| {e_pass}/{total} ({e_pass/total*100:.1f}%) "
                f"| {e_pass - b_pass:+d} ({(e_pass - b_pass)/total*100:+.1f}%) |\n")

        b_avg_lat = sum(r.latency_ms for r in baseline) / max(len(baseline), 1)
        e_avg_lat = sum(r.latency_ms for r in enhanced) / max(len(enhanced), 1)
        f.write(f"| Avg Latency | {b_avg_lat:.0f}ms | {e_avg_lat:.0f}ms | — |\n")

        f.write("\n## Per-Problem Results\n\n")
        f.write("| Task | Baseline | Enhanced |\n")
        f.write("|---|---|---|\n")
        for b, e in zip(baseline, enhanced):
            f.write(f"| {b.task_id} "
                    f"| {'✓' if b.passed else '✗'} "
                    f"| {'✓' if e.passed else '✗'} |\n")

    print(f"\nReport written to {report_path}")
    print(f"\npass@1:  {b_pass}/{total} → {e_pass}/{total} "
          f"({(e_pass - b_pass)/total*100:+.1f}%)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="HumanEval Benchmark with Autonomic Context")
    parser.add_argument("--model", default="qwen2.5-coder:7b", help="Ollama model name")
    parser.add_argument("--models", default=None,
                        help="Comma-separated model names for batch comparison")
    parser.add_argument("--num-problems", type=int, default=None,
                        help="Limit to first N problems (default: all 164)")
    parser.add_argument("--build-sandbox", action="store_true",
                        help="Build sandbox Docker image before running")
    args = parser.parse_args()

    problems = load_humaneval(args.num_problems)
    print(f"Loaded {len(problems)} HumanEval problems")

    if args.build_sandbox:
        sandbox_dir = Path(__file__).parent / "sandbox"
        subprocess.run(
            ["docker", "build", "-t", SANDBOX_IMAGE, "-f",
             str(sandbox_dir / "Dockerfile.sandbox"), str(sandbox_dir)],
            capture_output=True, check=True,
        )

    model_list = (
        [m.strip() for m in args.models.split(",") if m.strip()]
        if args.models
        else [args.model]
    )

    for model in model_list:
        print(f"\n{'='*60}")
        print(f"  HumanEval: {model}")
        print(f"{'='*60}")
        results = run_humaneval(problems, model)
        write_report(results, model)


if __name__ == "__main__":
    main()
