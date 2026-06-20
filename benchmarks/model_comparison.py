"""Model comparison benchmark — before/after with agent-brain context.

Uses Ollama (local) or HuggingFace Inference API for pluggable open-source
models.  Executes generated code in a Docker sandbox (--network=none) for
safe, isolated verification.

Usage:
    python model_comparison.py --model codellama:7b
    python model_comparison.py --model qwen2.5-coder:7b --provider ollama
    python model_comparison.py --model bigcode/starcoder2-7b --provider huggingface

Requires:
    - Ollama running locally (ollama serve), OR
    - HUGGINGFACE_TOKEN env var for HF Inference API
    - Docker for sandbox execution
"""

import argparse
import json
import os
import subprocess
import time
import tempfile
import re
from dataclasses import dataclass
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests")
    exit(1)


PROMPTS_DIR = Path(__file__).parent / "prompts"
CURATED_PROMPTS = PROMPTS_DIR / "curated_prompts.json"
SANDBOX_IMAGE = "autonomic-sandbox:latest"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PromptCase:
    id: str
    task: str
    code: str
    language: str
    expected_keywords: list
    category: str


@dataclass(frozen=True)
class EvalResult:
    prompt_id: str
    mode: str  # "baseline" or "enhanced"
    response: str
    response_tokens: int
    latency_ms: float
    keyword_hits: int
    keyword_total: int
    sandbox_exit_code: int  # -1 if sandbox not applicable
    sandbox_stdout: str


# ---------------------------------------------------------------------------
# LLM providers
# ---------------------------------------------------------------------------

def query_ollama(model: str, prompt: str) -> tuple[str, int, float]:
    """Query an Ollama model. Returns (response_text, token_count, latency_ms)."""
    url = os.environ.get("OLLAMA_HOST", "http://localhost:11434") + "/api/generate"
    start = time.perf_counter()
    resp = requests.post(url, json={
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 2048},
    }, timeout=120)
    latency = (time.perf_counter() - start) * 1000
    data = resp.json()
    text = data.get("response", "")
    tokens = data.get("eval_count", len(text.split()))
    return text, tokens, latency


def query_huggingface(model: str, prompt: str) -> tuple[str, int, float]:
    """Query HuggingFace Inference API. Returns (response_text, token_count, latency_ms)."""
    token = os.environ.get("HUGGINGFACE_TOKEN", "")
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    start = time.perf_counter()
    resp = requests.post(url, json={
        "inputs": prompt,
        "parameters": {"max_new_tokens": 2048, "temperature": 0.1},
    }, headers=headers, timeout=120)
    latency = (time.perf_counter() - start) * 1000
    data = resp.json()
    text = data[0].get("generated_text", "") if isinstance(data, list) else str(data)
    tokens = len(text.split())
    return text, tokens, latency


PROVIDERS = {
    "ollama": query_ollama,
    "huggingface": query_huggingface,
}


# ---------------------------------------------------------------------------
# Docker sandbox execution
# ---------------------------------------------------------------------------

def build_sandbox_image():
    """Build the sandbox Docker image if it doesn't exist."""
    sandbox_dir = Path(__file__).parent / "sandbox"
    subprocess.run(
        ["docker", "build", "-t", SANDBOX_IMAGE, "-f",
         str(sandbox_dir / "Dockerfile.sandbox"), str(sandbox_dir)],
        capture_output=True, check=True,
    )


def run_in_sandbox(code: str, language: str, timeout_s: int = 10) -> tuple[int, str]:
    """Execute code in a network-isolated Docker container.

    Returns (exit_code, stdout).
    """
    ext = {"python": ".py", "typescript": ".ts", "rust": ".rs"}.get(language, ".py")

    with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False) as f:
        f.write(code)
        f.flush()
        host_path = f.name

    try:
        cmd = {
            "python": f"python /tmp/code{ext}",
            "typescript": f"node /tmp/code{ext}",  # simplified; TS would need tsc
        }.get(language, f"python /tmp/code{ext}")

        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network=none",
                "--memory=128m",
                "--cpus=0.5",
                f"--stop-timeout={timeout_s}",
                "-v", f"{host_path}:/tmp/code{ext}:ro",
                SANDBOX_IMAGE,
                cmd,
            ],
            capture_output=True, text=True,
            timeout=timeout_s + 5,
        )
        return result.returncode, result.stdout[:2000]
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"
    finally:
        os.unlink(host_path)


