# agent-benchmarks

`agent-benchmarks` tests the Autonomic stack in tiers, from a CLI smoke check up to a graded scorecard. Each tier runs in Docker and writes its report to `benchmarks/`.

## Quick start

```bash
brew install go-task
task build
task test:smoke
```

## Tiers

| Task | What it checks |
|------|----------------|
| `task test:smoke` | Each organ's `--version` and basic CLI |
| `task test:standalone` | Per-organ feature tests |
| `task test:integration` | Full cluster: NATS, spine, and the daemons together |
| `task benchmark:stress` | HTTP throughput against the health endpoints |
| `task benchmark:brain` | agent-brain latency, MCP, and scale |
| `task benchmark:accuracy` | Recall@3 and token savings |
| `task benchmark:ecosystem` | The feature set, with graded thresholds |
| `task benchmark:architecture` | Fault isolation and determinism claims |
| `task benchmark:matrix:quick` | RAM and CPU profile per organ |
| `task scorecard` | Writes `benchmarks/scorecard.md` |
| `task all` | Every tier |

`task test:integration` needs a running Docker daemon.

## Model comparison

```bash
task benchmark:model MODEL=codellama:7b
HUGGINGFACE_TOKEN=hf_xxx task benchmark:model MODEL=bigcode/starcoder2-7b PROVIDER=huggingface
```

Generated code runs in a Docker sandbox with networking disabled and a memory limit.

## Layout

```
Taskfile.yml                     task targets
docker-compose.*.yml             standalone and integration stacks
tests/standalone/                per-organ pytest
tests/integration/               cluster pytest
benchmarks/                      stress, brain, accuracy, ecosystem, scorecard
```

Reports are written to `benchmarks/` (`results_*.md`, `results_*.json`, `scorecard.md`). Generated artifacts are gitignored.

## Develop

```bash
task --list
task test:edge-cases
```

Feature map and knowledge base: `.verify/features/` and `.verify/knowledge-base/`.
