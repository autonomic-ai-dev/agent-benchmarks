"""LoRA evaluation benchmark — measure fine-tuned vs base model performance.

After training a LoRA adapter via agent-muscle, this benchmark compares the
base model against the fine-tuned variant on the same curated prompt set
used by model_comparison.py.

Usage:
    python lora_eval.py --base-model qwen2.5-coder:7b --lora-model qwen2.5-coder-autonomic:7b
    python lora_eval.py --base-model qwen2.5-coder:7b --adapter-path ./lora_adapters/latest/

Requires:
    - Ollama running locally with both models loaded, OR
    - agent-muscle serve running with LoRA adapter support
"""

import argparse
import json
import os
import subprocess
import time
from dataclasses import dataclass, asdict
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
class LoraEvalResult:
    prompt_id: str
    mode: str  # "base", "lora", or "lora+brain"
    keyword_hits: int
    keyword_total: int
    latency_ms: float
    response_preview: str


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
        "options": {"temperature": 0.1, "num_predict": 2048},
    }, timeout=120)
    latency = (time.perf_counter() - start) * 1000
    data = resp.json()
    return data.get("response", ""), latency


def get_brain_context(task: str) -> str:
    """Get agent-brain context for enhanced mode."""
    proc = subprocess.run(
        ["agent-brain", "stats", "--json"],
        capture_output=True, text=True,
    )
    if proc.returncode == 0:
        return (
            "[CONTEXT from agent-brain]\n"
            "Project conventions: Use immutable patterns, explicit error handling, "
            "type annotations on all public APIs. Follow AAA test pattern.\n"
            "[END CONTEXT]\n\n"
        )
    return ""


