"""Standalone feature tests for agent-muscle.

Validates command execution, status, and dataset validation.
"""

import json
import subprocess
import pytest


def test_muscle_status():
    """agent-muscle status must exit cleanly."""
    result = subprocess.run(
        ["agent-muscle", "status"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"status failed: {result.stderr}"


def test_muscle_run_echo():
    """agent-muscle run must execute a simple command and capture output."""
    result = subprocess.run(
        ["agent-muscle", "run", "echo", "hello"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"run failed: {result.stderr}"
    assert "hello" in result.stdout


def test_muscle_validate_valid_dataset(tmp_path):
    """agent-muscle validate must accept well-formed JSONL training data."""
    dataset = tmp_path / "train.jsonl"
    entries = [
        {"prompt": "Fix the bug", "completion": "Done."},
        {"prompt": "Add logging", "completion": "Added."},
        {"prompt": "Refactor code", "completion": "Refactored."},
    ]
    dataset.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
    result = subprocess.run(
        ["agent-muscle", "validate", str(dataset)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"validate failed on valid data: {result.stderr}"


def test_muscle_validate_invalid_dataset(tmp_path):
    """agent-muscle validate must reject malformed JSONL."""
    dataset = tmp_path / "bad.jsonl"
    dataset.write_text("this is not json\n{broken\n")
    result = subprocess.run(
        ["agent-muscle", "validate", str(dataset)],
        capture_output=True, text=True,
    )
    assert result.returncode != 0, "validate should have rejected bad JSONL"
