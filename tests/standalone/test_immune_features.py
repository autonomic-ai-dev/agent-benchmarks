"""Standalone feature tests for agent-immune.

Validates dependency scanning, status, and memory verification.
"""

import subprocess
import pytest


def test_immune_status():
    """agent-immune status must exit cleanly."""
    result = subprocess.run(
        ["agent-immune", "status"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"status failed: {result.stderr}"


def test_immune_scan_cargo_toml(tmp_path):
    """agent-immune scan must process a Cargo.toml manifest."""
    cargo = tmp_path / "Cargo.toml"
    cargo.write_text(
        '[package]\nname = "test"\nversion = "0.1.0"\n\n[dependencies]\nserde = "1.0"\n'
    )
    result = subprocess.run(
        ["agent-immune", "scan", str(cargo)],
        capture_output=True, text=True,
    )
    # scan may find 0 vulns (exit 0) or report some (still exit 0 with warnings)
    assert result.returncode == 0, f"scan crashed: {result.stderr}"


def test_immune_scan_package_json(tmp_path):
    """agent-immune scan must process a package.json manifest."""
    pkg = tmp_path / "package.json"
    pkg.write_text('{"name":"test","version":"1.0.0","dependencies":{"express":"4.18.0"}}')
    result = subprocess.run(
        ["agent-immune", "scan", str(pkg)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"scan crashed: {result.stderr}"


def test_immune_verify_memory():
    """agent-immune verify-memory must check for runaway memory growth."""
    result = subprocess.run(
        ["agent-immune", "verify-memory", "test_script.py"],
        capture_output=True, text=True,
    )
    # May succeed or fail depending on dataset — just must not crash
    assert result.returncode in (0, 1), f"verify-memory crashed: {result.stderr}"
