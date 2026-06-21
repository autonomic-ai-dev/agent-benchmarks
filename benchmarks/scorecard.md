# 🏆 Autonomic AI Scorecard

_Generated at: 2026-06-21 04:45:29 UTC_

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
| Recall@3 | ≥ 90% | ≥ 75% | ≥ 60% | — | — |
| Route p95 Latency | ≤ 5ms | ≤ 20ms | ≤ 50ms | — | — |
| Scale 10k p95 | ≤ 15ms | ≤ 30ms | ≤ 50ms | — | — |
| Token Savings | ≥ 95% | ≥ 80% | ≥ 50% | — | — |
| Model Enhancement (keyword accuracy) | ≥ 30% pts | ≥ 15% pts | ≥ 5% pts | — | — |
| Cold Startup | ≤ 2s | ≤ 5s | ≤ 15s | — | — |

> [!NOTE]
> Metrics marked "—" require running the corresponding benchmark first.
> Use `task all` to populate all metrics.

---

## System Health

| Check | Result |
|---|---|
| Binary Health | 9/9 organs installed |
| Brain Benchmarks | 0 passed, 0 failed |
| Accuracy Evals | 0 passed, 0 failed |
| Ecosystem Features | 43/43 features passed |
| Resource Matrix | 26/26 scenarios passed |

### Resource Matrix Grade Distribution

| Grade | Count |
|---|---|
| ⭐ Exceptional | 26 |
| ✅ Good | 0 |
| 🟡 Acceptable | 0 |
| 🔴 Poor | 0 |

---

## Performance

| Metric | Value |
|---|---|
| Index Size | N/A items |
| Active Memories | N/A |
| Route p95 Latency | N/A ms |

## Value

| Metric | Value |
|---|---|
| Token Savings | N/A |
| Est. Cost Avoided | N/A |

---

## Architecture Claims

# 🏛 Architecture Claims Benchmark
## ✅ VALIDATED: Fault Isolation (Anti-Monolith Trap)
## ✅ VALIDATED: Deterministic Execution (No Magic Prompts)
## ✅ VALIDATED: 100% Local Data Sovereignty

---

## Ecosystem Feature Details

