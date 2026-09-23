"""QGIS-tier tests: an option the user unticks stays unticked.

Three things have to hold for that. The checkboxes must keep the state they are created with, so
enabling the panel may not tick them. An option nobody has chosen must follow what its block
declares. And the stored value has to survive a restart: settings are an INI file, and a bool
written there comes back as the string "false" once it is parsed from disk again — truthy, so the
option would be on again. Within a session the value is still cached as a bool, which is why the
last test below reads a settings *file* rather than the one this process just wrote.

`spec/003_local_storage.md` types `wd/{workflow_id}/{block_name}` as a bool.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QWidget
from qgis.core import QgsSettings

from mapflow.dialogs.main_dialog import MainDialog
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.schema.workflow_def import WorkflowDef


def _wd(optional_prices=(5, 7), defaults=()):
    """A workflow def with one obligatory block and an optional one per price. `defaults` gives the
    backend's `defaultEnabled` per optional block, off for any it does not mention."""
    declared = list(defaults) + [False] * (len(optional_prices) - len(defaults))
    blocks = [{"name": "base", "displayName": "Base", "price": 10, "optional": False}]
    blocks += [{"name": f"opt_{i}", "displayName": f"Option {i}", "price": price, "optional": True,
                "defaultEnabled": declared[i]}
               for i, price in enumerate(optional_prices)]
    return WorkflowDef(id="wd-1", name="Buildings", description="", blocks=blocks)


@pytest.fixture
def service():
    """A service over a real settings object, in its own group so the test cleans up after itself."""
    settings = QgsSettings()
    settings.remove("test_model_options")
    settings.beginGroup("test_model_options")
    instance = ProcessingService.__new__(ProcessingService)
    instance.app_context = SimpleNamespace(settings=settings)
    yield instance
    settings.endGroup()
    settings.remove("test_model_options")


def test_an_unticked_option_is_remembered_as_unticked(service):
    """The round trip end to end: what `save_option_settings` writes is what `saved_model_options`
    reads back."""
    wd = _wd()

    service.save_option_settings(wd, [False, True])

    assert service.saved_model_options(wd) == [("Option 0", False), ("Option 1", True)]


def test_an_option_never_chosen_follows_what_the_block_declares(service):
    """On a fresh profile nobody has expressed a preference, and `defaultEnabled` is the backend's."""
    wd = _wd(defaults=(True, False))

    assert service.saved_model_options(wd) == [("Option 0", True), ("Option 1", False)]


def test_a_choice_the_user_made_beats_what_the_block_declares(service):
    """Unticking an option the backend enables by default must stick — it is the user's credits."""
    wd = _wd(defaults=(True, True))

    service.save_option_settings(wd, [False, True])

    assert service.saved_model_options(wd) == [("Option 0", False), ("Option 1", True)]


def test_an_unticked_option_survives_a_restart(tmp_path):
    """Read from a settings file the way the next QGIS session reads it.

    A session answers from the value it cached when it wrote it, so in-process a bool stays a bool
    and this can never fail. The next session parses the INI text instead, and a bool written there
    as the bare word `false` comes back as a string — truthy, which is how an option the user turned
    off came back on at the next start.

    The restart is staged by copying the file QSettings wrote to a path nothing has cached, rather
    than by hand-writing INI: how keys with slashes are laid out is QSettings' business, not this
    test's.
    """
    written = tmp_path / "written.ini"
    source = QSettings(str(written), QSettings.IniFormat)
    source.setValue("wd/wd-1/opt_0", False)
    source.setValue("wd/wd-1/opt_1", True)
    source.sync()

    restarted = tmp_path / "restarted.ini"
    restarted.write_bytes(written.read_bytes())
    service = ProcessingService.__new__(ProcessingService)
    service.app_context = SimpleNamespace(
        settings=QSettings(str(restarted), QSettings.IniFormat))

    assert service.app_context.settings.value("wd/wd-1/opt_0") == "false", (
        "precondition: parsed back from the file, a stored bool is a string")
    assert service.saved_model_options(_wd(defaults=(True, True))) == [
        ("Option 0", False), ("Option 1", True)]


# ---------- the checkboxes themselves ----------

def _dialog_with_options(*checked_states):
    """A MainDialog stub with the option area the checkboxes go into."""
    dialog = MainDialog.__new__(MainDialog)
    # QDialog, not QObject: `add_model_option` parents a real QCheckBox to this dialog, and a
    # widget parented to something that was never constructed as one is undefined behaviour.
    QDialog.__init__(dialog)
    dialog.modelOptions = []
    container = QWidget()
    dialog.modelOptionsLayout = QVBoxLayout(container)
    dialog._container = container  # keeps the layout's parent alive for the test's lifetime
    dialog.modelOptionsChanged = MagicMock()
    for index, checked in enumerate(checked_states):
        dialog.add_model_option(f"Option {index}", checked=checked)
    return dialog


def test_enabling_the_options_does_not_tick_them():
    """Enabling is not ticking: the saved state is set when each box is created, and the panel
    enabling them afterwards must leave it alone."""
    dialog = _dialog_with_options(False, True)

    dialog.enable_model_options(True)

    assert dialog.enabled_blocks() == [False, True]
    assert all(box.isEnabled() for box in dialog.modelOptions)


def test_a_role_that_may_not_start_a_processing_cannot_touch_the_options():
    """Starting is already refused for such a role, so offering a choice it cannot act on is worse
    than showing it greyed out."""
    dialog = _dialog_with_options(True, False)

    dialog.enable_model_options(False)

    assert not any(box.isEnabled() for box in dialog.modelOptions)
    assert dialog.enabled_blocks() == [True, False]  # and their state is still the saved one


def test_creating_an_option_does_not_announce_a_change():
    """`add_model_option` sets the state before connecting `toggled`, so a rebuild is silent. The
    cost quote depends on it: a model change is quoted by the controller, not by an echo of its own
    rebuild."""
    dialog = _dialog_with_options(True, False)
    dialog.enable_model_options(True)

    dialog.modelOptionsChanged.emit.assert_not_called()
