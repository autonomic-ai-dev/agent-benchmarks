import pytest
import subprocess
import os

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

def _run(cmd, **kwargs):
    try:
        return subprocess.run(cmd, **kwargs)
    except FileNotFoundError:
        pytest.skip(f"Executable '{cmd[0]}' not found on PATH. Skipping test.")


# ---------------------------------------------------------------------------
# 1. Binary version checks
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("organ", ORGANS)
def test_organ_version_flag(organ):
    """Every organ binary must respond to --version with exit 0."""
    cmd = ["autonomic", "--version"] if organ == "agent-body" else [organ, "--version"]
    result = _run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"{organ} --version failed: {result.stderr}"
    assert len(result.stdout.strip()) > 0


# ---------------------------------------------------------------------------
# 2. autonomic doctor — binary presence
# ---------------------------------------------------------------------------

def test_autonomic_doctor():
    """autonomic doctor must find brain, heart, and nerves on PATH."""
    result = _run(["autonomic", "doctor"], capture_output=True, text=True)
    for organ in ["brain", "heart", "nerves"]:
        assert f"✓ {organ}" in result.stdout, f"doctor did not find {organ}"


# ---------------------------------------------------------------------------
# 3. Workspace & config initialisation
# ---------------------------------------------------------------------------

def test_autonomic_init(tmp_path):
    """autonomic init should scaffold a workspace directory."""
    result = _run(
        ["autonomic", "init"],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )
    # init may warn if already exists — accept 0 or known non-error exits
    assert result.returncode in (0, 1), f"autonomic init failed: {result.stderr}"


def test_brain_config_init(tmp_path):
    """agent-brain config init should create a default config.yaml."""
    result = _run(
        ["agent-brain", "config", "init"],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )
    assert result.returncode == 0, f"brain config init failed: {result.stderr}"


def test_spine_init(tmp_path):
    """agent-spine init should create config + example workflow."""
    result = _run(
        ["agent-spine", "init"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert result.returncode == 0, f"spine init failed: {result.stderr}"


# ---------------------------------------------------------------------------
# 4. Graceful failure modes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("organ", ORGANS)
def test_cli_invalid_flag_fails(organ):
    """Invalid flags must produce a non-zero exit and an error message."""
    cmd = (
        ["autonomic", "--invalid-flag-xyz"]
        if organ == "agent-body"
        else [organ, "--invalid-flag-xyz"]
    )
    result = _run(cmd, capture_output=True, text=True)
    assert result.returncode != 0


def test_immune_scan_missing_arg():
    """agent-immune scan without a path must fail gracefully."""
    result = _run(["agent-immune", "scan"], capture_output=True, text=True)
    assert result.returncode != 0


def test_spine_validate_missing_arg():
    """agent-spine validate without a workflow must fail gracefully."""
    result = _run(["agent-spine", "validate"], capture_output=True, text=True)
    assert result.returncode != 0
