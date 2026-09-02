"""QGIS-tier tests for adding, editing and removing imagery providers, and the zoom combo.

Untested while this lived in `mapflow.py`: every path needs the provider dialog, and the dialog
needed a plugin. With the widget reads in `ProviderView` and the decisions in the controller, the
name-collision rules and the default-provider guards can be driven directly.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PyQt5.QtCore import QObject

from mapflow.functional.controller import provider_controller as pc_mod
from mapflow.functional.controller.provider_controller import ProviderController


class _Providers(list):
    """`providers` is a list that also answers `name in providers`, as ProvidersList does."""

    def __contains__(self, item):
        if isinstance(item, str):
            return any(p.name == item for p in self)
        return list.__contains__(self, item)


def _provider(name, is_default=False):
    return SimpleNamespace(name=name, is_default=is_default)


def _controller(providers=(), user_providers=None, dialog_result=None, current=None):
    controller = ProviderController.__new__(ProviderController)
    QObject.__init__(controller)
    controller.tr = lambda text: text
    controller.provider_service = MagicMock()
    controller.provider_service.providers = _Providers(providers)
    controller.provider_service.user_providers = list(
        user_providers if user_providers is not None else providers)
    controller.provider_view = MagicMock()
    controller.provider_view.provider_index.return_value = 0
    controller.provider_dialog = MagicMock()
    controller.provider_dialog.result = dialog_result
    controller.provider_dialog.current_provider = current
    controller.app_context = SimpleNamespace(settings=MagicMock())
    controller.processing_service = MagicMock()
    return controller


@pytest.fixture(autouse=True)
def alerts(monkeypatch):
    """Everything the user was told. Autouse — an unstubbed `alert` opens a modal that never
    closes in the test container (see tests/qgis/conftest.py)."""
    said = []
    monkeypatch.setattr(pc_mod, "alert", lambda message, *a, **k: said.append(message) or True)
    monkeypatch.setattr(pc_mod, "alert_warning", lambda message, *a, **k: said.append(message))
    return said


@pytest.fixture(autouse=True)
def created(monkeypatch):
    """`create_provider` builds a model from the dialog's dict; only its name matters here."""
    monkeypatch.setattr(pc_mod, "create_provider",
                        lambda **kwargs: _provider(kwargs.get("name", "new")))


# ---------- the zoom ----------

def test_a_chosen_zoom_is_saved_and_re_prices():
    controller = _controller()
    controller.provider_view.zoom_is_default.return_value = False
    controller.provider_view.zoom_text.return_value = "16"

    controller.on_zoom_change()

    controller.app_context.settings.setValue.assert_called_once_with('zoom', "16")
    controller.processing_service.update_processing_cost.assert_called_once()


def test_the_default_zoom_entry_stores_nothing():
    """Index 0 means 'the provider's own resolution'. Storing its label would send a zoom the
    user never picked."""
    controller = _controller()
    controller.provider_view.zoom_is_default.return_value = True

    controller.on_zoom_change()

    controller.app_context.settings.setValue.assert_called_once_with('zoom', None)


# ---------- removing ----------

def test_a_default_provider_cannot_be_removed(alerts):
    controller = _controller([_provider("Mapflow", is_default=True)])

    controller.remove_provider()

    controller.provider_service.update_providers.assert_not_called()
    assert "cannot be removed" in alerts[0]


def test_removing_asks_first_and_then_removes(alerts):
    mine = _provider("Mine")
    controller = _controller([mine])

    controller.remove_provider()

    assert "Permanently remove Mine?" in alerts[0]
    assert mine not in controller.provider_service.user_providers
    controller.provider_service.update_providers.assert_called_once()


def test_declining_the_confirmation_keeps_the_provider(monkeypatch):
    mine = _provider("Mine")
    controller = _controller([mine])
    monkeypatch.setattr(pc_mod, "alert", lambda *a, **k: False)

    controller.remove_provider()

    assert mine in controller.provider_service.user_providers
    controller.provider_service.update_providers.assert_not_called()


# ---------- editing ----------

def test_a_default_provider_cannot_be_edited(alerts):
    controller = _controller([_provider("Mapflow", is_default=True)])

    controller.edit_provider()

    controller.provider_dialog.setup.assert_not_called()
    assert "cannot be edited" in alerts[0]


def test_editing_opens_the_dialog_on_the_selected_provider():
    mine = _provider("Mine")
    controller = _controller([mine])

    controller.edit_provider()

    controller.provider_dialog.setup.assert_called_once_with(mine)


# ---------- committing the dialog ----------

def test_a_dialog_closed_without_changes_does_nothing():
    controller = _controller([_provider("Mine")], dialog_result=None)

    controller.commit_provider()

    controller.provider_service.update_providers.assert_not_called()


def test_a_new_provider_is_appended_and_selected():
    controller = _controller([_provider("Mine")], dialog_result={"name": "Second"})

    controller.commit_provider()

    assert [p.name for p in controller.provider_service.user_providers] == ["Mine", "Second"]
    controller.provider_service.update_providers.assert_called_once()
    controller.provider_view.set_provider_index.assert_called_once()


def test_a_new_provider_may_not_reuse_a_name(alerts):
    controller = _controller([_provider("Mine")], dialog_result={"name": "Mine"})

    controller.commit_provider()

    assert "must be unique" in alerts[0]
    controller.provider_service.update_providers.assert_not_called()
    # Reopened with the user's input, rather than discarding what they typed.
    controller.provider_dialog.show.assert_called_once()


def test_an_edited_provider_replaces_the_old_one():
    old = _provider("Mine")
    controller = _controller([old], dialog_result={"name": "Renamed"}, current=old)

    controller.commit_provider()

    assert [p.name for p in controller.provider_service.user_providers] == ["Renamed"]
    controller.provider_service.update_providers.assert_called_once()


def test_keeping_its_own_name_while_editing_is_not_a_collision():
    """The name is unchanged, so it collides with itself — which must be allowed, or no provider
    could ever be edited without renaming it."""
    old = _provider("Mine")
    controller = _controller([old], dialog_result={"name": "Mine"}, current=old)

    controller.commit_provider()

    controller.provider_service.update_providers.assert_called_once()


def test_renaming_onto_another_providers_name_is_refused(alerts):
    old = _provider("Mine")
    controller = _controller([old, _provider("Other")],
                             dialog_result={"name": "Other"}, current=old)

    controller.commit_provider()

    assert "must be unique" in alerts[0]
    controller.provider_service.update_providers.assert_not_called()
