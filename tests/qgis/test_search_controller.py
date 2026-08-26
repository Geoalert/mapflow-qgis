"""SearchController — the imagery-search preview dispatch.

These behaviours (`preview`, `preview_or_search`, `preview_search_from_cell`) had no direct
tests before the extraction: they ran only through the plugin. `spec/007_architecture.md` says a
step that moves code must not leave a behaviour covered by neither suite, so they are pinned here
against the new owner.

The controller reads *which* image through `SearchView` and dispatches to `PreviewService`; the
provider it acts on comes from `ProviderService`. Alerts go through the message tier, patched
here so the singleton is never touched.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mapflow.functional.controller.search_controller import SearchController
from mapflow.functional.view.search_view import SearchView
from mapflow.model.provider.default import ImagerySearchProvider


def _xyz_provider(requires_id):
    """A non-search provider (the isinstance check must send it down the XYZ path)."""
    return SimpleNamespace(requires_image_id=requires_id)


@pytest.fixture
def controller(monkeypatch):
    """A controller whose search_button/metadata_table are mocks (only `.connect` is called on
    them at construction) and whose collaborators are mocks."""
    alerts = []
    monkeypatch.setattr("mapflow.functional.controller.search_controller.alert",
                        lambda *a, **k: alerts.append(a[0] if a else ""))
    view = MagicMock(spec=SearchView)
    view.provider_index.return_value = 0
    controller = SearchController(search_service=MagicMock(),
                                  search_view=view,
                                  preview_service=MagicMock(),
                                  provider_service=SimpleNamespace(providers=[]),
                                  search_button=MagicMock(),
                                  metadata_table=MagicMock())
    controller._alerts = alerts
    return controller


# ---------- preview (double-click / Preview) ----------

def test_preview_of_search_provider_goes_to_the_catalog(controller):
    provider = ImagerySearchProvider(proxy="https://example.com/rest")
    provider.requires_id = True
    controller.provider_service.providers = [provider]
    controller.search_view.selected_image_id.return_value = "IMG-1"

    controller.preview()

    controller.preview_service.preview_catalog.assert_called_once_with(image_id="IMG-1")
    controller.preview_service.preview_xyz.assert_not_called()


def test_preview_of_xyz_provider_goes_to_xyz(controller):
    provider = _xyz_provider(requires_id=False)
    controller.provider_service.providers = [provider]
    controller.search_view.selected_image_id.return_value = None

    controller.preview()

    controller.preview_service.preview_xyz.assert_called_once_with(provider=provider,
                                                                   image_id=None)
    controller.preview_service.preview_catalog.assert_not_called()


def test_preview_requires_image_id_alerts_and_stops(controller):
    provider = _xyz_provider(requires_id=True)
    controller.provider_service.providers = [provider]
    controller.search_view.selected_image_id.return_value = None  # none selected

    controller.preview()

    assert len(controller._alerts) == 1
    controller.preview_service.preview_catalog.assert_not_called()
    controller.preview_service.preview_xyz.assert_not_called()


# ---------- preview_or_search (the Search button) ----------

def test_search_button_sends_id_provider_to_the_search_tab(controller):
    controller.provider_service.providers = [_xyz_provider(requires_id=True)]

    controller.preview_or_search()

    controller.search_view.switch_to_search_tab.assert_called_once()
    controller.preview_service.preview_catalog.assert_not_called()


def test_search_button_previews_a_non_id_provider_directly(controller):
    provider = _xyz_provider(requires_id=False)
    controller.provider_service.providers = [provider]
    controller.search_view.selected_image_id.return_value = None

    controller.preview_or_search()

    controller.search_view.switch_to_search_tab.assert_not_called()
    controller.preview_service.preview_xyz.assert_called_once()


# ---------- preview_search_from_cell (Preview column click) ----------

def test_cell_click_in_preview_column_previews_that_row(controller):
    controller.search_view.is_preview_column.return_value = True
    controller.search_view.image_id_at.return_value = "IMG-9"

    controller.preview_search_from_cell(row=3, column=1)

    controller.search_view.image_id_at.assert_called_once_with(3)
    controller.preview_service.preview_catalog.assert_called_once_with("IMG-9")


def test_cell_click_outside_preview_column_does_nothing(controller):
    controller.search_view.is_preview_column.return_value = False

    controller.preview_search_from_cell(row=3, column=0)

    controller.preview_service.preview_catalog.assert_not_called()
