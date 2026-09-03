"""QGIS-tier tests for the working directory: startup resilience, and the prompt before writing.

A working directory on an unmounted external drive leaves a root-owned, unwritable stub at
``/Volumes/<name>``; ``mkdir(parents=True)`` then raises ``PermissionError`` partway up. Before
the fix this propagated out of ``classFactory`` and the plugin could not start at all (and
reinstalling did not help, because ``outputDir`` lives in QgsSettings). ``setup_tempdir`` must
survive it and fall back to "no working directory".

The filesystem half is `WorkdirService`; the two dialogs are `WorkdirView`; `mapflow.py` keeps the
coordination, because two controllers need "is there a directory, ask if not" and neither may call
the other.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.service.workdir_service import WorkdirService
from mapflow.mapflow import Mapflow


def _service(output_dir, temp_dir_sentinel="sentinel"):
    return WorkdirService(app_context=SimpleNamespace(
        settings=SimpleNamespace(value=lambda key: output_dir if key == 'outputDir' else None),
        temp_dir=temp_dir_sentinel,
    ))


def test_creates_temp_dir_under_configured_output(tmp_path):
    service = _service(str(tmp_path / "work"))

    # No error string -> success.
    assert service.setup_tempdir() is None
    assert service.app_context.temp_dir == tmp_path / "work" / "Temp"
    assert (tmp_path / "work" / "Temp").exists()


def test_survives_permission_error_and_returns_reason(tmp_path, monkeypatch):
    service = _service(str(tmp_path / "Volumes" / "Seagate Exp" / "mapflow"))

    # Simulate the unmounted-drive stub: mkdir refused with Errno 13 on the root-owned parent.
    def deny(self, *args, **kwargs):
        raise PermissionError(13, "Permission denied")
    monkeypatch.setattr(Path, "mkdir", deny)

    error = service.setup_tempdir()  # must not raise (this previously killed classFactory)
    assert error and "Permission denied" in error  # reason is surfaced to the caller
    assert service.app_context.temp_dir is None


def test_survives_other_exceptions(tmp_path, monkeypatch):
    # An unmounted volume can also fail differently (e.g. FileNotFoundError) — handle any failure.
    service = _service(str(tmp_path / "gone"))

    def boom(self, *args, **kwargs):
        raise FileNotFoundError(2, "No such file or directory")
    monkeypatch.setattr(Path, "mkdir", boom)

    error = service.setup_tempdir()
    assert error and "No such file" in error
    assert service.app_context.temp_dir is None


def test_no_output_dir_is_a_noop():
    service = _service(output_dir=None, temp_dir_sentinel="unchanged")

    # Nothing configured: early return, temp_dir left untouched, no failure signal.
    assert service.setup_tempdir() is None
    assert service.app_context.temp_dir == "unchanged"


def test_usable_only_when_the_directory_still_exists(tmp_path):
    """The setting survives across sessions, so an existing path is not enough — the directory
    itself can have been deleted or unmounted since."""
    service = _service(str(tmp_path))
    service.app_context.temp_dir = tmp_path / "gone"
    assert service.is_usable() is False

    (tmp_path / "there").mkdir()
    service.app_context.temp_dir = tmp_path / "there"
    assert service.is_usable() is True


def test_usable_is_false_before_any_directory_is_chosen():
    service = _service(output_dir=None, temp_dir_sentinel=None)
    assert service.is_usable() is False


# ---------------- ensure_output_directory: prompt only when needed ----------------

def _plugin(usable, user_accepts=True):
    """`mapflow.py` coordinating the two: the service says whether writing is possible, the view
    asks when it is not."""
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.workdir_service = MagicMock()
    plugin.workdir_service.is_usable.side_effect = list(usable)
    plugin.workdir_view = MagicMock()
    plugin.workdir_view.offer_to_choose.return_value = user_accepts
    plugin.select_output_directory = MagicMock()
    return plugin


def test_a_usable_directory_is_not_questioned():
    plugin = _plugin(usable=[True])

    assert plugin.ensure_output_directory("need it") is True
    plugin.workdir_view.offer_to_choose.assert_not_called()


def test_an_unusable_directory_explains_why_one_is_needed():
    # Unusable, then usable after the user picks one.
    plugin = _plugin(usable=[False, True])

    assert plugin.ensure_output_directory("need a dir") is True
    plugin.workdir_view.offer_to_choose.assert_called_once_with("need a dir")
    plugin.select_output_directory.assert_called_once()


def test_postponing_cancels_without_opening_the_file_dialog():
    plugin = _plugin(usable=[False], user_accepts=False)

    assert plugin.ensure_output_directory("need it") is False
    plugin.select_output_directory.assert_not_called()


def test_picking_an_unusable_directory_still_reports_failure():
    """The user chose a directory, but it could not be written to — `select_output_directory` has
    already said so, and the caller must still cancel. The answer is whether the directory became
    usable, not whether the user picked something."""
    plugin = _plugin(usable=[False, False])

    assert plugin.ensure_output_directory("need it") is False
    plugin.select_output_directory.assert_called_once()
