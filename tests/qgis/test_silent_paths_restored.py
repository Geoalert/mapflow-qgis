"""The four restored request paths now use the default (throttled) error handler.

Before the report throttle these polled/fetched silently — a server error reached nobody. The
throttle bounds repeat dialogs, so they take the default handler back (error-reporting step 3). The
"handler fires on error" logic lives in the unchanged `Http.response_dispatcher`; what step 3
changed is only the flag these calls pass, so that is what is asserted.
"""
from unittest.mock import MagicMock

from mapflow.functional.service.account_service import AccountService
from mapflow.functional.api.processing_api import ProcessingApi
from mapflow.functional.api.data_catalog_api import DataCatalogApi
from mapflow.schema.processing import ProcessingsRequest


def _kwargs(mock_method):
    mock_method.assert_called_once()
    return mock_method.call_args.kwargs


def _assert_reports(kwargs):
    assert kwargs.get("use_default_error_handler") is True, "the path must report its errors"
    assert "error_handler" not in kwargs, "it uses the default handler, not its own"


def test_the_status_poll_reports_its_errors():
    service = AccountService.__new__(AccountService)
    service.http = MagicMock()
    service.server = "https://example.com/rest"
    service.apply_status = MagicMock()

    service.refresh_status()

    _assert_reports(_kwargs(service.http.get))


def test_the_processings_page_reports_its_errors():
    api = ProcessingApi.__new__(ProcessingApi)
    api.http = MagicMock()

    api.get_processings(project_id="p-1", request_body=ProcessingsRequest(), callback=MagicMock())

    _assert_reports(_kwargs(api.http.post))


def test_loading_a_mosaic_and_its_images_reports_errors():
    api = DataCatalogApi.__new__(DataCatalogApi)
    api.http = MagicMock()
    api.server = "https://example.com/rest"

    api.get_mosaic(mosaic_id="m-1", callback=MagicMock())
    _assert_reports(_kwargs(api.http.get))

    api.http.get.reset_mock()
    api.get_mosaic_images(mosaic_id="m-1", callback=MagicMock())
    _assert_reports(_kwargs(api.http.get))
