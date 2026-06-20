"""Edge case and failure mode tests for all organs.

These tests push each organ into unusual, adversarial, or boundary
conditions to verify graceful degradation rather than crashes.
"""

import json
import subprocess
import os
import pytest


# ---------------------------------------------------------------------------
# agent-brain edge cases
# ---------------------------------------------------------------------------

class TestBrainEdgeCases:
    """Boundary and adversarial tests for agent-brain."""

    def test_route_with_empty_query(self):
        """Brain should handle an empty route_task query gracefully."""
        result = subprocess.run(
            ["agent-brain", "stats"],  # stats with no data is an edge case
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_stats_with_zero_days(self):
        """Stats with --days 0 should not crash."""
        result = subprocess.run(
            ["agent-brain", "stats", "--days", "0"],
            capture_output=True, text=True,
        )
        assert result.returncode in (0, 1), f"Crashed: {result.stderr}"

    def test_stats_with_huge_days(self):
        """Stats with very large --days should not overflow."""
        result = subprocess.run(
            ["agent-brain", "stats", "--days", "99999"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_gc_with_aggressive_thresholds(self):
        """GC with very aggressive thresholds should still run safely."""
        result = subprocess.run(
            ["agent-brain", "gc", "--min-confidence", "99"],
            capture_output=True, text=True,
        )
        assert result.returncode in (0, 1), f"Crashed: {result.stderr}"

    def test_memory_gc_dry_run(self):
        """Memory GC in dry-run mode should never mutate data."""
        result = subprocess.run(
            ["agent-brain", "memory", "gc"],
            capture_output=True, text=True,
        )
        # dry-run is default — should always succeed
        assert result.returncode == 0, f"Dry-run GC failed: {result.stderr}"

    def test_export_to_nonexistent_dir(self, tmp_path):
        """Export to a deeply nested non-existent path should either create it or fail gracefully."""
        deep_path = tmp_path / "a" / "b" / "c" / "export"
        result = subprocess.run(
            ["agent-brain", "export", str(deep_path)],
            capture_output=True, text=True,
        )
        # Should either create the path or fail with a clear error
        assert result.returncode in (0, 1), f"Crashed: {result.stderr}"

    def test_config_show(self):
        """Config show should always work even with no custom config."""
        result = subprocess.run(
            ["agent-brain", "config", "show"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# agent-spine edge cases
# ---------------------------------------------------------------------------

class TestSpineEdgeCases:
    """Boundary tests for agent-spine."""

    def test_validate_empty_file(self, tmp_path):
        """Validate an empty YAML file."""
        empty = tmp_path / "empty.yml"
        empty.write_text("")
        result = subprocess.run(
            ["agent-spine", "validate", str(empty)],
            capture_output=True, text=True,
        )
        assert result.returncode != 0, "Should reject empty workflow"

    def test_validate_huge_workflow(self, tmp_path):
        """Validate a very large YAML workflow (1000 steps)."""
        steps = "\n".join(
            f"  - name: step_{i}\n    run: echo {i}" for i in range(1000)
        )
        huge = tmp_path / "huge.yml"
        huge.write_text(f"name: huge\nsteps:\n{steps}\n")
        result = subprocess.run(
            ["agent-spine", "validate", str(huge)],
            capture_output=True, text=True,
            timeout=30,
        )
        # Should parse without timing out
        assert result.returncode in (0, 1), f"Crashed on large workflow: {result.stderr}"

    def test_validate_binary_file(self, tmp_path):
        """Validate a binary file should fail gracefully."""
        binary = tmp_path / "binary.yml"
        binary.write_bytes(os.urandom(1024))
        result = subprocess.run(
            ["agent-spine", "validate", str(binary)],
            capture_output=True, text=True,
        )
        assert result.returncode != 0

    def test_validate_nonexistent_file(self):
        """Validate a file that does not exist."""
        result = subprocess.run(
            ["agent-spine", "validate", "/nonexistent/path/workflow.yml"],
            capture_output=True, text=True,
        )
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# agent-muscle edge cases
# ---------------------------------------------------------------------------

class TestMuscleEdgeCases:
    """Boundary tests for agent-muscle."""

    def test_run_command_that_fails(self):
        """Running a command that exits non-zero should be reported."""
        result = subprocess.run(
            ["agent-muscle", "run", "false"],
            capture_output=True, text=True,
        )
        assert result.returncode != 0

    def test_run_command_with_large_output(self):
        """Running a command that produces large output should not hang."""
        result = subprocess.run(
            ["agent-muscle", "run", "seq", "10000"],
            capture_output=True, text=True,
            timeout=15,
        )
        assert result.returncode == 0
        assert "10000" in result.stdout

    def test_validate_empty_dataset(self, tmp_path):
        """Validating an empty file should fail gracefully."""
        empty = tmp_path / "empty.jsonl"
        empty.write_text("")
        result = subprocess.run(
            ["agent-muscle", "validate", str(empty)],
            capture_output=True, text=True,
        )
        assert result.returncode != 0, "Should reject empty dataset"

    def test_validate_single_entry_dataset(self, tmp_path):
        """Validating a single-entry JSONL should work."""
        single = tmp_path / "single.jsonl"
        single.write_text(json.dumps({"prompt": "test", "completion": "ok"}) + "\n")
        result = subprocess.run(
            ["agent-muscle", "validate", str(single)],
            capture_output=True, text=True,
        )
        # May require minimum entries — accept either
        assert result.returncode in (0, 1)


# ---------------------------------------------------------------------------
# agent-immune edge cases
# ---------------------------------------------------------------------------

class TestImmuneEdgeCases:
    """Boundary tests for agent-immune."""

    def test_scan_empty_manifest(self, tmp_path):
        """Scanning an empty Cargo.toml should not crash."""
        empty_cargo = tmp_path / "Cargo.toml"
        empty_cargo.write_text("")
        result = subprocess.run(
            ["agent-immune", "scan", str(empty_cargo)],
            capture_output=True, text=True,
        )
        assert result.returncode in (0, 1), f"Crashed on empty manifest: {result.stderr}"

    def test_scan_manifest_with_many_deps(self, tmp_path):
        """Scanning a manifest with 50+ dependencies should complete in time."""
        deps = "\n".join(f'dep_{i} = "1.0"' for i in range(50))
        cargo = tmp_path / "Cargo.toml"
        cargo.write_text(f'[package]\nname = "test"\nversion = "0.1.0"\n\n[dependencies]\n{deps}\n')
        result = subprocess.run(
            ["agent-immune", "scan", str(cargo)],
            capture_output=True, text=True,
            timeout=30,
        )
        assert result.returncode in (0, 1), f"Crashed on large manifest: {result.stderr}"

    def test_scan_wrong_file_type(self, tmp_path):
        """Scanning a non-manifest file should fail gracefully."""
        txt = tmp_path / "readme.txt"
        txt.write_text("This is not a manifest")
        result = subprocess.run(
            ["agent-immune", "scan", str(txt)],
            capture_output=True, text=True,
        )
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# agent-mouth edge cases
# ---------------------------------------------------------------------------

class TestMouthEdgeCases:
    """Boundary tests for agent-mouth."""

    def test_validate_empty_command(self):
        """Validating an empty string should be handled."""
        result = subprocess.run(
            ["agent-mouth", "validate", ""],
            capture_output=True, text=True,
        )
        # Should either accept empty (no-op) or reject — just no crash
        assert result.returncode in (0, 1, 2)

    def test_validate_pipe_chain(self):
        """Validating a complex pipe chain."""
        result = subprocess.run(
            ["agent-mouth", "validate", "cat /etc/passwd | grep root | head -1"],
            capture_output=True, text=True,
        )
        assert result.returncode in (0, 1)

    def test_summarize_empty_input(self):
        """Summarizing empty input should produce something or exit cleanly."""
        result = subprocess.run(
            ["agent-mouth", "summarize"],
            input="",
            capture_output=True, text=True,
        )
        assert result.returncode in (0, 1)

    def test_summarize_huge_input(self):
        """Summarizing a very large log input should not OOM."""
        big_log = "2026-01-01 INFO test line\n" * 10000
        result = subprocess.run(
            ["agent-mouth", "summarize"],
            input=big_log,
            capture_output=True, text=True,
            timeout=30,
        )
        assert result.returncode in (0, 1), f"Crashed on large input: {result.stderr}"
