# tiered-test-pipeline

Summary: agent-benchmarks checks the whole Autonomic stack in tiers, from a CLI smoke test up to a graded release scorecard. It runs organ features in Docker, probes a full NATS and spine cluster, and writes JSON and Markdown reports.

## Sub-features

- `smoke-and-standalone`: Runs every organ's CLI and per-feature checks in isolated containers.
  - Intent: Catch CLI drift before it reaches a release.
  - Behaviour: `task test:smoke` and `task test:standalone` run the tests in `tests/standalone/` with `docker-compose.standalone.yml`.
  - Outcome: A pass or fail per organ feature. Not verified in this pass.
- `integration-cluster`: Brings up NATS, spine, and the daemons together and checks cross-organ paths.
  - Intent: Confirm the cluster works, not only each organ alone.
  - Behaviour: `task test:integration` uses `docker-compose.integration.yml` and `tests/integration/` with `tests/integration-config.toml`.
  - Outcome: Health and cross-organ results. Not verified in this pass.
- `benchmark-suites`: Stress, brain, accuracy, ecosystem, and architecture benchmarks.
  - Intent: Measure throughput, latency, recall, and fault isolation against thresholds.
  - Behaviour: The scripts in `benchmarks/` (`stress_test.py`, `brain_bench.py`, `accuracy_eval.py`, `ecosystem_bench.py`, `architecture_bench.py`) run through the `task benchmark:*` targets in `Taskfile.yml`.
  - Outcome: Results written to `benchmarks/`. Not verified in this pass.
- `release-scorecard`: Grades the feature set and writes the adoption report.
  - Intent: Give a release gate one artifact to read.
  - Behaviour: `benchmarks/scorecard.py` writes `benchmarks/scorecard.json` and `benchmarks/scorecard.md`.
  - Outcome: A graded report. The committed scorecard is a snapshot, not a live result.

## Code

- `benchmarks/`
- `tests/`
- `Taskfile.yml`
- `docker-compose.standalone.yml`
- `docker-compose.integration.yml`

## How to get to it (user POV)

- Install Docker and Task, then run `task build` and `task test:smoke`.
- Run `task all` for the full pipeline.

## Verification Suites (Targeted Test Commands)

- `task test:smoke`
- `task test:standalone`
- `task test:integration`

## Gotchas

- Organ binaries are pulled inside Docker through `agent-body/install-all-organs.sh`. A local Rust build is not needed, but a stale image can hide a regression.
- The committed `benchmarks/scorecard.*` files are snapshots. Regenerate them before a release gate reads them.
- `lora_adapters/` and the `error.log` and `output.log` files are local artifacts, not sources of truth.
