"""Standalone feature tests for agent-spine.

Validates workflow parsing, initialisation, and status reporting.
"""

import subprocess
import os
import pytest


VALID_WORKFLOW = """\
version: 1
name: hello
start_node: greet
nodes:
  - name: greet
    kind: agent
"""

INVALID_WORKFLOW = """\
this is not valid yaml: [[[
steps:
  - totally broken
"""


def test_spine_status():
    """agent-spine status must exit cleanly."""
    result = subprocess.run(
        ["agent-spine", "status"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"status failed: {result.stderr}"


def test_spine_validate_valid(tmp_path):
    """agent-spine validate must accept a well-formed workflow YAML."""
    wf = tmp_path / "hello.yml"
    wf.write_text(VALID_WORKFLOW)
    result = subprocess.run(
        ["agent-spine", "validate", str(wf)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"validate failed on valid workflow: {result.stderr}"


def test_spine_validate_invalid(tmp_path):
    """agent-spine validate must reject a malformed workflow YAML."""
    wf = tmp_path / "bad.yml"
    wf.write_text(INVALID_WORKFLOW)
    result = subprocess.run(
        ["agent-spine", "validate", str(wf)],
        capture_output=True, text=True,
    )
    assert result.returncode != 0, "validate should have rejected malformed YAML"
