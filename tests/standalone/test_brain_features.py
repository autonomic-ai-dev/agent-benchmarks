"""Standalone feature tests for agent-brain.

These tests exercise brain's core capabilities without requiring NATS or
the full cluster.  They call the CLI directly and assert on exit codes
and structured output.
"""

import json
import subprocess
import pytest


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------

def test_brain_index():
    """agent-brain index must complete without error."""
    result = subprocess.run(
        ["agent-brain", "index"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"index failed: {result.stderr}"


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def test_brain_stats_json():
    """agent-brain stats --json must return valid JSON with expected keys."""
    result = subprocess.run(
        ["agent-brain", "stats", "--json"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"stats failed: {result.stderr}"
    data = json.loads(result.stdout)
    assert "index" in data or "routing" in data or "value" in data, (
        f"unexpected stats shape: {list(data.keys())}"
    )


# ---------------------------------------------------------------------------
# Built-in benchmark gates (CI-safe, isolated fixtures)
# ---------------------------------------------------------------------------

def test_brain_bench_ci():
    """agent-brain bench --ci must pass its internal latency gate."""
    result = subprocess.run(
        ["agent-brain", "bench", "--ci"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"bench --ci failed: {result.stderr}"


def test_brain_bench_mcp():
    """agent-brain bench --mcp --assert must pass MCP tool latency bounds."""
    result = subprocess.run(
        ["agent-brain", "bench", "--mcp", "--assert"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"bench --mcp failed: {result.stderr}"


def test_brain_bench_scale():
    """agent-brain bench --scale --assert must pass ANN scale bench (p95 ≤ 50ms)."""
    result = subprocess.run(
        ["agent-brain", "bench", "--scale", "--assert"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"bench --scale failed: {result.stderr}"


def test_brain_bench_supervisor():
    """agent-brain bench --supervisor --assert must pass supervisor savings bench."""
    result = subprocess.run(
        ["agent-brain", "bench", "--supervisor", "--assert"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"bench --supervisor failed: {result.stderr}"


def test_brain_bench_graphify():
    """agent-brain bench --graphify --assert must pass graphify bench."""
    result = subprocess.run(
        ["agent-brain", "bench", "--graphify", "--assert"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"bench --graphify failed: {result.stderr}"


# ---------------------------------------------------------------------------
# Eval gates
# ---------------------------------------------------------------------------

def test_brain_eval_ci():
    """agent-brain eval --ci must pass Recall@3 gate (≥ 60%)."""
    result = subprocess.run(
        ["agent-brain", "eval", "--ci"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"eval --ci failed: {result.stderr}"


# ---------------------------------------------------------------------------
# GC
# ---------------------------------------------------------------------------

def test_brain_gc():
    """agent-brain gc must run without error."""
    result = subprocess.run(
        ["agent-brain", "gc"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"gc failed: {result.stderr}"