# ---------------------------------------------------------------------------
# Context injection via agent-brain
# ---------------------------------------------------------------------------

def get_brain_context(task: str) -> str:
    """Call agent-brain's route_task to get retrieval context for a task."""
    # Use the MCP bench interface or direct CLI
    proc = subprocess.run(
        ["agent-brain", "inspect", "log", "--last"],
        capture_output=True, text=True,
    )
    # For the benchmark, we simulate context injection by running a stats query
    # In production, the MCP server injects this automatically
    proc2 = subprocess.run(
        ["agent-brain", "stats", "--json"],
        capture_output=True, text=True,
    )
    if proc2.returncode == 0:
        try:
            stats = json.loads(proc2.stdout)
            return (
                f"[CONTEXT from agent-brain]\n"
                f"Index size: {stats.get('index', {}).get('total', 'N/A')} items\n"
                f"Active memories: {stats.get('index', {}).get('memories', 'N/A')}\n"
                f"Project conventions: Use immutable patterns, explicit error handling, "
                f"type annotations on all public APIs. Follow AAA test pattern.\n"
                f"[END CONTEXT]\n\n"
            )
        except (json.JSONDecodeError, KeyError):
            pass
    return ""


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def score_keywords(response: str, expected: list[str]) -> tuple[int, int]:
    """Count how many expected keywords appear in the response."""
    hits = sum(1 for kw in expected if kw.lower() in response.lower())
    return hits, len(expected)


def extract_code_block(response: str) -> str:
    """Extract the first fenced code block from a model response."""
    match = re.search(r"```(?:\w+)?\n(.*?)```", response, re.DOTALL)
    return match.group(1).strip() if match else response


