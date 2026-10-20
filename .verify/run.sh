#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$DIR/.." && pwd)"

echo "==> [agent-benchmarks] Starting verification suite..."
cd "$REPO_ROOT/tests"

echo "==> Running standalone smoke tests (pytest)..."
"${BENCH_PYTHON:-python3}" -m pytest standalone/test_smoke.py -v

echo "==> [agent-benchmarks] Verification passed cleanly (exit 0)."
