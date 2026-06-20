"""Standalone feature tests for agent-eyes.

Validates status, DOM indexing, and structure description.
"""

import subprocess
import pytest


SAMPLE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head><title>Test Page</title></head>
<body>
  <h1>Hello World</h1>
  <p>This is a test paragraph.</p>
  <button id="submit">Submit</button>
  <input type="text" name="email" />
</body>
</html>
"""


def test_eyes_status():
    """agent-eyes status must exit cleanly."""
    result = subprocess.run(
        ["agent-eyes", "status"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"status failed: {result.stderr}"


def test_eyes_describe_file(tmp_path):
    """agent-eyes describe must extract structure from a local HTML file."""
    html = tmp_path / "page.html"
    html.write_text(SAMPLE_HTML)
    result = subprocess.run(
        ["agent-eyes", "describe", str(html)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"describe failed: {result.stderr}"
    # Should mention elements found
    assert len(result.stdout.strip()) > 0


import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

def test_eyes_dom_index_file(tmp_path):
    """agent-eyes dom index must index DOM elements from a local HTML file."""
    html = tmp_path / "index.html"
    html.write_text(SAMPLE_HTML)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(tmp_path), **kwargs)

    server = HTTPServer(('127.0.0.1', 0), Handler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    try:
        result = subprocess.run(
            ["agent-eyes", "dom", "index", f"http://127.0.0.1:{port}/index.html"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"dom index failed: {result.stderr}"
    finally:
        server.shutdown()
        server.server_close()
