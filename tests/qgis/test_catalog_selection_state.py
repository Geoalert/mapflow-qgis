"""QGIS-tier tests: app_context.selected_image must stay in sync with the My Imagery table.

Regression: after processing an IMAGE from a mosaic, selecting another MOSAIC (or deselecting
the image) left app_context.selected_image stale, so the next processing reused the old image's
imageIds instead of the newly selected mosaic. Selecting a mosaic and clearing the image
selection must both drop the cached image.

The selection orchestration moved from the service to `DataCatalogController` in C2.3 (a service
reads no table), so these drive the controller.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from PyQt5.QtCore import QObject

from mapflow.functional.controller.data_catalog_controller import DataCatalogController
from mapflow.functional.app_context import AppContext


def _controller():
    controller = DataCatalogController.__new__(DataCatalogController)
    QObject.__init__(controller)
    controller.dlg = MagicMock()
    # len() must work on the "selected indexes" used by the dedup guard in on_mosaic_selection.
    controller.dlg.mosaicTable.selectedIndexes.return_value = [MagicMock()]
    controller.view = MagicMock()
    controller.service = MagicMock()
    controller.app_context = AppContext()
    return controller


def test_selecting_mosaic_clears_cached_image():
    controller = _controller()
    controller.app_context.selected_image = SimpleNamespace(id="old-image-id")

    controller.on_mosaic_selection(SimpleNamespace(id="mosaic-2", name="Mosaic 2"))

    assert controller.app_context.selected_image is None


def test_deselecting_image_clears_cached_image():
    controller = _controller()
    controller.app_context.selected_image = SimpleNamespace(id="old-image-id")
    controller.service.selected_image.return_value = None  # nothing selected in the image table

    controller.check_image_selection()

    assert controller.app_context.selected_image is None


def test_selecting_image_still_sets_cached_image():
    controller = _controller()
    image = SimpleNamespace(id="new-image-id")
    controller.service.selected_image.return_value = image

    controller.check_image_selection()

    assert controller.app_context.selected_image is image
