"""Runs the end-to-end flow (tests/e2e_flow.py) in its own process: it needs a fresh QGIS application."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.image_check import missing_qgis_outcome

ROOT = Path(__file__).resolve().parents[1]
try:
    import qgis.core  # noqa: F401
    QGIS_IMPORT_ERROR = None
except ImportError as error:
    QGIS_IMPORT_ERROR = error
    if missing_qgis_outcome(ROOT) == "skip":
        pytest.skip(f"PyQGIS is not importable on this host: {error}", allow_module_level=True)


def test_qgis_is_importable_in_the_test_images():
    """Reached without qgis.core only inside a test image, where skipping would hide a broken image."""
    assert QGIS_IMPORT_ERROR is None, f"qgis.core can't be imported inside the test image: {QGIS_IMPORT_ERROR}"


def test_end_to_end_flow():
    result = subprocess.run([sys.executable, "-m", "tests.e2e_flow"], cwd=ROOT, capture_output=True, text=True,
                            timeout=300, env=dict(os.environ, QT_QPA_PLATFORM="offscreen"))
    failures = [line for line in result.stdout.splitlines() if line.startswith("FAIL")]
    assert result.returncode == 0 and not failures, "\n".join(failures) or result.stdout[-2000:] + result.stderr[-2000:]
