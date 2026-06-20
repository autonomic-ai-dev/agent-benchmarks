"""Expanded integration tests for the full autonomic cluster.

Requires all daemons to be running via docker-compose.integration.yml.
Tests cross-organ communication over NATS and REST endpoints.
"""

import pytest
import requests
import subprocess
import time

# ---------------------------------------------------------------------------
# 2. Cross-organ communication
# ---------------------------------------------------------------------------

def test_nerves_ping_within_cluster():
    """agent-nerves ping must succeed when NATS is running inside the cluster."""
    result = subprocess.run(
        ["agent-nerves", "ping"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"nerves ping failed in cluster: {result.stderr}"


def test_autonomic_doctor_in_cluster():
    """autonomic doctor must report all organs healthy inside the cluster."""
    result = subprocess.run(
        ["autonomic", "doctor"],
        capture_output=True, text=True,
    )
    for organ in ["brain", "spine", "heart", "nerves"]:
        assert f"✓ {organ}" in result.stdout, (
            f"doctor did not find {organ}: {result.stdout}"
        )


# ---------------------------------------------------------------------------
# 4. Brain routing within cluster
# ---------------------------------------------------------------------------

def test_brain_stats_in_cluster():
    """agent-brain stats must return meaningful data inside the cluster."""
    result = subprocess.run(
        ["agent-brain", "stats", "--json"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"brain stats failed: {result.stderr}"


# ---------------------------------------------------------------------------
# 5. Immune scan → Mouth notification pipeline
# ---------------------------------------------------------------------------

def test_immune_scan_in_cluster(tmp_path):
    """agent-immune scan must process a manifest inside the cluster."""
    cargo = tmp_path / "Cargo.toml"
    cargo.write_text(
        '[package]\nname = "test"\nversion = "0.1.0"\n\n[dependencies]\nserde = "1.0"\n'
    )
    result = subprocess.run(
        ["agent-immune", "scan", str(cargo)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"immune scan failed in cluster: {result.stderr}"
