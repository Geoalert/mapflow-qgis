"""Runs the end-to-end flow (tests/e2e_flow.py) in its own process: it needs a fresh QGIS application."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("qgis.core")


def test_end_to_end_flow():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, "-m", "tests.e2e_flow"], cwd=root, capture_output=True, text=True,
                            timeout=300, env=dict(os.environ, QT_QPA_PLATFORM="offscreen"))
    failures = [line for line in result.stdout.splitlines() if line.startswith("FAIL")]
    assert result.returncode == 0 and not failures, "\n".join(failures) or result.stdout[-2000:] + result.stderr[-2000:]