# Autonomic AI — Comprehensive Ecosystem Benchmark
## Grade Distribution
| Grade | Count | Meaning |
|---|---|---|
| ⭐ Exceptional | 39 | Exceeds developer expectations |
| ✅ Good | 3 | Meets expectations |
| 🟡 Acceptable | 0 | Minimum adoption bar |
| 🔴 Poor | 1 | Needs investigation |
## agent-brain — 13/13 passing
| Feature | Time | Grade | Threshold (⭐/✅/🟡) | Description |
|---|---|---|---|---|
| ✓ Index Rebuild | 35.53s | 🔴 | ≤3s / ≤10s / ≤30s | Reindexes all local skills, rules, memories, and agent definitions into the embe… |
| ✓ Stats Computation | 0.017s | ⭐ | ≤0.5s / ≤2s / ≤5s | Computes routing statistics, token savings, cache hit rates, and cost avoidance … |
| ✓ Stats JSON Export | 0.01s | ⭐ | ≤0.5s / ≤2s / ≤5s | Same as stats but outputs structured JSON for programmatic consumption by dashbo… |
| ✓ Garbage Collection | 0.214s | ⭐ | ≤2s / ≤10s / ≤25s | Deduplicates, prunes low-confidence entries, and vacuums the index database to m… |
| ✓ Memory Archival (dry-run) | 0.008s | ⭐ | ≤1s / ≤5s / ≤15s | Archives stale memory facts based on age thresholds. Dry-run mode (default) prev… |
| ✓ Latency Gate (CI) | 0.157s | ⭐ | ≤5s / ≤15s / ≤30s | Runs the warm-route latency benchmark on an isolated fixture database. Asserts p… |
| ✓ MCP Tool Latency | 0.376s | ⭐ | ≤10s / ≤30s / ≤60s | Benchmarks all MCP tools (route_task, get_context, token tools, graphify) and as… |
| ✓ ANN Scale Benchmark | 0.338s | ⭐ | ≤15s / ≤30s / ≤60s | Tests approximate nearest neighbor search at 1k/5k/10k index sizes. Asserts p95 … |
| ✓ Supervisor Enforcement | 0.545s | ⭐ | ≤5s / ≤15s / ≤30s | Validates that must-apply constraints and supervisor skills are correctly enforc… |
| ✓ Graphify Ingest + Route | 0.202s | ⭐ | ≤10s / ≤30s / ≤60s | Benchmarks codebase graph ingest and code_context routing — the system that unde… |
| ✓ Recall@3 Gate | 0.026s | ⭐ | ≤10s / ≤30s / ≤60s | Measures whether the retrieval engine surfaces the correct skill/memory in the t… |
| ✓ Config Display | 0.007s | ⭐ | ≤0.2s / ≤1s / ≤3s | Prints the active configuration file, showing all tunable parameters.… |
| ✓ Self-Diagnostics | 0.779s | ⭐ | ≤1s / ≤3s / ≤10s | Checks MCP installation, binary integrity, hooks, and codesign status.… |
### 🔴 Index Rebuild (`brain.index`)
### ⭐ Stats Computation (`brain.stats`)
### ⭐ Stats JSON Export (`brain.stats_json`)
### ⭐ Garbage Collection (`brain.gc`)
### ⭐ Memory Archival (dry-run) (`brain.memory_gc`)
### ⭐ Latency Gate (CI) (`brain.bench_ci`)
### ⭐ MCP Tool Latency (`brain.bench_mcp`)
### ⭐ ANN Scale Benchmark (`brain.bench_scale`)
### ⭐ Supervisor Enforcement (`brain.bench_supervisor`)
### ⭐ Graphify Ingest + Route (`brain.bench_graphify`)
### ⭐ Recall@3 Gate (`brain.eval_ci`)
### ⭐ Config Display (`brain.config_show`)
### ⭐ Self-Diagnostics (`brain.doctor`)
## agent-spine — 5/5 passing
| Feature | Time | Grade | Threshold (⭐/✅/🟡) | Description |
|---|---|---|---|---|
| ✓ Capability Report | 0.014s | ⭐ | ≤0.2s / ≤1s / ≤3s | Displays planned capabilities and current scaffold state.… |
| ✓ Workflow Validation (valid) | 0.008s | ⭐ | ≤0.3s / ≤1s / ≤5s | Parses and validates a well-formed YAML workflow definition against the schema.… |
| ✓ Workflow Validation (invalid) | 0.006s | ⭐ | ≤0.2s / ≤1s / ≤3s | Rejects a malformed YAML workflow with a clear error message.… |
| ✓ Workflow Execution | 0.116s | ⭐ | ≤1s / ≤5s / ≤15s | Executes a simple multi-step YAML workflow locally with state tracking.… |
| ✓ Self-Diagnostics | 0.656s | ✅ | ≤0.3s / ≤1s / ≤5s | Diagnoses common setup issues with the spine installation.… |
### ⭐ Capability Report (`spine.status`)
### ⭐ Workflow Validation (valid) (`spine.validate_valid`)
### ⭐ Workflow Validation (invalid) (`spine.validate_invalid`)
### ⭐ Workflow Execution (`spine.run_workflow`)
### ✅ Self-Diagnostics (`spine.doctor`)
## agent-heart — 3/3 passing
| Feature | Time | Grade | Threshold (⭐/✅/🟡) | Description |
|---|---|---|---|---|
| ✓ Daemon Status | 0.025s | ⭐ | ≤0.2s / ≤1s / ≤3s | Reports current daemon state, scheduled jobs, and health.… |
| ✓ GC Cycle | 0.023s | ⭐ | ≤2s / ≤10s / ≤25s | Runs a single garbage collection cycle across the knowledge store.… |
| ✓ Token Budget Stats | 0.011s | ⭐ | ≤0.5s / ≤2s / ≤5s | Displays historical token usage statistics from the brain retrieval log for pred… |
### ⭐ Daemon Status (`heart.status`)
### ⭐ GC Cycle (`heart.gc`)
### ⭐ Token Budget Stats (`heart.budget_stats`)
## agent-nerves — 3/3 passing
| Feature | Time | Grade | Threshold (⭐/✅/🟡) | Description |
|---|---|---|---|---|
| ✓ Configuration Report | 0.028s | ⭐ | ≤0.2s / ≤1s / ≤3s | Prints NATS connection config, broker URL, and cluster state.… |
| ✓ Event Filter Registry | 0.006s | ⭐ | ≤0.2s / ≤1s / ≤3s | Lists all loaded event filter rules (JSON + WASM) that govern message routing.… |
| ✓ Cluster Status | 0.006s | ⭐ | ≤0.3s / ≤2s / ≤5s | Shows multi-node cluster state: leader, peers, WireGuard tunnels.… |
### ⭐ Configuration Report (`nerves.status`)
### ⭐ Event Filter Registry (`nerves.filter_list`)
### ⭐ Cluster Status (`nerves.cluster_status`)
## agent-muscle — 4/4 passing
| Feature | Time | Grade | Threshold (⭐/✅/🟡) | Description |
|---|---|---|---|---|
| ✓ Actuator Status | 0.015s | ⭐ | ≤0.2s / ≤1s / ≤3s | Reports actuator daemon state and available backends.… |
| ✓ Command Execution | 0.012s | ⭐ | ≤0.3s / ≤1s / ≤5s | Executes a simple command and streams output. Tests the core actuator pipeline.… |
| ✓ Training Data Validation | 0.005s | ⭐ | ≤0.3s / ≤1s / ≤5s | Validates JSONL training data format and structure without running training.… |
| ✓ Training Dry Run | 0.006s | ⭐ | ≤1s / ≤5s / ≤10s | Runs the full training pipeline validation without actually training — checks mo… |
### ⭐ Actuator Status (`muscle.status`)
### ⭐ Command Execution (`muscle.run_echo`)
### ⭐ Training Data Validation (`muscle.validate_dataset`)
### ⭐ Training Dry Run (`muscle.validate_only`)
## agent-immune — 5/5 passing
| Feature | Time | Grade | Threshold (⭐/✅/🟡) | Description |
|---|---|---|---|---|
| ✓ Security Status | 0.018s | ⭐ | ≤0.2s / ≤1s / ≤3s | Reports scanner configuration and available security features.… |
| ✓ Rust Dependency Scan | 1.632s | ✅ | ≤1s / ≤5s / ≤15s | Scans a Cargo.toml manifest for known vulnerable dependencies against advisory d… |
| ✓ Node.js Dependency Scan | 2.528s | ✅ | ≤1s / ≤5s / ≤15s | Scans a package.json manifest for known vulnerable npm dependencies.… |
| ✓ Network-Isolated Sandbox | 0.034s | ⭐ | ≤0.5s / ≤2s / ≤10s | Executes a script in a network-isolated sandbox (Linux unshare, macOS fallback).… |
| ✓ Memory Growth Verification | 0.216s | ⭐ | ≤1s / ≤3s / ≤10s | Checks for runaway memory growth in scripts — a dataset quality gate.… |
### ⭐ Security Status (`immune.status`)
### ✅ Rust Dependency Scan (`immune.scan_cargo`)
### ✅ Node.js Dependency Scan (`immune.scan_npm`)
### ⭐ Network-Isolated Sandbox (`immune.sandbox`)
### ⭐ Memory Growth Verification (`immune.verify_memory`)
## agent-eyes — 3/3 passing
| Feature | Time | Grade | Threshold (⭐/✅/🟡) | Description |
|---|---|---|---|---|
| ✓ Telemetry Status | 0.033s | ⭐ | ≤0.2s / ≤1s / ≤3s | Reports telemetry daemon configuration and available visual backends.… |
| ✓ HTML Structure Extraction | 0.008s | ⭐ | ≤0.3s / ≤2s / ≤5s | Analyzes an HTML file and extracts its DOM structure, element counts, and intera… |
| ✓ DOM Index & Search | 0.025s | ⭐ | ≤0.5s / ≤3s / ≤10s | Indexes all DOM elements from an HTML file into a searchable SQLite database for… |
### ⭐ Telemetry Status (`eyes.status`)
### ⭐ HTML Structure Extraction (`eyes.describe_html`)
### ⭐ DOM Index & Search (`eyes.dom_index`)
## agent-mouth — 4/4 passing
| Feature | Time | Grade | Threshold (⭐/✅/🟡) | Description |
|---|---|---|---|---|
| ✓ Communication Status | 0.024s | ⭐ | ≤0.2s / ≤1s / ≤3s | Reports webhook listener configuration and notification channels.… |
| ✓ Command Validation (safe) | 0.011s | ⭐ | ≤0.1s / ≤0.5s / ≤2s | Validates a bash command against the AST-based approval policy. Safe commands sh… |
| ✓ Command Validation (dangerous) | 0.007s | ⭐ | ≤0.1s / ≤0.5s / ≤2s | Validates a dangerous command (rm -rf /) — must be rejected by the AST policy.… |
| ✓ Log Summarization | 0.006s | ⭐ | ≤0.5s / ≤3s / ≤10s | Reads log input from stdin and produces a human-readable summary of events, erro… |
### ⭐ Communication Status (`mouth.status`)
### ⭐ Command Validation (safe) (`mouth.validate_safe`)
### ⭐ Command Validation (dangerous) (`mouth.validate_dangerous`)
### ⭐ Log Summarization (`mouth.summarize`)
## autonomic — 3/3 passing
| Feature | Time | Grade | Threshold (⭐/✅/🟡) | Description |
|---|---|---|---|---|
| ✓ Ecosystem Health Check | 0.054s | ⭐ | ≤1s / ≤3s / ≤10s | Verifies all organ binaries are on PATH, executable, and return valid version st… |
| ✓ Version Report | 0.038s | ⭐ | ≤0.5s / ≤2s / ≤5s | Lists installed versions of all organ binaries on PATH.… |
| ✓ Supervisor Status | 0.007s | ⭐ | ≤0.5s / ≤2s / ≤5s | Shows workspace paths and daemon supervisor state table.… |
### ⭐ Ecosystem Health Check (`body.doctor`)
### ⭐ Version Report (`body.update`)
### ⭐ Supervisor Status (`body.status`)

---

## Model Enhancement Results

# Model Comparison: Qwen 2.5 Coder 1.5B vs 7B
## Summary
| Model | Baseline Keywords | Enhanced Keywords | Delta | Sandbox Pass |
|---|---|---|---|---|
| `qwen2.5-coder:1.5b` | 42.5% | 68.0% | +25.5% | 3/6 → 5/6 |
| `qwen2.5-coder:7b` | 65.0% | 85.5% | +20.5% | 5/6 → 6/6 |
## Reliability Scores (ARS)
| Model | Configuration | ARS Score | Grade |
|---|---|---|---|
| `qwen2.5-coder:1.5b` | Baseline | 45.2 | F |
| `qwen2.5-coder:1.5b` | Enhanced | **72.5** | **C** |
| `qwen2.5-coder:7b` | Baseline | 68.0 | D |
| `qwen2.5-coder:7b` | Enhanced | **88.5** | **B** |

