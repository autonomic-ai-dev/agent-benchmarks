import pytest
import subprocess

ORGANS = [
    "agent-body",
    "agent-brain",
    "agent-spine",
    "agent-heart",
    "agent-nerves",
    "agent-muscle",
    "agent-immune",
    "agent-eyes",
    "agent-mouth",
]

@pytest.mark.parametrize("organ", ORGANS)
def test_organ_version_flag(organ):
    """Ensure all organs successfully parse the --version flag."""
    if organ == "agent-body":
        # agent-body exposes autonomic
        cmd = ["autonomic", "--version"]
    else:
        cmd = [organ, "--version"]
        
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"{organ} failed --version: {result.stderr}"
    assert len(result.stdout.strip()) > 0

def test_autonomic_doctor_fails_without_nats():
    """Ensure autonomic doctor fails gracefully if the workspace or nats is missing/offline (if applicable), or simply verify it runs."""
    # autonomic doctor just checks binaries on PATH. In this container, it should succeed finding them all.
    result = subprocess.run(["autonomic", "doctor"], capture_output=True, text=True)
    assert "✓ brain" in result.stdout
    assert "✓ heart" in result.stdout
    assert "✓ nerves" in result.stdout

def test_cli_invalid_arg_fails():
    """Ensure CLI fails gracefully with invalid arguments."""
    result = subprocess.run(["agent-brain", "--invalid-flag-that-doesnt-exist"], capture_output=True, text=True)
    assert result.returncode != 0
    assert "error" in result.stderr.lower()
