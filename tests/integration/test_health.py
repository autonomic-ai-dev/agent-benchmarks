import pytest
import requests
import time
import subprocess

# Pytest fixtures and helpers for testing the autonomic ecosystem

@pytest.fixture(scope="session", autouse=True)
def docker_compose_up():
    """Spin up the docker-compose cluster for the duration of the test session."""
    # We assume tests are run from the agent-benchmarks directory
    subprocess.run(["docker-compose", "up", "-d", "--build"], check=True)
    
    # Wait a bit for services to initialize and NATS to be ready
    time.sleep(10)
    
    yield
    
    # Teardown
    subprocess.run(["docker-compose", "down", "-v"], check=True)

def test_nats_health():
    """Verify NATS broker is up and running."""
    resp = requests.get("http://localhost:8222/healthz")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"

def test_agent_brain_health():
    """Verify agent-brain is up and responding to health checks."""
    # Retry a few times in case brain is still initializing
    for _ in range(5):
        try:
            resp = requests.get("http://localhost:3100/health")
            if resp.status_code == 200:
                assert resp.json().get("status") == "ok"
                return
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
        
    pytest.fail("agent-brain health check failed after retries")
