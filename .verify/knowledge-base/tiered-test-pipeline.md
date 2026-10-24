# Tiered test pipeline

## What it does

agent-benchmarks is the conformance layer for the Autonomic platform. It runs six tiers, from a CLI smoke check through a graded release scorecard, and writes the results as JSON and Markdown.

## How it works

1. **Smoke.** `task test:smoke` checks each organ's `--version` and basic CLI behaviour.
2. **Standalone.** `task test:standalone` runs per-organ feature tests in Docker, using `docker-compose.standalone.yml`.
3. **Integration.** `task test:integration` starts NATS, spine, and the daemons together, using `docker-compose.integration.yml`, and checks cross-organ paths.
4. **Stress and brain.** `task benchmark:stress` and `task benchmark:brain` measure HTTP throughput and brain latency.
5. **Accuracy.** `task benchmark:accuracy` measures Recall@3 and token savings.
6. **Scorecard.** `benchmarks/scorecard.py` grades the features and writes `scorecard.json` and `scorecard.md`.

## Where the code is

- `benchmarks/` holds the benchmark scripts and the committed scorecard snapshot.
- `tests/standalone/` and `tests/integration/` hold the test suites. `tests/integration-config.toml` sets the cluster layout.
- `Taskfile.yml` maps each tier to a `task` target.

## How to use it

- Install Docker and [Task](https://taskfile.dev/), then run `task build` and `task test:smoke`.
- Run `task all` to run every tier.

## How it is verified

- This pass did not run any tier. The verification command for each tier is listed in the feature map.

## Known limits

- The committed scorecard is a snapshot. A release gate that reads it without regenerating it sees old results.
- Organ binaries come from `agent-body/install-all-organs.sh` inside Docker. A stale image can hide a regression.

## Related

- Feature map: `.verify/features/tiered-test-pipeline.md`
- Organ stack: agent-body `supervisor-and-gateway` feature map
