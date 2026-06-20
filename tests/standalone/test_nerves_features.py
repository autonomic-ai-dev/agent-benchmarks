"""Standalone feature tests for agent-nerves.

Validates status reporting and NATS ping failure handling.
"""

import subprocess


def test_nerves_status():
    """agent-nerves status must exit cleanly."""
    result = subprocess.run(
        ["agent-nerves", "status"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"status failed: {result.stderr}"


def test_nerves_ping_without_nats():
    """agent-nerves ping must fail gracefully when NATS is not running."""
    result = subprocess.run(
        ["agent-nerves", "ping"],
        capture_output=True, text=True,
    )
    # Without NATS running, ping should exit non-zero but not crash
    assert result.returncode != 0, "ping should fail without NATS"
