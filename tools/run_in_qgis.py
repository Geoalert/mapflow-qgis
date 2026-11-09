"""Run the end-to-end tests with the QGIS you have open (QGIS 3 or QGIS 4). In its Python console:

    import runpy; runpy.run_path("/path/to/mapflow-next/tools/run_in_qgis.py")

The tests run in a separate process, with their own settings and authentication database in a temporary
folder, so this QGIS session and your profile are not touched. The output and the screenshots go to
test-results/qgis-<version>/ in the repository folder; the console says when the run has finished.
"""
import os
import subprocess
import sys
from pathlib import Path

from qgis.core import Qgis, QgsApplication
from qgis.PyQt.QtCore import PYQT_VERSION_STR, QT_VERSION_STR, QCoreApplication, QTimer

REPO = Path(__file__).resolve().parent.parent


def qgis_python():
    """The Python executable that QGIS embeds (on macOS it sits inside the app bundle)."""
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    places = [Path(sys.prefix) / "bin", Path(sys.exec_prefix) / "bin", Path(sys.executable).parent,
              Path(QgsApplication.prefixPath()) / "bin", Path(QgsApplication.prefixPath()).parent / "bin",
              Path(QgsApplication.prefixPath()).parent / "MacOS" / "bin"]
    for place in places:
        for name in (version, "python3", "python"):
            candidate = place / name
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
    return ""


def main():
    out = REPO / "test-results" / f"qgis-{Qgis.QGIS_VERSION.split('-')[0]}"
    out.mkdir(parents=True, exist_ok=True)
    python = qgis_python()
    info = (f"QGIS {Qgis.QGIS_VERSION}, Qt {QT_VERSION_STR}, PyQt {PYQT_VERSION_STR}, Python {sys.version.split()[0]}\n"
            f"python: {python or 'not found'}\nprefix: {QgsApplication.prefixPath()}\n")
    print(info)
    (out / "environment.txt").write_text(info)
    if not python:
        print("Couldn't find the Python inside QGIS: the tests didn't run.")
        return
    env = dict(os.environ)
    env.update({
        "PYTHONPATH": os.pathsep.join([str(REPO)] + [p for p in sys.path if p]),
        "QGIS_PREFIX_PATH": QgsApplication.prefixPath(),
        "QT_PLUGIN_PATH": os.pathsep.join(QCoreApplication.libraryPaths()),
        "QT_QPA_PLATFORM": "offscreen",
        "PYTHONNOUSERSITE": "1",
    })
    log = open(out / "e2e.log", "w")
    process = subprocess.Popen([python, "-m", "tests.e2e_flow", str(out / "screens")], cwd=str(REPO), env=env,
                               stdout=log, stderr=subprocess.STDOUT)
    print(f"End-to-end tests started (pid {process.pid}); output: {out / 'e2e.log'}")

    def finished():
        if process.poll() is None:
            QTimer.singleShot(2000, finished)
            return
        log.close()
        lines = (out / "e2e.log").read_text(errors="replace").splitlines()
        summary = next((line for line in reversed(lines) if "checks passed" in line), "no summary: see the log")
        print(f"End-to-end tests finished (exit {process.returncode}): {summary}")
    QTimer.singleShot(2000, finished)


main()
