import pytest
import requests
import time

def test_nats_health():
    """Verify NATS broker is up and running."""
    resp = requests.get("http://nats:8222/healthz")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"

# Define the expected ports for the ecosystem daemons
DAEMONS = {
    "agent-brain": 3100,
    "agent-heart": 3101,
    "agent-nerves": 3102,
    "agent-muscle": 3103,
    "agent-mouth": 3104,
    "agent-eyes": 3105,
    "agent-immune": 3106,
    "agent-spine": 3000, # Note: spine defaults to 3000 usually
}

@pytest.mark.parametrize("daemon,port", DAEMONS.items())
def test_daemon_health(daemon, port):
    """Verify each specific daemon is up and responding to health checks on its default port."""
    url = f"http://{daemon}:{port}/health"
    
    # Retry a few times in case the daemon is still initializing or reconnecting to NATS
    for _ in range(10):
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                assert resp.json().get("status") == "ok"
                return
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            pass
        time.sleep(2)
        
    pytest.fail(f"{daemon} health check failed after retries on {url}")
