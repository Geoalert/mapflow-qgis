"""QGIS-tier tests: app_context.selected_image must stay in sync with the My Imagery table.

Regression: after processing an IMAGE from a mosaic, selecting another MOSAIC (or deselecting
the image) left app_context.selected_image stale, so the next processing reused the old image's
imageIds instead of the newly selected mosaic. Selecting a mosaic and clearing the image
selection must both drop the cached image.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.service.data_catalog import DataCatalogService
from mapflow.functional.app_context import AppContext


def _service():
    svc = DataCatalogService.__new__(DataCatalogService)
    svc.dlg = MagicMock()
    # len() must work on the "selected indexes" used inside on_mosaic_selection.
    svc.dlg.mosaicTable.selectedIndexes.return_value = [MagicMock()]
    svc.view = MagicMock()
    svc.api = MagicMock()
    svc.app_context = AppContext()
    return svc


def test_selecting_mosaic_clears_cached_image():
    svc = _service()
    svc.app_context.selected_image = SimpleNamespace(id="old-image-id")

    svc.on_mosaic_selection(SimpleNamespace(id="mosaic-2", name="Mosaic 2"))

    assert svc.app_context.selected_image is None


def test_deselecting_image_clears_cached_image():
    svc = _service()
    svc.app_context.selected_image = SimpleNamespace(id="old-image-id")
    svc.selected_image = MagicMock(return_value=None)  # nothing selected in the image table

    svc.check_image_selection()

    assert svc.app_context.selected_image is None


def test_selecting_image_still_sets_cached_image():
    svc = _service()
    image = SimpleNamespace(id="new-image-id")
    svc.selected_image = MagicMock(return_value=image)

    svc.check_image_selection()

    assert svc.app_context.selected_image is image