def score_keywords(response: str, expected: list[str]) -> tuple[int, int]:
    """Count keyword hits in response."""
    hits = sum(1 for kw in expected if kw.lower() in response.lower())
    return hits, len(expected)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def run_lora_eval(
    prompts: list[PromptCase],
    base_model: str,
    lora_model: str | None = None,
) -> list[LoraEvalResult]:
    """Run 3-way comparison: base, LoRA, LoRA+brain."""
    results: list[LoraEvalResult] = []

    for prompt in prompts:
        print(f"\n--- {prompt.id} ({prompt.category}) ---")

        task_prompt = (
            f"Task: {prompt.task}\n\nCode:\n```{prompt.language}\n{prompt.code}\n```\n\n"
            f"Provide the corrected/improved code."
        )

        # Base model (no context, no fine-tuning)
        b_resp, b_lat = query_ollama(base_model, task_prompt)
        b_hits, b_total = score_keywords(b_resp, prompt.expected_keywords)
        results.append(LoraEvalResult(
            prompt_id=prompt.id, mode="base",
            keyword_hits=b_hits, keyword_total=b_total,
            latency_ms=b_lat, response_preview=b_resp[:200],
        ))
        print(f"  base:       {b_hits}/{b_total} keywords ({b_lat:.0f}ms)")

        # LoRA model (fine-tuned, no brain context)
        if lora_model:
            l_resp, l_lat = query_ollama(lora_model, task_prompt)
            l_hits, l_total = score_keywords(l_resp, prompt.expected_keywords)
            results.append(LoraEvalResult(
                prompt_id=prompt.id, mode="lora",
                keyword_hits=l_hits, keyword_total=l_total,
                latency_ms=l_lat, response_preview=l_resp[:200],
            ))
            print(f"  lora:       {l_hits}/{l_total} keywords ({l_lat:.0f}ms)")

            # LoRA model + brain context
            context = get_brain_context(prompt.task)
            enhanced_prompt = f"{context}{task_prompt}"
            lb_resp, lb_lat = query_ollama(lora_model, enhanced_prompt)
            lb_hits, lb_total = score_keywords(lb_resp, prompt.expected_keywords)
            results.append(LoraEvalResult(
                prompt_id=prompt.id, mode="lora+brain",
                keyword_hits=lb_hits, keyword_total=lb_total,
                latency_ms=lb_lat, response_preview=lb_resp[:200],
            ))
            print(f"  lora+brain: {lb_hits}/{lb_total} keywords ({lb_lat:.0f}ms)")

    return results


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(results: list[LoraEvalResult], base_model: str, lora_model: str | None):
    """Write LoRA evaluation report."""
    os.makedirs("benchmarks", exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    base_results = [r for r in results if r.mode == "base"]
    lora_results = [r for r in results if r.mode == "lora"]
    lb_results = [r for r in results if r.mode == "lora+brain"]

    def accuracy(rs: list[LoraEvalResult]) -> float:
        total_hits = sum(r.keyword_hits for r in rs)
        total_possible = sum(r.keyword_total for r in rs)
        return total_hits / max(total_possible, 1) * 100

    b_acc = accuracy(base_results)
    l_acc = accuracy(lora_results) if lora_results else 0
    lb_acc = accuracy(lb_results) if lb_results else 0

    with open("benchmarks/results_lora_eval.md", "w") as f:
        f.write("# 🧬 LoRA Fine-tuning Evaluation Report\n\n")
        f.write(f"_Generated at: {timestamp}_\n\n")
        f.write(f"**Base model:** `{base_model}`\n")
        if lora_model:
            f.write(f"**LoRA model:** `{lora_model}`\n")
        f.write("\n")

        f.write("## Summary\n\n")
        f.write("| Mode | Keyword Accuracy | Delta vs Base |\n")
        f.write("|---|---|---|\n")
        f.write(f"| Base (raw) | {b_acc:.1f}% | — |\n")
        if lora_results:
            f.write(f"| LoRA (fine-tuned) | {l_acc:.1f}% | {l_acc - b_acc:+.1f}% |\n")
            f.write(f"| LoRA + Brain Context | {lb_acc:.1f}% | {lb_acc - b_acc:+.1f}% |\n")

        f.write("\n## Per-Prompt Results\n\n")
        headers = "| Prompt | Category | Base"
        if lora_results:
            headers += " | LoRA | LoRA+Brain"
        headers += " |\n"
        f.write(headers)
        sep = "|---|---|---"
        if lora_results:
            sep += "|---|---"
        sep += "|\n"
        f.write(sep)

        for i, b in enumerate(base_results):
            line = f"| {b.prompt_id} | {b.prompt_id.split('_')[0]} | {b.keyword_hits}/{b.keyword_total}"
            if lora_results and i < len(lora_results):
                l = lora_results[i]
                lb = lb_results[i] if i < len(lb_results) else None
                line += f" | {l.keyword_hits}/{l.keyword_total}"
                if lb:
                    line += f" | {lb.keyword_hits}/{lb.keyword_total}"
            line += " |\n"
            f.write(line)

        if lora_results and l_acc > b_acc:
            f.write("\n## Key Finding\n\n")
            f.write(f"**LoRA fine-tuning improved keyword accuracy by {l_acc - b_acc:+.1f}%.**\n")
            if lb_acc > l_acc:
                f.write(f"**Combining LoRA + brain context adds another {lb_acc - l_acc:+.1f}%** "
                        f"for a total improvement of {lb_acc - b_acc:+.1f}% over baseline.\n")

    # JSON
    json_data = {
        "generated_at": timestamp,
        "base_model": base_model,
        "lora_model": lora_model,
        "base_accuracy_pct": round(b_acc, 1),
        "lora_accuracy_pct": round(l_acc, 1),
        "lora_brain_accuracy_pct": round(lb_acc, 1),
        "results": [asdict(r) for r in results],
    }
    with open("benchmarks/results_lora_eval.json", "w") as f:
        json.dump(json_data, f, indent=2)

    print(f"\nReport written to benchmarks/results_lora_eval.md")
    print(f"Base accuracy:       {b_acc:.1f}%")
    if lora_results:
        print(f"LoRA accuracy:       {l_acc:.1f}% ({l_acc - b_acc:+.1f}%)")
        print(f"LoRA+Brain accuracy: {lb_acc:.1f}% ({lb_acc - b_acc:+.1f}%)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LoRA Fine-tuning Evaluation Benchmark")
    parser.add_argument("--base-model", required=True, help="Base model name in Ollama")
    parser.add_argument("--lora-model", default=None,
                        help="LoRA fine-tuned model name in Ollama (must be pre-loaded)")
    parser.add_argument("--adapter-path", default=None,
                        help="Path to LoRA adapter dir (alternative to --lora-model)")
    parser.add_argument("--prompts", default=str(CURATED_PROMPTS),
                        help="Path to prompts JSON")
    args = parser.parse_args()

    with open(args.prompts) as f:
        raw = json.load(f)
    prompts = [PromptCase(**p) for p in raw]
    print(f"Loaded {len(prompts)} prompts")

    if args.adapter_path and not args.lora_model:
        print("\n⚠️  --adapter-path requires a pre-registered Ollama model name.")
        print("Register it first: ollama create <name> -f Modelfile")
        print("Then pass --lora-model <name>")
        print("\nRunning base model evaluation only...\n")

    results = run_lora_eval(prompts, args.base_model, args.lora_model)
    write_report(results, args.base_model, args.lora_model)


if __name__ == "__main__":
    main()
