"""QGIS-tier tests for the My Imagery wiring after C2.3.

`DataCatalogService` announces what the panel must show and is told the selection; the controller
renders and owns the dialogs. These build the *real* `DataCatalogController.__init__` against a
real service (for its signals) and a mock view/dlg, so a connection that stops being made fails
here — a test that wired its own connections could not (the C2.2b lesson).
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PyQt5.QtCore import QObject

from mapflow.functional.controller import data_catalog_controller as controller_module
from mapflow.functional.controller.data_catalog_controller import DataCatalogController
from mapflow.functional.service.data_catalog import DataCatalogService
from mapflow.model.provider.default import MyImageryProvider, ImagerySearchProvider


def _service():
    service = DataCatalogService.__new__(DataCatalogService)
    QObject.__init__(service)  # it is the announce signals we are wiring
    service.tr = lambda text: text
    return service


def _controller(service):
    """A real controller, wired by its own __init__. Kept referenced by the caller — a collected
    QObject drops its Qt connections."""
    return DataCatalogController(
        dlg=MagicMock(),
        data_catalog_service=service,
        preview_service=MagicMock(),
        view=MagicMock(),
        app_context=MagicMock())


# ---------- the service announces, the controller renders ----------

def test_a_mosaic_list_is_drawn_and_the_selection_cleared():
    service = _service()
    controller = _controller(service)

    service.mosaicsChanged.emit(["m1", "m2"])

    controller.view.display_mosaics.assert_called_once_with(["m1", "m2"])
    controller.view.clear_mosaic_selection.assert_called_once()


def test_a_reselect_redraws_and_reselects():
    service = _service()
    controller = _controller(service)

    service.mosaicReselected.emit(["m1"], "m1")

    controller.view.display_mosaics_and_reselect.assert_called_once_with(["m1"], "m1")


def test_images_preview_and_storage_reach_the_view():
    service = _service()
    controller = _controller(service)

    service.imagesChanged.emit(["i1"])
    controller.view.display_images.assert_called_once_with(["i1"])

    service.previewChanged.emit("a-qimage")
    controller.view.show_preview_s.assert_called_once_with("a-qimage")

    service.storageChanged.emit(10, 90)
    controller.view.show_storage.assert_called_once_with(10, 90)


def test_a_source_image_selects_its_mosaic_and_binds_its_row():
    service = _service()
    controller = _controller(service)
    image = SimpleNamespace(id="img-1", mosaic_id="mos-1")

    service.sourceImageReady.emit(image)

    controller.view.select_mosaic_cell.assert_called_once_with("mos-1")
    controller.view.bind_source_image.assert_called_once_with("img-1")


def test_a_source_error_opens_an_error_widget():
    service = _service()
    controller = _controller(service)

    assert controller is not None  # keep it alive: a collected QObject drops its connections

    with patch.object(controller_module, "ErrorMessageWidget") as widget:
        service.imageSourceError.emit("not found")

    widget.assert_called_once()
    widget.return_value.show.assert_called_once()


def test_a_download_url_prompts_for_a_path_and_then_saves():
    service = _service()
    controller = _controller(service)
    assert controller is not None  # keep it alive: a collected QObject drops its connections
    service.save_downloaded = MagicMock()

    with patch.object(controller_module.QFileDialog, "getSaveFileName",
                      return_value=("/tmp/out.tif", "")):
        service.downloadUrlReady.emit("https://x/y.tif", "y.tif")

    service.save_downloaded.assert_called_once_with("https://x/y.tif", "/tmp/out.tif")


def test_a_cancelled_save_dialog_downloads_nothing():
    service = _service()
    controller = _controller(service)
    assert controller is not None  # keep it alive: a collected QObject drops its connections
    service.save_downloaded = MagicMock()

    with patch.object(controller_module.QFileDialog, "getSaveFileName", return_value=("", "")):
        service.downloadUrlReady.emit("https://x/y.tif", "y.tif")

    service.save_downloaded.assert_not_called()


# ---------- switching the data source to My Imagery ----------

def test_switch_points_the_source_combo_at_my_imagery():
    service = _service()
    controller = _controller(service)
    controller.dlg.providerIndex.return_value = 0  # currently on a non-My-Imagery provider
    providers = [ImagerySearchProvider(proxy="https://e/rest"), MyImageryProvider()]

    service.switchToMyImageryRequested.emit(providers)

    controller.dlg.sourceCombo.setCurrentIndex.assert_called_once_with(1)


def test_switch_is_a_noop_when_already_on_my_imagery():
    service = _service()
    controller = _controller(service)
    controller.dlg.providerIndex.return_value = 0
    providers = [MyImageryProvider(), ImagerySearchProvider(proxy="https://e/rest")]

    service.switchToMyImageryRequested.emit(providers)

    controller.dlg.sourceCombo.setCurrentIndex.assert_not_called()


# ---------- the empty-mosaic create path ----------

def test_creating_an_empty_mosaic_calls_the_service():
    service = _service()
    service.create_mosaic = MagicMock()
    service.create_mosaic_from_images = MagicMock()
    controller = _controller(service)
    mosaic_dialog = MagicMock()
    mosaic_dialog.createMosaicCombo.currentIndex.return_value = 0
    mosaic_dialog.mosaic.return_value = "the-mosaic"

    controller._create_mosaic_from_options(mosaic_dialog)

    service.create_mosaic.assert_called_once_with("the-mosaic")
    service.create_mosaic_from_images.assert_not_called()