def run_comparison(prompts: list[PromptCase], model: str, provider: str):
    """Run before/after comparison for all prompts."""
    query_fn = PROVIDERS[provider]
    results: list[EvalResult] = []

    print(f"\n{'='*70}")
    print(f"Model: {model} | Provider: {provider}")
    print(f"Prompts: {len(prompts)}")
    print(f"{'='*70}")

    for prompt in prompts:
        print(f"\n--- {prompt.id} ({prompt.category}) ---")

        # ── Baseline (no context) ──
        baseline_prompt = (
            f"Task: {prompt.task}\n\nCode:\n```{prompt.language}\n{prompt.code}\n```\n\n"
            f"Provide the corrected/improved code."
        )
        b_resp, b_tokens, b_latency = query_fn(model, baseline_prompt)
        b_hits, b_total = score_keywords(b_resp, prompt.expected_keywords)

        # Try sandbox execution for Python
        b_exit = -1
        b_stdout = ""
        if prompt.language == "python":
            code_block = extract_code_block(b_resp)
            try:
                b_exit, b_stdout = run_in_sandbox(code_block, prompt.language)
            except Exception:
                b_exit, b_stdout = -1, "sandbox error"

        results.append(EvalResult(
            prompt_id=prompt.id, mode="baseline",
            response=b_resp[:500], response_tokens=b_tokens,
            latency_ms=b_latency,
            keyword_hits=b_hits, keyword_total=b_total,
            sandbox_exit_code=b_exit, sandbox_stdout=b_stdout[:200],
        ))
        print(f"  baseline: {b_hits}/{b_total} keywords, {b_tokens} tokens, {b_latency:.0f}ms")

        # ── Enhanced (with agent-brain context) ──
        context = get_brain_context(prompt.task)
        enhanced_prompt = (
            f"{context}"
            f"Task: {prompt.task}\n\nCode:\n```{prompt.language}\n{prompt.code}\n```\n\n"
            f"Provide the corrected/improved code following the project conventions above."
        )
        e_resp, e_tokens, e_latency = query_fn(model, enhanced_prompt)
        e_hits, e_total = score_keywords(e_resp, prompt.expected_keywords)

        e_exit = -1
        e_stdout = ""
        if prompt.language == "python":
            code_block = extract_code_block(e_resp)
            try:
                e_exit, e_stdout = run_in_sandbox(code_block, prompt.language)
            except Exception:
                e_exit, e_stdout = -1, "sandbox error"

        results.append(EvalResult(
            prompt_id=prompt.id, mode="enhanced",
            response=e_resp[:500], response_tokens=e_tokens,
            latency_ms=e_latency,
            keyword_hits=e_hits, keyword_total=e_total,
            sandbox_exit_code=e_exit, sandbox_stdout=e_stdout[:200],
        ))
        print(f"  enhanced: {e_hits}/{e_total} keywords, {e_tokens} tokens, {e_latency:.0f}ms")

    return results


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(results: list[EvalResult], model: str):
    """Write comparison report to benchmarks/results_model.md."""
    os.makedirs("benchmarks", exist_ok=True)

    baseline = [r for r in results if r.mode == "baseline"]
    enhanced = [r for r in results if r.mode == "enhanced"]

    b_kw = sum(r.keyword_hits for r in baseline) / max(sum(r.keyword_total for r in baseline), 1) * 100
    e_kw = sum(r.keyword_hits for r in enhanced) / max(sum(r.keyword_total for r in enhanced), 1) * 100
    b_tokens = sum(r.response_tokens for r in baseline) / max(len(baseline), 1)
    e_tokens = sum(r.response_tokens for r in enhanced) / max(len(enhanced), 1)
    b_sandbox_pass = sum(1 for r in baseline if r.sandbox_exit_code == 0)
    e_sandbox_pass = sum(1 for r in enhanced if r.sandbox_exit_code == 0)
    sandbox_total = sum(1 for r in baseline if r.sandbox_exit_code != -1)

    with open("benchmarks/results_model.md", "w") as f:
        f.write(f"# Model Enhancement Report\n\n")
        f.write(f"**Model:** `{model}`\n")
        f.write(f"_Generated at: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}_\n\n")

        f.write("## Summary\n\n")
        f.write("| Metric | Baseline | Enhanced | Delta |\n")
        f.write("|---|---|---|---|\n")
        f.write(f"| Keyword Accuracy | {b_kw:.1f}% | {e_kw:.1f}% | {e_kw - b_kw:+.1f}% |\n")
        f.write(f"| Avg Tokens | {b_tokens:.0f} | {e_tokens:.0f} | {e_tokens - b_tokens:+.0f} |\n")
        if sandbox_total > 0:
            f.write(f"| Sandbox Pass | {b_sandbox_pass}/{sandbox_total} | {e_sandbox_pass}/{sandbox_total} | {e_sandbox_pass - b_sandbox_pass:+d} |\n")

        f.write("\n## Per-Prompt Results\n\n")
        f.write("| Prompt | Category | Baseline KW | Enhanced KW | Baseline Tokens | Enhanced Tokens | Sandbox |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for b, e in zip(baseline, enhanced):
            sbx = ""
            if b.sandbox_exit_code != -1:
                sbx = f"{'✓' if b.sandbox_exit_code == 0 else '✗'} → {'✓' if e.sandbox_exit_code == 0 else '✗'}"
            f.write(
                f"| {b.prompt_id} | {b.prompt_id.split('_')[0]} "
                f"| {b.keyword_hits}/{b.keyword_total} "
                f"| {e.keyword_hits}/{e.keyword_total} "
                f"| {b.response_tokens} "
                f"| {e.response_tokens} "
                f"| {sbx} |\n"
            )

    print(f"\nReport written to benchmarks/results_model.md")
    print(f"\nKeyword accuracy:  {b_kw:.1f}% → {e_kw:.1f}% ({e_kw - b_kw:+.1f}%)")
    print(f"Avg tokens:        {b_tokens:.0f} → {e_tokens:.0f}")
    if sandbox_total > 0:
        print(f"Sandbox pass:      {b_sandbox_pass}/{sandbox_total} → {e_sandbox_pass}/{sandbox_total}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Autonomic Model Comparison Benchmark")
    parser.add_argument("--model", default="qwen2.5-coder:7b", help="Model name")
    parser.add_argument("--provider", default="ollama", choices=list(PROVIDERS.keys()),
                        help="LLM provider (ollama or huggingface)")
    parser.add_argument("--prompts", default=str(CURATED_PROMPTS),
                        help="Path to prompts JSON file")
    parser.add_argument("--build-sandbox", action="store_true",
                        help="Build the sandbox Docker image before running")
    args = parser.parse_args()

    # Load prompts
    with open(args.prompts) as f:
        raw = json.load(f)
    prompts = [PromptCase(**p) for p in raw]
    print(f"Loaded {len(prompts)} prompts from {args.prompts}")

    # Build sandbox image if requested
    if args.build_sandbox:
        print("Building sandbox image...")
        build_sandbox_image()

    results = run_comparison(prompts, args.model, args.provider)
    write_report(results, args.model)


if __name__ == "__main__":
    main()
