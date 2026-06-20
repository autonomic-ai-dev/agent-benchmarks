"""Standalone feature tests for agent-mouth.

Validates status, command validation, and log summarization.
"""

import subprocess


def test_mouth_status():
    """agent-mouth status must exit cleanly."""
    result = subprocess.run(
        ["agent-mouth", "status"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"status failed: {result.stderr}"


def test_mouth_validate_safe_command():
    """agent-mouth validate must accept a safe bash command."""
    result = subprocess.run(
        ["agent-mouth", "validate", "--command", "echo hello"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"validate rejected safe command: {result.stderr}"


def test_mouth_validate_dangerous_command():
    """agent-mouth validate must reject a dangerous bash command."""
    result = subprocess.run(
        ["agent-mouth", "validate", "rm -rf /"],
        capture_output=True, text=True,
    )
    # Should either reject (exit != 0) or flag as dangerous
    assert result.returncode != 0 or "deny" in result.stdout.lower() or "reject" in result.stdout.lower(), (
        "validate should have flagged rm -rf /"
    )


def test_mouth_summarize():
    """agent-mouth summarize must process piped log input."""
    log_input = (
        "2026-06-20 INFO starting daemon\n"
        "2026-06-20 WARN disk usage high\n"
        "2026-06-20 ERROR connection refused\n"
        "2026-06-20 INFO retry succeeded\n"
    )
    result = subprocess.run(
        ["agent-mouth", "summarize"],
        input=log_input,
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"summarize failed: {result.stderr}"
    assert len(result.stdout.strip()) > 0
