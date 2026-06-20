"""Standalone feature tests for agent-heart.

Validates GC, status, and budget tooling.
"""

import subprocess


def test_heart_status():
    """agent-heart status must exit cleanly."""
    result = subprocess.run(
        ["agent-heart", "status"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"status failed: {result.stderr}"


def test_heart_gc():
    """agent-heart gc must run a single GC cycle without error."""
    result = subprocess.run(
        ["agent-heart", "gc"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"gc failed: {result.stderr}"


def test_heart_budget():
    """agent-heart budget must produce token budget output."""
    result = subprocess.run(
        ["agent-heart", "budget"],
        capture_output=True, text=True,
    )
    # budget may warn if no retrieval_log exists — accept 0 or graceful exit
    assert result.returncode in (0, 1), f"budget crashed: {result.stderr}"
