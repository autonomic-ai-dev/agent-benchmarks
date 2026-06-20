# Agent Benchmarks

This repository contains integration tests, benchmarking tools, and standalone tests for the [Autonomic AI](https://github.com/autonomic-ai-dev/agent-body) ecosystem.

It provides a unified way to spin up the entire cluster of daemons and execute rigorous performance metrics, API tests, and workflow validations.

## Architecture

* **docker-compose**: Spins up NATS, `agent-body`, `agent-brain`, and other organs via a generic Dockerfile capable of building any crate in the workspace.
* **Pytest Suite**: Evaluates the health and integrations between running containers over HTTP endpoints.
* **Benchmarks**: Load testing scripts (to be added) to capture response latency, throughput, and token budget estimations for cluster-wide behaviors.

## Quick Start

1. Install test dependencies:
   ```bash
   cd tests/
   pip install -r requirements.txt
   ```

2. Run the integration test suite:
   ```bash
   docker-compose -f docker-compose.integration.yml up --build --abort-on-container-exit
   ```

3. Run the standalone test suite:
   ```bash
   docker-compose -f docker-compose.standalone.yml up --build --abort-on-container-exit
   ```

## Creating new tests

Place integration tests in `tests/integration/` and standalone API/logic tests in `tests/standalone/`. Ensure the `docker_compose_up` fixture is used or adapted in your `conftest.py` as needed.
