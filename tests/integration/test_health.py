import pytest
import requests
import time

def test_nats_health():
    """Verify NATS broker is up and running."""
    resp = requests.get("http://nats:8222/healthz")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"

def test_agent_brain_health():
    """Verify agent-brain is up and responding to health checks."""
    # Retry a few times in case brain is still initializing
    for _ in range(5):
        try:
            resp = requests.get("http://agent-brain:3100/health")
            if resp.status_code == 200:
                assert resp.json().get("status") == "ok"
                return
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
        
    pytest.fail("agent-brain health check failed after retries")
