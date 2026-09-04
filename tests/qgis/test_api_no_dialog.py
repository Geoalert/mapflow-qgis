"""QGIS-tier tests: the api clients hold no dialog (C2.6, the last of Phase C2).

`ProcessingApi` and `DataCatalogApi` took the main dialog as a constructor argument — the last
`dlg` parameters in the api/service layers. `ProcessingApi` never used it; `DataCatalogApi` used it
in one place, to write "Preview is unavailable" into the preview pane, which is now announced for
the view to draw. Dropping the parameter is what let `ProcessingService` and `DataCatalogService`
drop their own `dlg` too, clearing four `dialog-param` allowlist entries.
"""
import inspect
from unittest.mock import MagicMock

from PyQt5.QtCore import QObject

from mapflow.functional.api.processing_api import ProcessingApi
from mapflow.functional.api.data_catalog_api import DataCatalogApi
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.functional.service.data_catalog import DataCatalogService


def test_no_api_or_service_constructor_takes_a_dialog():
    for cls in (ProcessingApi, DataCatalogApi, ProcessingService, DataCatalogService):
        params = set(inspect.signature(cls.__init__).parameters)
        assert "dlg" not in params, f"{cls.__name__} still takes a dlg"


def test_processing_api_builds_without_a_dialog():
    api = ProcessingApi(http=MagicMock(), iface=MagicMock(), result_loader=MagicMock())
    assert not hasattr(api, "dlg")


def test_a_failed_preview_is_announced_not_drawn():
    """The api used to write straight into the preview pane; it emits instead, and the view (wired
    in mapflow.py) renders. Announcing keeps the api widget-free."""
    api = DataCatalogApi.__new__(DataCatalogApi)
    QObject.__init__(api)
    announced = []
    api.previewUnavailable.connect(lambda: announced.append(True))

    api.preview_s_error_handler(MagicMock())

    assert announced == [True]
