"""SWE-bench benchmark scaffold.

Evaluates Autonomic AI models against the SWE-bench-lite dataset (300 curated
real-world GitHub issues from Python repositories).

This benchmark tests the agent's ability to solve complex, multi-file software
engineering tasks using agent-spine workflows and agent-brain context.

Usage:
    python swebench_bench.py --model qwen2.5-coder:7b
    python swebench_bench.py --models qwen2.5-coder:1.5b,qwen2.5-coder:7b
    python swebench_bench.py --limit 10

Requires:
    - Ollama running locally
    - Docker for SWE-bench evaluation environments
    - 'datasets' package from HuggingFace
"""

import argparse
import json
import os
import subprocess
import time
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    from datasets import load_dataset
except ImportError:
    print("Please install required packages: pip install datasets")
    exit(1)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SWEBenchInstance:
    instance_id: str
    repo: str
    base_commit: str
    problem_statement: str
    hints_text: str


@dataclass(frozen=True)
class SWEBenchResult:
    instance_id: str
    model: str
    mode: str
    resolved: bool
    patch: str
    latency_ms: float


# ---------------------------------------------------------------------------
# Benchmark Logic
# ---------------------------------------------------------------------------

def load_swebench_lite(limit: int | None = None) -> list[SWEBenchInstance]:
    """Load SWE-bench-lite from HuggingFace datasets."""
    print("Loading SWE-bench-lite dataset...")
    dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    
    instances = []
    for item in dataset:
        instances.append(SWEBenchInstance(
            instance_id=item["instance_id"],
            repo=item["repo"],
            base_commit=item["base_commit"],
            problem_statement=item["problem_statement"],
            hints_text=item["hints_text"]
        ))
        
        if limit and len(instances) >= limit:
            break
            
    return instances


def run_swebench_instance(instance: SWEBenchInstance, model: str, mode: str) -> SWEBenchResult:
    """Run a single SWE-bench instance."""
    print(f"  Running {instance.instance_id} with {model} ({mode})...")
    start = time.perf_counter()
    
    # In a full implementation, this would:
    # 1. Start a Docker container with the repo at base_commit
    # 2. Give the agent access to the workspace
    # 3. Ask it to solve the problem_statement
    # 4. Extract the diff/patch
    # 5. Run the evaluation script
    
    # For now, this is a scaffold that simulates execution
    time.sleep(1) # Simulate thinking
    
    latency = (time.perf_counter() - start) * 1000
    
    return SWEBenchResult(
        instance_id=instance.instance_id,
        model=model,
        mode=mode,
        resolved=False, # Simulated failure
        patch="--- a/file.py\n+++ b/file.py\n@@ -1,1 +1,2 @@\n+ # TODO",
        latency_ms=latency
    )


def run_benchmark(instances: list[SWEBenchInstance], model: str) -> list[SWEBenchResult]:
    """Run all instances for a given model."""
    results = []
    
    for idx, instance in enumerate(instances):
        print(f"\n[{idx+1}/{len(instances)}] {instance.instance_id}")
        
        # Baseline (No Agent-Brain)
        b_res = run_swebench_instance(instance, model, mode="baseline")
        results.append(b_res)
        
        # Enhanced (With Agent-Brain Context + Spine Workflows)
        e_res = run_swebench_instance(instance, model, mode="enhanced")
        results.append(e_res)
        
    return results


def write_report(results: list[SWEBenchResult], models: list[str]):
    """Write the SWE-bench evaluation report."""
    os.makedirs("benchmarks", exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    
    report_path = "benchmarks/results_swebench.md"
    
    with open(report_path, "w") as f:
        f.write("# 🏗️ SWE-bench Evaluation Report\n\n")
        f.write(f"_Generated at: {timestamp}_\n\n")
        
        f.write("## Summary Table\n\n")
        f.write("| Model | Baseline Resolved | Enhanced Resolved | **Δ Resolved** | Avg Latency |\n")
        f.write("|---|---|---|---|---|\n")
        
        for model in models:
            model_results = [r for r in results if r.model == model]
            b_resolved = sum(1 for r in model_results if r.mode == "baseline" and r.resolved)
            e_resolved = sum(1 for r in model_results if r.mode == "enhanced" and r.resolved)
            total = len([r for r in model_results if r.mode == "baseline"])
            avg_latency = sum(r.latency_ms for r in model_results) / max(len(model_results), 1)
            
            delta = e_resolved - b_resolved
            f.write(
                f"| `{model}` "
                f"| {b_resolved}/{total} "
                f"| {e_resolved}/{total} "
                f"| **{delta:+}** "
                f"| {avg_latency:.0f}ms |\n"
            )
            
    print(f"\nSWE-bench report written to {report_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="SWE-bench Evaluation Scaffold")
    parser.add_argument("--model", default="qwen2.5-coder:7b", help="Model name")
    parser.add_argument("--models", default=None, help="Comma-separated model list")
    parser.add_argument("--limit", type=int, default=10, help="Limit number of instances")
    args = parser.parse_args()
    
    models = [m.strip() for m in args.models.split(",")] if args.models else [args.model]
    
    instances = load_swebench_lite(limit=args.limit)
    print(f"Loaded {len(instances)} SWE-bench instances.")
    
    all_results = []
    for model in models:
        print(f"\n{'='*60}\n  Evaluating model: {model}\n{'='*60}")
        results = run_benchmark(instances, model)
        all_results.extend(results)
        
    write_report(all_results, models)


if __name__ == "__main__":
    main()
