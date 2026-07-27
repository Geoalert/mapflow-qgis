"""QGIS-tier tests for Mapflow.setup_tempdir startup resilience.

A working directory on an unmounted external drive leaves a root-owned, unwritable stub at
``/Volumes/<name>``; ``mkdir(parents=True)`` then raises ``PermissionError`` partway up. Before
the fix this propagated out of ``classFactory`` and the plugin could not start at all (and
reinstalling did not help, because ``outputDir`` lives in QgsSettings). ``setup_tempdir`` must
now survive it and fall back to "no working directory".
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.mapflow import Mapflow


def _plugin(output_dir, temp_dir_sentinel="sentinel"):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.plugin_name = "Mapflow"
    plugin.app_context = SimpleNamespace(
        settings=SimpleNamespace(value=lambda key: output_dir if key == 'outputDir' else None),
        temp_dir=temp_dir_sentinel,
    )
    return plugin


def test_creates_temp_dir_under_configured_output(tmp_path):
    plugin = _plugin(str(tmp_path / "work"))

    # No error string -> success.
    assert plugin.setup_tempdir() is None
    assert plugin.app_context.temp_dir == tmp_path / "work" / "Temp"
    assert (tmp_path / "work" / "Temp").exists()


def test_survives_permission_error_and_returns_reason(tmp_path, monkeypatch):
    plugin = _plugin(str(tmp_path / "Volumes" / "Seagate Exp" / "mapflow"))

    # Simulate the unmounted-drive stub: mkdir refused with Errno 13 on the root-owned parent.
    def deny(self, *args, **kwargs):
        raise PermissionError(13, "Permission denied")
    monkeypatch.setattr(Path, "mkdir", deny)

    error = plugin.setup_tempdir()  # must not raise (this is what previously killed classFactory)
    assert error and "Permission denied" in error  # reason is surfaced to the caller
    assert plugin.app_context.temp_dir is None


def test_survives_other_exceptions(tmp_path, monkeypatch):
    # An unmounted volume can also fail differently (e.g. FileNotFoundError) — handle any failure.
    plugin = _plugin(str(tmp_path / "gone"))

    def boom(self, *args, **kwargs):
        raise FileNotFoundError(2, "No such file or directory")
    monkeypatch.setattr(Path, "mkdir", boom)

    error = plugin.setup_tempdir()
    assert error and "No such file" in error
    assert plugin.app_context.temp_dir is None


def test_no_output_dir_is_a_noop():
    plugin = _plugin(output_dir=None, temp_dir_sentinel="unchanged")

    # Nothing configured: early return, temp_dir left untouched, no failure signal.
    assert plugin.setup_tempdir() is None
    assert plugin.app_context.temp_dir == "unchanged"


# ---------------- ensure_output_directory: prompt only when needed ----------------

def test_ensure_output_directory_skips_prompt_when_usable(tmp_path):
    existing = tmp_path / "Temp"
    existing.mkdir()
    plugin = Mapflow.__new__(Mapflow)
    plugin.app_context = SimpleNamespace(temp_dir=existing)
    plugin.prompt_output_directory = MagicMock()

    assert plugin.ensure_output_directory("need it") is True
    plugin.prompt_output_directory.assert_not_called()


def test_ensure_output_directory_prompts_when_not_set():
    plugin = Mapflow.__new__(Mapflow)
    plugin.app_context = SimpleNamespace(temp_dir=None)
    plugin.prompt_output_directory = MagicMock(return_value=True)

    assert plugin.ensure_output_directory("need a dir") is True
    plugin.prompt_output_directory.assert_called_once_with("need a dir")


def test_ensure_output_directory_prompts_when_dir_deleted(tmp_path):
    gone = tmp_path / "gone" / "Temp"  # a stale path that no longer exists
    plugin = Mapflow.__new__(Mapflow)
    plugin.app_context = SimpleNamespace(temp_dir=gone)
    plugin.prompt_output_directory = MagicMock(return_value=False)

    # Postponed by the user -> caller must cancel.
    assert plugin.ensure_output_directory("need it") is False
    plugin.prompt_output_directory.assert_called_once()


# ------------- prompt_output_directory: 'Later' cancels, 'Select' picks -------------

class _FakeMessageBox:
    """Stand-in for QMessageBox that records buttons and reports a preset click."""
    Warning = 2
    AcceptRole = 0
    RejectRole = 1
    click = "select"  # or "later"

    def __init__(self, *args, **kwargs):
        self._buttons = []

    def setTextFormat(self, *args):
        pass

    def addButton(self, text, role):
        button = object()
        self._buttons.append(button)
        return button

    def exec(self):
        pass

    def clickedButton(self):
        # buttons added in order: [Select directory…, Later]
        return self._buttons[0] if _FakeMessageBox.click == "select" else self._buttons[1]


def _prompt_plugin(monkeypatch, click):
    monkeypatch.setattr("mapflow.mapflow.QMessageBox", _FakeMessageBox)
    _FakeMessageBox.click = click
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.plugin_name = "Mapflow"
    plugin.main_window = None
    plugin.app_context = SimpleNamespace(temp_dir=None)
    plugin.select_output_directory = MagicMock()
    return plugin


def test_prompt_later_cancels_without_opening_file_dialog(monkeypatch):
    plugin = _prompt_plugin(monkeypatch, click="later")

    assert plugin.prompt_output_directory("why") is False
    plugin.select_output_directory.assert_not_called()


def test_prompt_select_opens_dialog_and_reports_success(monkeypatch):
    plugin = _prompt_plugin(monkeypatch, click="select")
    # Simulate the file dialog setting a usable directory.
    plugin.select_output_directory.side_effect = lambda: setattr(
        plugin.app_context, "temp_dir", "/some/Temp")

    assert plugin.prompt_output_directory("why") is True
    plugin.select_output_directory.assert_called_once()


def test_prompt_select_reports_failure_when_dir_still_unset(monkeypatch):
    plugin = _prompt_plugin(monkeypatch, click="select")
    # User picked an unusable dir: select_output_directory alerted and left temp_dir None.
    assert plugin.prompt_output_directory("why") is False
    plugin.select_output_directory.assert_called_once()
