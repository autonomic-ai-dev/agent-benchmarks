"""Expanded integration tests for the full autonomic cluster.

Requires all daemons to be running via docker-compose.integration.yml.
Tests cross-organ communication over NATS and REST endpoints.
"""

import pytest
import requests
import subprocess
import time

# ---------------------------------------------------------------------------
# Daemon health matrix
# ---------------------------------------------------------------------------

DAEMONS = {
    "agent-brain": 3100,
    "agent-heart": 3101,
    "agent-nerves": 3102,
    "agent-muscle": 3103,
    "agent-mouth": 3104,
    "agent-eyes": 3105,
    "agent-immune": 3106,
    "agent-spine": 3000,
}


def _retry_get(url, retries=10, delay=2):
    """Retry a GET request with backoff."""
    for _ in range(retries):
        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                return resp
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass
        time.sleep(delay)
    return None


# ---------------------------------------------------------------------------
# 1. NATS broker
# ---------------------------------------------------------------------------

def test_nats_health():
    """NATS JetStream broker must be healthy."""
    resp = _retry_get("http://nats:8222/healthz")
    assert resp is not None, "NATS health check failed after retries"
    assert resp.json().get("status") == "ok"


def test_nats_jetstream_enabled():
    """NATS must report JetStream as enabled."""
    resp = _retry_get("http://nats:8222/jsz")
    assert resp is not None, "JetStream info endpoint unreachable"
    data = resp.json()
    assert "streams" in data or "config" in data, f"Unexpected jsz response: {data}"


# ---------------------------------------------------------------------------
# 2. All daemon health endpoints
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("daemon,port", DAEMONS.items())
def test_daemon_health(daemon, port):
    """Every daemon must respond to /health with 200 OK."""
    url = f"http://{daemon}:{port}/health"
    resp = _retry_get(url)
    assert resp is not None, f"{daemon} health check failed on {url}"


# ---------------------------------------------------------------------------
# 3. Cross-organ communication
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
