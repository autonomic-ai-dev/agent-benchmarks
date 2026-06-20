"""Comprehensive feature benchmark for the entire Autonomic AI ecosystem.

Tests EVERY feature of EVERY organ — not just health endpoints — and produces
detailed, publishable reports with feature descriptions, grading, and analysis.

Each benchmark scenario describes:
  - WHAT the feature does (for developers evaluating the tool)
  - WHY the benchmark matters (what it proves about the system)
  - HOW it's measured (methodology transparency)
  - The RESULT with grading against defined thresholds

Produces:
    benchmarks/results_ecosystem.md    (detailed publishable report)
    benchmarks/results_ecosystem.json  (agent-consumable structured data)
"""

import json
import os
import subprocess
import tempfile
import time
import statistics
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Feature definitions — the complete Autonomic feature catalog
# ---------------------------------------------------------------------------

FEATURE_CATALOG = {
    # ===== agent-brain =====
    "brain": {
        "organ": "agent-brain",
        "description": "Local MCP router for agents — manages skills, rules, memory, and context retrieval for AI coding agents.",
        "features": [
            {
                "id": "brain.index",
                "name": "Index Rebuild",
                "description": "Reindexes all local skills, rules, memories, and agent definitions into the embedded vector store. This is the foundation of context retrieval quality.",
                "why_it_matters": "A fast reindex means developers can iterate on their knowledge base without waiting. Slow indexing blocks adoption.",
                "cmd": ["agent-brain", "index"],
                "timeout": 60,
                "thresholds": {"exceptional": 3, "good": 10, "acceptable": 30},
            },
            {
                "id": "brain.stats",
                "name": "Stats Computation",
                "description": "Computes routing statistics, token savings, cache hit rates, and cost avoidance metrics from the retrieval log.",
                "why_it_matters": "Stats must be instant so developers can check their ROI at any time without disrupting workflow.",
                "cmd": ["agent-brain", "stats"],
                "timeout": 15,
                "thresholds": {"exceptional": 0.5, "good": 2, "acceptable": 5},
            },
            {
                "id": "brain.stats_json",
                "name": "Stats JSON Export",
                "description": "Same as stats but outputs structured JSON for programmatic consumption by dashboards and CI pipelines.",
                "why_it_matters": "JSON output enables automated monitoring and alerting on retrieval quality degradation.",
                "cmd": ["agent-brain", "stats", "--json"],
                "timeout": 15,
                "thresholds": {"exceptional": 0.5, "good": 2, "acceptable": 5},
                "validate_json": True,
            },
            {
                "id": "brain.gc",
                "name": "Garbage Collection",
                "description": "Deduplicates, prunes low-confidence entries, and vacuums the index database to maintain retrieval quality over time.",
                "why_it_matters": "GC prevents index bloat and retrieval quality degradation. Must be fast enough to run frequently.",
                "cmd": ["agent-brain", "gc"],
                "timeout": 30,
                "thresholds": {"exceptional": 2, "good": 10, "acceptable": 25},
            },
            {
                "id": "brain.memory_gc",
                "name": "Memory Archival (dry-run)",
                "description": "Archives stale memory facts based on age thresholds. Dry-run mode (default) previews what would be archived without mutating data.",
                "why_it_matters": "Prevents memory bloat while protecting valuable knowledge. Dry-run is safe for automated scheduling.",
                "cmd": ["agent-brain", "memory", "gc"],
                "timeout": 30,
                "thresholds": {"exceptional": 1, "good": 5, "acceptable": 15},
            },
            {
                "id": "brain.bench_ci",
                "name": "Latency Gate (CI)",
                "description": "Runs the warm-route latency benchmark on an isolated fixture database. Asserts p95 latency stays within thresholds.",
                "why_it_matters": "This is the gate that prevents latency regressions from shipping. If this passes, routing performance is guaranteed.",
                "cmd": ["agent-brain", "bench", "--ci"],
                "timeout": 120,
                "thresholds": {"exceptional": 5, "good": 15, "acceptable": 30},
            },
            {
                "id": "brain.bench_mcp",
                "name": "MCP Tool Latency",
                "description": "Benchmarks all MCP tools (route_task, get_context, token tools, graphify) and asserts they meet latency bounds.",
                "why_it_matters": "MCP tools are called on every agent turn. High latency here directly slows down every developer interaction.",
                "cmd": ["agent-brain", "bench", "--mcp", "--assert"],
                "timeout": 120,
                "thresholds": {"exceptional": 10, "good": 30, "acceptable": 60},
            },
            {
                "id": "brain.bench_scale",
                "name": "ANN Scale Benchmark",
                "description": "Tests approximate nearest neighbor search at 1k/5k/10k index sizes. Asserts p95 ≤ 50ms at 10k scale.",
                "why_it_matters": "Proves the system scales to large codebases. Enterprise users need confidence that 10k+ skills won't degrade performance.",
                "cmd": ["agent-brain", "bench", "--scale", "--assert"],
                "timeout": 120,
                "thresholds": {"exceptional": 15, "good": 30, "acceptable": 60},
            },
            {
                "id": "brain.bench_supervisor",
                "name": "Supervisor Enforcement",
                "description": "Validates that must-apply constraints and supervisor skills are correctly enforced during routing.",
                "why_it_matters": "Enterprises need guarantee that critical rules (security policies, code standards) are ALWAYS applied, never skipped.",
                "cmd": ["agent-brain", "bench", "--supervisor", "--assert"],
                "timeout": 60,
                "thresholds": {"exceptional": 5, "good": 15, "acceptable": 30},
            },
            {
                "id": "brain.bench_graphify",
                "name": "Graphify Ingest + Route",
                "description": "Benchmarks codebase graph ingest and code_context routing — the system that understands code relationships.",
                "why_it_matters": "Graph-aware context retrieval is what separates Autonomic from keyword search. Speed here determines UX quality.",
                "cmd": ["agent-brain", "bench", "--graphify", "--assert"],
                "timeout": 120,
                "thresholds": {"exceptional": 10, "good": 30, "acceptable": 60},
            },
            {
                "id": "brain.eval_ci",
                "name": "Recall@3 Gate",
                "description": "Measures whether the retrieval engine surfaces the correct skill/memory in the top 3 results. Threshold: ≥ 60%.",
                "why_it_matters": "This is the ACCURACY metric. If Recall@3 drops, the agent gets wrong context and produces worse code.",
                "cmd": ["agent-brain", "eval", "--ci"],
                "timeout": 120,
                "thresholds": {"exceptional": 10, "good": 30, "acceptable": 60},
            },
            {
                "id": "brain.config_show",
                "name": "Config Display",
                "description": "Prints the active configuration file, showing all tunable parameters.",
                "why_it_matters": "Instant config inspection supports debugging and onboarding.",
                "cmd": ["agent-brain", "config", "show"],
                "timeout": 5,
                "thresholds": {"exceptional": 0.2, "good": 1, "acceptable": 3},
            },
            {
                "id": "brain.doctor",
                "name": "Self-Diagnostics",
                "description": "Checks MCP installation, binary integrity, hooks, and codesign status.",
                "why_it_matters": "Doctor must be fast and thorough — it's the first thing developers run when something breaks.",
                "cmd": ["agent-brain", "doctor"],
                "timeout": 15,
                "thresholds": {"exceptional": 1, "good": 3, "acceptable": 10},
            },
        ],
    },

    # ===== agent-spine =====
    "spine": {
        "organ": "agent-spine",
        "description": "Stateful workflow supervision — validates, executes, and inspects YAML-defined multi-step workflows for AI agents.",
        "features": [
            {
                "id": "spine.status",
                "name": "Capability Report",
                "description": "Displays planned capabilities and current scaffold state.",
                "why_it_matters": "Instant feedback on what the system can do helps developers plan integrations.",
                "cmd": ["agent-spine", "status"],
                "timeout": 5,
                "thresholds": {"exceptional": 0.2, "good": 1, "acceptable": 3},
            },
            {
                "id": "spine.validate_valid",
                "name": "Workflow Validation (valid)",
                "description": "Parses and validates a well-formed YAML workflow definition against the schema.",
                "why_it_matters": "Fast validation enables CI integration — fail early before execution.",
                "cmd_factory": "_spine_validate_valid",
                "timeout": 10,
                "thresholds": {"exceptional": 0.3, "good": 1, "acceptable": 5},
            },
            {
                "id": "spine.validate_invalid",
                "name": "Workflow Validation (invalid)",
                "description": "Rejects a malformed YAML workflow with a clear error message.",
                "why_it_matters": "Clear error messages reduce debugging time. Reject fast, explain clearly.",
                "cmd_factory": "_spine_validate_invalid",
                "timeout": 10,
                "thresholds": {"exceptional": 0.2, "good": 1, "acceptable": 3},
                "expect_failure": True,
            },
            {
                "id": "spine.run_workflow",
                "name": "Workflow Execution",
                "description": "Executes a simple multi-step YAML workflow locally with state tracking.",
                "why_it_matters": "End-to-end workflow execution is the core value proposition of spine. Speed and reliability are critical.",
                "cmd_factory": "_spine_run_workflow",
                "timeout": 30,
                "thresholds": {"exceptional": 1, "good": 5, "acceptable": 15},
            },
            {
                "id": "spine.doctor",
                "name": "Self-Diagnostics",
                "description": "Diagnoses common setup issues with the spine installation.",
                "why_it_matters": "Fast diagnostics reduce onboarding friction.",
                "cmd": ["agent-spine", "doctor"],
                "timeout": 10,
                "thresholds": {"exceptional": 0.3, "good": 1, "acceptable": 5},
            },
        ],
    },

    # ===== agent-heart =====
    "heart": {
        "organ": "agent-heart",
        "description": "Background distillation daemon — runs GC, cluster distillation, fine-tuning, and predictive token budgets.",
        "features": [
            {
                "id": "heart.status",
                "name": "Daemon Status",
                "description": "Reports current daemon state, scheduled jobs, and health.",
                "why_it_matters": "Operators need instant visibility into background processes.",
                "cmd": ["agent-heart", "status"],
                "timeout": 5,
                "thresholds": {"exceptional": 0.2, "good": 1, "acceptable": 3},
            },
            {
                "id": "heart.gc",
                "name": "GC Cycle",
                "description": "Runs a single garbage collection cycle across the knowledge store.",
                "why_it_matters": "GC keeps the system healthy over time. Must complete reliably without blocking other operations.",
                "cmd": ["agent-heart", "gc"],
                "timeout": 30,
                "thresholds": {"exceptional": 2, "good": 10, "acceptable": 25},
            },
            {
                "id": "heart.budget_stats",
                "name": "Token Budget Stats",
                "description": "Displays historical token usage statistics from the brain retrieval log for predictive budgeting.",
                "why_it_matters": "Token budget visibility lets developers predict API costs before they spike.",
                "cmd": ["agent-heart", "budget", "stats"],
                "timeout": 10,
                "thresholds": {"exceptional": 0.5, "good": 2, "acceptable": 5},
            },
        ],
    },

    # ===== agent-nerves =====
    "nerves": {
        "organ": "agent-nerves",
        "description": "Distributed event bus — manages NATS/JetStream broker health, event filtering, stream inspection, and cluster coordination.",
        "features": [
            {
                "id": "nerves.status",
                "name": "Configuration Report",
                "description": "Prints NATS connection config, broker URL, and cluster state.",
                "why_it_matters": "Instant config visibility is essential for diagnosing connectivity issues.",
                "cmd": ["agent-nerves", "status"],
                "timeout": 5,
                "thresholds": {"exceptional": 0.2, "good": 1, "acceptable": 3},
            },
            {
                "id": "nerves.filter_list",
                "name": "Event Filter Registry",
                "description": "Lists all loaded event filter rules (JSON + WASM) that govern message routing.",
                "why_it_matters": "Filter visibility prevents silent message drops in production.",
                "cmd": ["agent-nerves", "filter", "list"],
                "timeout": 5,
                "thresholds": {"exceptional": 0.2, "good": 1, "acceptable": 3},
            },
            {
                "id": "nerves.cluster_status",
                "name": "Cluster Status",
                "description": "Shows multi-node cluster state: leader, peers, WireGuard tunnels.",
                "why_it_matters": "Cluster health visibility is critical for distributed deployments.",
                "cmd": ["agent-nerves", "cluster", "status"],
                "timeout": 10,
                "thresholds": {"exceptional": 0.3, "good": 2, "acceptable": 5},
            },
        ],
    },

    # ===== agent-muscle =====
    "muscle": {
        "organ": "agent-muscle",
        "description": "Remote actuator — executes commands, runs LoRA fine-tuning (MLX/candle), validates training datasets, and manages K8s GPU jobs.",
        "features": [
            {
                "id": "muscle.status",
                "name": "Actuator Status",
                "description": "Reports actuator daemon state and available backends.",
                "why_it_matters": "Operators need to know which execution backends are available.",
                "cmd": ["agent-muscle", "status"],
                "timeout": 5,
                "thresholds": {"exceptional": 0.2, "good": 1, "acceptable": 3},
            },
            {
                "id": "muscle.run_echo",
                "name": "Command Execution",
                "description": "Executes a simple command and streams output. Tests the core actuator pipeline.",
                "why_it_matters": "Command execution latency directly impacts agent responsiveness during tool use.",
                "cmd": ["agent-muscle", "run", "echo", "benchmark_test"],
                "timeout": 10,
                "thresholds": {"exceptional": 0.3, "good": 1, "acceptable": 5},
                "validate_stdout": "benchmark_test",
            },
            {
                "id": "muscle.validate_dataset",
                "name": "Training Data Validation",
                "description": "Validates JSONL training data format and structure without running training.",
                "why_it_matters": "Catching data issues before an expensive GPU training run saves hours and money.",
                "cmd_factory": "_muscle_validate_dataset",
                "timeout": 10,
                "thresholds": {"exceptional": 0.3, "good": 1, "acceptable": 5},
            },
            {
                "id": "muscle.validate_only",
                "name": "Training Dry Run",
                "description": "Runs the full training pipeline validation without actually training — checks model availability, data format, config.",
                "why_it_matters": "Prevents wasted GPU hours on misconfigured training runs.",
                "cmd_factory": "_muscle_train_validate",
                "timeout": 15,
                "thresholds": {"exceptional": 1, "good": 5, "acceptable": 10},
            },
        ],
    },

    # ===== agent-immune =====
    "immune": {
        "organ": "agent-immune",
        "description": "Dependency fuzzing & security sandbox — scans manifests for vulnerabilities, runs scripts in network-isolated sandboxes, and verifies memory safety.",
        "features": [
            {
                "id": "immune.status",
                "name": "Security Status",
                "description": "Reports scanner configuration and available security features.",
                "why_it_matters": "Security posture visibility is a compliance requirement.",
                "cmd": ["agent-immune", "status"],
                "timeout": 5,
                "thresholds": {"exceptional": 0.2, "good": 1, "acceptable": 3},
            },
            {
                "id": "immune.scan_cargo",
                "name": "Rust Dependency Scan",
                "description": "Scans a Cargo.toml manifest for known vulnerable dependencies against advisory databases.",
                "why_it_matters": "Automated vulnerability scanning prevents shipping known CVEs. Speed enables CI integration.",
                "cmd_factory": "_immune_scan_cargo",
                "timeout": 30,
                "thresholds": {"exceptional": 1, "good": 5, "acceptable": 15},
            },
            {
                "id": "immune.scan_npm",
                "name": "Node.js Dependency Scan",
                "description": "Scans a package.json manifest for known vulnerable npm dependencies.",
                "why_it_matters": "npm ecosystem has the highest CVE density. Fast scanning is critical for JavaScript projects.",
                "cmd_factory": "_immune_scan_npm",
                "timeout": 30,
                "thresholds": {"exceptional": 1, "good": 5, "acceptable": 15},
            },
            {
                "id": "immune.sandbox",
                "name": "Network-Isolated Sandbox",
                "description": "Executes a script in a network-isolated sandbox (Linux unshare, macOS fallback). Prevents untrusted code from making network calls.",
                "why_it_matters": "Sandboxed execution is the safety net for AI-generated code. Latency overhead must be minimal.",
                "cmd_factory": "_immune_sandbox",
                "timeout": 15,
                "thresholds": {"exceptional": 0.5, "good": 2, "acceptable": 10},
            },
            {
                "id": "immune.verify_memory",
                "name": "Memory Growth Verification",
                "description": "Checks for runaway memory growth in scripts — a dataset quality gate.",
                "why_it_matters": "Prevents OOM kills in production from poorly written generated code.",
                "cmd": ["agent-immune", "verify-memory"],
                "timeout": 15,
                "thresholds": {"exceptional": 1, "good": 3, "acceptable": 10},
            },
        ],
    },

    # ===== agent-eyes =====
    "eyes": {
        "organ": "agent-eyes",
        "description": "Observability and visual QA — captures screenshots, performs pixel diffs, indexes DOM elements, and runs local vision models.",
        "features": [
            {
                "id": "eyes.status",
                "name": "Telemetry Status",
                "description": "Reports telemetry daemon configuration and available visual backends.",
                "why_it_matters": "Developers need to know which visual QA features are available on their system.",
                "cmd": ["agent-eyes", "status"],
                "timeout": 5,
                "thresholds": {"exceptional": 0.2, "good": 1, "acceptable": 3},
            },
            {
                "id": "eyes.describe_html",
                "name": "HTML Structure Extraction",
                "description": "Analyzes an HTML file and extracts its DOM structure, element counts, and interactive elements.",
                "why_it_matters": "Fast DOM analysis enables AI agents to understand web pages without a browser. Critical for UI testing.",
                "cmd_factory": "_eyes_describe_html",
                "timeout": 10,
                "thresholds": {"exceptional": 0.3, "good": 2, "acceptable": 5},
            },
            {
                "id": "eyes.dom_index",
                "name": "DOM Index & Search",
                "description": "Indexes all DOM elements from an HTML file into a searchable SQLite database for element lookup.",
                "why_it_matters": "Indexed DOM enables precise element targeting without full page re-parse. Essential for UI automation.",
                "cmd_factory": "_eyes_dom_index",
                "timeout": 15,
                "thresholds": {"exceptional": 0.5, "good": 3, "acceptable": 10},
            },
        ],
    },

    # ===== agent-mouth =====
    "mouth": {
        "organ": "agent-mouth",
        "description": "Communication and notification daemon — validates commands against AST policies, sends webhooks, and summarizes logs.",
        "features": [
            {
                "id": "mouth.status",
                "name": "Communication Status",
                "description": "Reports webhook listener configuration and notification channels.",
                "why_it_matters": "Operators need to verify notification channels are configured before relying on them.",
                "cmd": ["agent-mouth", "status"],
                "timeout": 5,
                "thresholds": {"exceptional": 0.2, "good": 1, "acceptable": 3},
            },
            {
                "id": "mouth.validate_safe",
                "name": "Command Validation (safe)",
                "description": "Validates a bash command against the AST-based approval policy. Safe commands should pass instantly.",
                "why_it_matters": "Fast command validation enables real-time agent supervision without blocking execution.",
                "cmd": ["agent-mouth", "validate", "echo hello world"],
                "timeout": 5,
                "thresholds": {"exceptional": 0.1, "good": 0.5, "acceptable": 2},
            },
            {
                "id": "mouth.validate_dangerous",
                "name": "Command Validation (dangerous)",
                "description": "Validates a dangerous command (rm -rf /) — must be rejected by the AST policy.",
                "why_it_matters": "Security-critical: dangerous commands must NEVER pass validation. Speed matters less than correctness here.",
                "cmd": ["agent-mouth", "validate", "rm -rf /"],
                "timeout": 5,
                "thresholds": {"exceptional": 0.1, "good": 0.5, "acceptable": 2},
                "expect_failure": True,
            },
            {
                "id": "mouth.summarize",
                "name": "Log Summarization",
                "description": "Reads log input from stdin and produces a human-readable summary of events, errors, and patterns.",
                "why_it_matters": "Automated log summarization saves operators hours of manual log reading.",
                "cmd_factory": "_mouth_summarize",
                "timeout": 15,
                "thresholds": {"exceptional": 0.5, "good": 3, "acceptable": 10},
            },
        ],
    },

    # ===== agent-body (autonomic) =====
    "body": {
        "organ": "autonomic",
        "description": "Ecosystem manager — initializes workspaces, supervises daemons, runs health checks, and coordinates the entire biological architecture.",
        "features": [
            {
                "id": "body.doctor",
                "name": "Ecosystem Health Check",
                "description": "Verifies all organ binaries are on PATH, executable, and return valid version strings.",
                "why_it_matters": "The first thing any developer runs. Must be fast, thorough, and give actionable output.",
                "cmd": ["autonomic", "doctor"],
                "timeout": 15,
                "thresholds": {"exceptional": 1, "good": 3, "acceptable": 10},
            },
            {
                "id": "body.update",
                "name": "Version Report",
                "description": "Lists installed versions of all organ binaries on PATH.",
                "why_it_matters": "Version visibility is essential for debugging and ensuring consistent deployments.",
                "cmd": ["autonomic", "update"],
                "timeout": 10,
                "thresholds": {"exceptional": 0.5, "good": 2, "acceptable": 5},
            },
            {
                "id": "body.status",
                "name": "Supervisor Status",
                "description": "Shows workspace paths and daemon supervisor state table.",
                "why_it_matters": "Operators need a single command to see the full system state.",
                "cmd": ["autonomic", "status"],
                "timeout": 10,
                "thresholds": {"exceptional": 0.5, "good": 2, "acceptable": 5},
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# Command factories (for tests that need temp files)
# ---------------------------------------------------------------------------

def _spine_validate_valid(tmp_dir: str) -> list[str]:
    wf = os.path.join(tmp_dir, "valid.yml")
    with open(wf, "w") as f:
        f.write("name: benchmark\nsteps:\n  - name: greet\n    run: echo hello\n  - name: count\n    run: seq 5\n")
    return ["agent-spine", "validate", wf]


def _spine_validate_invalid(tmp_dir: str) -> list[str]:
    wf = os.path.join(tmp_dir, "invalid.yml")
    with open(wf, "w") as f:
        f.write("this: [[[is not valid yaml\nsteps: broken\n")
    return ["agent-spine", "validate", wf]


def _spine_run_workflow(tmp_dir: str) -> list[str]:
    wf = os.path.join(tmp_dir, "run.yml")
    with open(wf, "w") as f:
        f.write("name: benchmark_run\nsteps:\n  - name: greet\n    run: echo benchmarking\n  - name: date\n    run: date\n")
    return ["agent-spine", "run", wf]


def _muscle_validate_dataset(tmp_dir: str) -> list[str]:
    ds = os.path.join(tmp_dir, "train.jsonl")
    entries = [{"prompt": f"Task {i}", "completion": f"Done {i}"} for i in range(10)]
    with open(ds, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return ["agent-muscle", "validate", ds]


def _muscle_train_validate(tmp_dir: str) -> list[str]:
    ds = os.path.join(tmp_dir, "train_data")
    os.makedirs(ds, exist_ok=True)
    train_file = os.path.join(ds, "train.jsonl")
    entries = [{"prompt": f"Task {i}", "completion": f"Done {i}"} for i in range(5)]
    with open(train_file, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return ["agent-muscle", "train", "--data", ds, "--validate-only"]


def _immune_scan_cargo(tmp_dir: str) -> list[str]:
    cargo = os.path.join(tmp_dir, "Cargo.toml")
    with open(cargo, "w") as f:
        f.write('[package]\nname = "bench"\nversion = "0.1.0"\n\n[dependencies]\nserde = "1.0"\ntokio = "1.0"\nreqwest = "0.11"\nclap = "4.0"\n')
    return ["agent-immune", "scan", cargo]


def _immune_scan_npm(tmp_dir: str) -> list[str]:
    pkg = os.path.join(tmp_dir, "package.json")
    with open(pkg, "w") as f:
        f.write('{"name":"bench","version":"1.0.0","dependencies":{"express":"4.18.0","lodash":"4.17.21","axios":"1.6.0"}}')
    return ["agent-immune", "scan", pkg]


def _immune_sandbox(tmp_dir: str) -> list[str]:
    script = os.path.join(tmp_dir, "safe.sh")
    with open(script, "w") as f:
        f.write("#!/bin/bash\necho 'sandboxed execution'\ndate\n")
    os.chmod(script, 0o755)
    return ["agent-immune", "sandbox", script]


def _eyes_describe_html(tmp_dir: str) -> list[str]:
    html = os.path.join(tmp_dir, "page.html")
    with open(html, "w") as f:
        f.write('<!DOCTYPE html><html><head><title>Bench</title></head><body>'
                '<h1>Title</h1><p>Paragraph</p><button id="submit">Go</button>'
                '<input type="text" name="q"/><a href="/link">Link</a></body></html>')
    return ["agent-eyes", "describe", html]


def _eyes_dom_index(tmp_dir: str) -> list[str]:
    html = os.path.join(tmp_dir, "index.html")
    with open(html, "w") as f:
        f.write('<!DOCTYPE html><html><body>'
                '<nav><a href="/">Home</a><a href="/about">About</a></nav>'
                '<main><h1>Page</h1><form><input name="email"/><button>Submit</button></form></main>'
                '</body></html>')
    return ["agent-eyes", "dom", "index", "--file", html]


def _mouth_summarize(tmp_dir: str) -> list[str]:
    # This one uses stdin, handled specially
    return ["agent-mouth", "summarize"]


FACTORIES = {
    "_spine_validate_valid": _spine_validate_valid,
    "_spine_validate_invalid": _spine_validate_invalid,
    "_spine_run_workflow": _spine_run_workflow,
    "_muscle_validate_dataset": _muscle_validate_dataset,
    "_muscle_train_validate": _muscle_train_validate,
    "_immune_scan_cargo": _immune_scan_cargo,
    "_immune_scan_npm": _immune_scan_npm,
    "_immune_sandbox": _immune_sandbox,
    "_eyes_describe_html": _eyes_describe_html,
    "_eyes_dom_index": _eyes_dom_index,
    "_mouth_summarize": _mouth_summarize,
}


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------

GRADE_ICONS = {"exceptional": "⭐", "good": "✅", "acceptable": "🟡", "poor": "🔴"}


def grade_latency(elapsed_s: float, thresholds: dict) -> str:
    if elapsed_s <= thresholds["exceptional"]:
        return "exceptional"
    elif elapsed_s <= thresholds["good"]:
        return "good"
    elif elapsed_s <= thresholds["acceptable"]:
        return "acceptable"
    return "poor"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FeatureResult:
    feature_id: str
    feature_name: str
    organ: str
    organ_description: str
    feature_description: str
    why_it_matters: str
    exit_code: int
    passed: bool
    elapsed_s: float
    grade: str
    thresholds: dict
    stdout_tail: str
    stderr_tail: str
    json_valid: Optional[bool]
    error_summary: Optional[str]
    fix_suggestion: Optional[str]


def run_feature(organ_key: str, organ_info: dict, feature: dict, tmp_dir: str) -> FeatureResult:
    """Run a single feature benchmark."""
    # Resolve command
    if "cmd" in feature:
        cmd = feature["cmd"]
    elif "cmd_factory" in feature:
        cmd = FACTORIES[feature["cmd_factory"]](tmp_dir)
    else:
        raise ValueError(f"No cmd for {feature['id']}")

    # Handle stdin for summarize
    stdin_data = None
    if feature["id"] == "mouth.summarize":
        stdin_data = "2026-06-20 INFO startup complete\n2026-06-20 WARN high memory usage\n2026-06-20 ERROR connection timeout\n2026-06-20 INFO recovered\n" * 50

    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=feature["timeout"],
            input=stdin_data,
        )
        elapsed = time.perf_counter() - start
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        return FeatureResult(
            feature_id=feature["id"], feature_name=feature["name"],
            organ=organ_info["organ"], organ_description=organ_info["description"],
            feature_description=feature["description"], why_it_matters=feature["why_it_matters"],
            exit_code=124, passed=False, elapsed_s=round(elapsed, 3), grade="poor",
            thresholds=feature["thresholds"],
            stdout_tail="", stderr_tail="TIMEOUT",
            json_valid=None,
            error_summary=f"Timed out after {feature['timeout']}s",
            fix_suggestion=f"Profile {feature['id']} for CPU/IO bottlenecks. Consider async or batched processing.",
        )

    expect_failure = feature.get("expect_failure", False)
    passed = (result.returncode != 0) if expect_failure else (result.returncode == 0)

    # Validate JSON output if required
    json_valid = None
    if feature.get("validate_json") and passed:
        try:
            json.loads(result.stdout)
            json_valid = True
        except (json.JSONDecodeError, ValueError):
            json_valid = False
            passed = False

    # Validate stdout content if required
    if feature.get("validate_stdout") and passed:
        if feature["validate_stdout"] not in result.stdout:
            passed = False

    grade = grade_latency(elapsed, feature["thresholds"]) if passed else "poor"

    error_summary = None
    fix_suggestion = None
    if not passed:
        error_summary = _extract_error(result.stderr, result.stdout)
        fix_suggestion = f"Feature '{feature['name']}' failed. Check {organ_info['organ']} source for the error: {error_summary[:100]}"

    return FeatureResult(
        feature_id=feature["id"], feature_name=feature["name"],
        organ=organ_info["organ"], organ_description=organ_info["description"],
        feature_description=feature["description"], why_it_matters=feature["why_it_matters"],
        exit_code=result.returncode, passed=passed, elapsed_s=round(elapsed, 3), grade=grade,
        thresholds=feature["thresholds"],
        stdout_tail=result.stdout[-300:] if result.stdout else "",
        stderr_tail=result.stderr[-300:] if result.stderr else "",
        json_valid=json_valid, error_summary=error_summary, fix_suggestion=fix_suggestion,
    )


def _extract_error(stderr: str, stdout: str) -> str:
    for line in (stderr + stdout).split("\n"):
        lower = line.lower()
        if any(kw in lower for kw in ["error", "panic", "fatal", "failed"]):
            return line.strip()[:200]
    return stderr[-200:].strip() if stderr else "Unknown error"


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def write_reports(results: list[FeatureResult]):
    os.makedirs("benchmarks", exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    # --- JSON ---
    json_data = {
        "generated_at": timestamp,
        "total_features": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
        "grades": {g: sum(1 for r in results if r.grade == g) for g in GRADE_ICONS},
        "results": [asdict(r) for r in results],
        "failures": [
            {"feature_id": r.feature_id, "organ": r.organ, "error": r.error_summary, "fix": r.fix_suggestion}
            for r in results if not r.passed
        ],
    }
    with open("benchmarks/results_ecosystem.json", "w") as f:
        json.dump(json_data, f, indent=2)

    # --- Markdown ---
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    total = len(results)

    md = f"""# Autonomic AI — Comprehensive Ecosystem Benchmark

_Generated at: {timestamp}_

> Every feature of every organ, tested and graded. These are not synthetic
> micro-benchmarks — each test exercises real CLI operations with real data.

**Overall: {passed}/{total} features passing** ({failed} failures)

## Grade Distribution

| Grade | Count | Meaning |
|---|---|---|
| ⭐ Exceptional | {sum(1 for r in results if r.grade == 'exceptional')} | Exceeds developer expectations |
| ✅ Good | {sum(1 for r in results if r.grade == 'good')} | Meets expectations |
| 🟡 Acceptable | {sum(1 for r in results if r.grade == 'acceptable')} | Minimum adoption bar |
| 🔴 Poor | {sum(1 for r in results if r.grade == 'poor')} | Needs investigation |

---

"""

    # Group by organ
    organs_seen = []
    for organ_key, organ_info in FEATURE_CATALOG.items():
        organ_results = [r for r in results if r.feature_id.startswith(organ_key + ".")]
        if not organ_results:
            continue
        organs_seen.append(organ_key)
        organ_passed = sum(1 for r in organ_results if r.passed)
        organ_total = len(organ_results)

        md += f"""## {organ_info['organ']} — {organ_passed}/{organ_total} passing

> {organ_info['description']}

| Feature | Time | Grade | Threshold (⭐/✅/🟡) | Description |
|---|---|---|---|---|
"""
        for r in organ_results:
            icon = GRADE_ICONS[r.grade]
            status = "✓" if r.passed else "✗"
            t = r.thresholds
            md += (
                f"| {status} {r.feature_name} | {r.elapsed_s}s | {icon} "
                f"| ≤{t['exceptional']}s / ≤{t['good']}s / ≤{t['acceptable']}s "
                f"| {r.feature_description[:80]}… |\n"
            )

        md += "\n"

        # Detailed feature analysis for this organ
        md += f"<details><summary>📋 Detailed Feature Analysis — {organ_info['organ']}</summary>\n\n"
        for r in organ_results:
            icon = GRADE_ICONS[r.grade]
            md += f"### {icon} {r.feature_name} (`{r.feature_id}`)\n\n"
            md += f"**What:** {r.feature_description}\n\n"
            md += f"**Why it matters:** {r.why_it_matters}\n\n"
            md += f"**Result:** {r.elapsed_s}s — graded **{r.grade}** "
            md += f"(thresholds: ⭐ ≤{r.thresholds['exceptional']}s, ✅ ≤{r.thresholds['good']}s, 🟡 ≤{r.thresholds['acceptable']}s)\n\n"
            if not r.passed and r.error_summary:
                md += f"> ⚠️ **Error:** `{r.error_summary}`\n>\n"
                md += f"> **Fix:** {r.fix_suggestion}\n\n"
        md += "</details>\n\n---\n\n"

    # Failures section
    failures = [r for r in results if not r.passed]
    if failures:
        md += "## ⚠️ Failures Requiring Attention\n\n"
        md += "```json\n"
        md += json.dumps(
            [{"feature_id": r.feature_id, "organ": r.organ, "error": r.error_summary, "fix": r.fix_suggestion}
             for r in failures],
            indent=2,
        )
        md += "\n```\n"

    with open("benchmarks/results_ecosystem.md", "w") as f:
        f.write(md)

    print(f"\nReports written:")
    print(f"  benchmarks/results_ecosystem.md  ({len(md)} chars)")
    print(f"  benchmarks/results_ecosystem.json")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Autonomic Ecosystem Feature Benchmark")
    parser.add_argument("--organs", nargs="*", default=None, help="Specific organs to test (default: all)")
    parser.add_argument("--features", nargs="*", default=None, help="Specific feature IDs to test")
    args = parser.parse_args()

    tmp_dir = tempfile.mkdtemp(prefix="autonomic_bench_")
    results: list[FeatureResult] = []

    catalog = FEATURE_CATALOG
    if args.organs:
        catalog = {k: v for k, v in catalog.items() if k in args.organs}

    total_features = sum(len(o["features"]) for o in catalog.values())
    current = 0

    for organ_key, organ_info in catalog.items():
        print(f"\n{'='*70}")
        print(f"  {organ_info['organ'].upper()} — {organ_info['description'][:60]}")
        print(f"{'='*70}")

        for feature in organ_info["features"]:
            if args.features and feature["id"] not in args.features:
                continue
            current += 1
            print(f"\n  [{current}/{total_features}] {feature['name']} ({feature['id']})")

            r = run_feature(organ_key, organ_info, feature, tmp_dir)
            results.append(r)

            icon = GRADE_ICONS[r.grade]
            status = "✓" if r.passed else "✗"
            print(f"    {status} {icon} {r.elapsed_s}s")

    write_reports(results)

    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    print(f"\n{'='*60}")
    print(f"  ECOSYSTEM BENCHMARK COMPLETE")
    print(f"  {passed}✓  {failed}✗  ({len(results)} features tested)")
    for g in ["exceptional", "good", "acceptable", "poor"]:
        count = sum(1 for r in results if r.grade == g)
        if count:
            print(f"  {GRADE_ICONS[g]} {g}: {count}")
    print(f"{'='*60}")

    if failed > 0:
        exit(1)


if __name__ == "__main__":
    main()
