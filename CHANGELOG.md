# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-06-20

### Added

- Docker-based 6-tier benchmark pipeline: smoke, standalone, integration, stress, accuracy, and scorecard
- `Dockerfile.test` and integration compose healthchecks for full organ cluster testing
- Comprehensive ecosystem feature benchmark (`ecosystem_bench.py`) covering all 43 organ features
- Architecture claims benchmark (fault isolation, deterministic execution, data sovereignty)
- Resource matrix benchmark with graded RAM/CPU profiles
- Integration config template (`tests/integration-config.toml`) for NATS/spine service discovery

### Changed

- Standalone tests updated for current organ CLI APIs (`--command`, `--data`, workflow `version` schema)
- Integration compose uses organ health endpoints and ordered startup dependencies
- `install-all-organs.sh`-based Docker images for release binary installs

### Fixed

- Ecosystem benchmark CLI invocations aligned with organ API changes (spine, muscle, mouth, eyes, immune)
- `brain.doctor` treats macOS codesign dev warnings as pass in local benchmark runs
- Edge-case and feature tests use correct JSONL `instruction`/`response` fields for agent-muscle
