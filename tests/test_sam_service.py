"""Tests for SAM Interactive service layer (Pass 4: Processings + Workflows).

Tests verify that SamService correctly:
- parses API responses into schema objects
- updates the view with parsed data
- tracks pagination state
- outputs raw JSON to debug panel
"""
import json
from unittest.mock import MagicMock, patch, call

import pytest

from mapflow.schema.sam import (
    ProcessingListResponse,
    ProcessingSummaryResponse,
    ProcessingDetailResponse,
    WorkflowSummaryResponse,
)


SERVER = "https://whitemaps-test.mapflow.ai/rest"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_reply(data: dict) -> MagicMock:
    """Create a mock QNetworkReply whose readAll().data() returns JSON bytes."""
    reply = MagicMock()
    encoded = json.dumps(data).encode()
    reply.readAll.return_value.data.return_value = encoded
    return reply


@pytest.fixture()
def sam_api(http_mock):
    from mapflow.functional.api.sam_api import SamApi
    return SamApi(http=http_mock, server=SERVER)


@pytest.fixture()
def sam_view():
    view = MagicMock()
    return view


@pytest.fixture()
def sam_service(sam_api, sam_view):
    from mapflow.functional.service.sam import SamService
    service = SamService.__new__(SamService)
    service.api = sam_api
    service.view = sam_view
    service._offset = 0
    service._limit = 20
    service._total = 0
    return service


# ---------------------------------------------------------------------------
# list_processings
# ---------------------------------------------------------------------------

class TestListProcessings:
    def test_calls_api_with_pagination(self, sam_service, http_mock):
        sam_service._offset = 40
        sam_service._limit = 10
        sam_service.list_processings()

        http_mock.get.assert_called_once()
        url = http_mock.get.call_args[1]["url"]
        assert "limit=10" in url
        assert "offset=40" in url

    def test_calls_api_with_filter(self, sam_service, http_mock):
        sam_service.list_processings(filter_="test-name")

        url = http_mock.get.call_args[1]["url"]
        assert "filter=test-name" in url


class TestListProcessingsCallback:
    RESPONSE_DATA = {
        "total": 2,
        "limit": 20,
        "offset": 0,
        "items": [
            {"id": "p1", "name": "proc-1", "status": "done",
             "created_at": "2025-01-01T00:00:00"},
            {"id": "p2", "name": "proc-2", "status": "running",
             "created_at": "2025-01-02T00:00:00"},
        ],
    }

    def test_populates_view_with_processings(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.list_processings_callback(reply)

        sam_view.display_processings.assert_called_once()
        items = sam_view.display_processings.call_args[0][0]
        assert len(items) == 2
        assert items[0].id == "p1"
        assert items[1].name == "proc-2"

    def test_updates_pagination_state(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.list_processings_callback(reply)

        assert sam_service._total == 2

    def test_appends_debug_output(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.list_processings_callback(reply)

        sam_view.append_debug.assert_called_once()
        title, data = sam_view.append_debug.call_args[0]
        assert "List Processings" in title
        assert data["total"] == 2

    def test_empty_response(self, sam_service, sam_view):
        reply = _make_reply({"total": 0, "limit": 20, "offset": 0, "items": []})
        sam_service.list_processings_callback(reply)

        sam_view.display_processings.assert_called_once()
        items = sam_view.display_processings.call_args[0][0]
        assert len(items) == 0


# ---------------------------------------------------------------------------
# get_processing (detail)
# ---------------------------------------------------------------------------

class TestGetProcessingCallback:
    DETAIL_DATA = {
        "id": "p1",
        "name": "proc-1",
        "status": "done",
        "embedding_uri": "s3://bucket/embed",
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T01:00:00",
        "sessions": ["s1", "s2"],
    }

    def test_appends_debug_with_detail(self, sam_service, sam_view):
        reply = _make_reply(self.DETAIL_DATA)
        sam_service.get_processing_callback(reply)

        sam_view.append_debug.assert_called_once()
        title, data = sam_view.append_debug.call_args[0]
        assert "Processing Detail" in title
        assert data["id"] == "p1"

    def test_displays_sessions_count(self, sam_service, sam_view):
        reply = _make_reply(self.DETAIL_DATA)
        sam_service.get_processing_callback(reply)

        sam_view.display_processing_detail.assert_called_once()
        detail = sam_view.display_processing_detail.call_args[0][0]
        assert isinstance(detail, ProcessingDetailResponse)
        assert len(detail.sessions) == 2


# ---------------------------------------------------------------------------
# list_workflows
# ---------------------------------------------------------------------------

class TestListWorkflowsCallback:
    WORKFLOWS_DATA = [
        {"id": "w1", "processing_id": "p1", "status": "done",
         "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
         "embedding_uri": "s3://bucket/embed1"},
        {"id": "w2", "processing_id": "p1", "status": "running",
         "geometry": None, "embedding_uri": None},
    ]

    def test_appends_debug_with_workflows(self, sam_service, sam_view):
        reply = _make_reply(self.WORKFLOWS_DATA)
        sam_service.list_workflows_callback(reply)

        sam_view.append_debug.assert_called_once()
        title, data = sam_view.append_debug.call_args[0]
        assert "Workflows" in title

    def test_displays_workflows(self, sam_service, sam_view):
        reply = _make_reply(self.WORKFLOWS_DATA)
        sam_service.list_workflows_callback(reply)

        sam_view.display_workflows.assert_called_once()
        workflows = sam_view.display_workflows.call_args[0][0]
        assert len(workflows) == 2
        assert isinstance(workflows[0], WorkflowSummaryResponse)
        assert workflows[0].status == "done"
        assert workflows[1].embedding_uri is None


# ---------------------------------------------------------------------------
# get_workflow (detail)
# ---------------------------------------------------------------------------

class TestGetWorkflowCallback:
    WORKFLOW_DATA = {
        "id": "w1",
        "processing_id": "p1",
        "status": "done",
        "external_id": 42,
        "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
        "raw_raster_uri": "s3://bucket/raster",
        "embedding_uri": "s3://bucket/embed",
    }

    def test_appends_debug_with_workflow_detail(self, sam_service, sam_view):
        reply = _make_reply(self.WORKFLOW_DATA)
        sam_service.get_workflow_callback(reply)

        sam_view.append_debug.assert_called_once()
        title, data = sam_view.append_debug.call_args[0]
        assert "Workflow Detail" in title
        assert data["id"] == "w1"


# ---------------------------------------------------------------------------
# Pagination helpers
# ---------------------------------------------------------------------------

class TestPagination:
    def test_next_page_increments_offset(self, sam_service, http_mock):
        sam_service._total = 50
        sam_service._offset = 0
        sam_service._limit = 20

        sam_service.next_page()
        assert sam_service._offset == 20

    def test_next_page_clamps_to_total(self, sam_service, http_mock):
        sam_service._total = 25
        sam_service._offset = 20
        sam_service._limit = 20

        sam_service.next_page()
        # offset should not go beyond total
        assert sam_service._offset == 20

    def test_prev_page_decrements_offset(self, sam_service, http_mock):
        sam_service._total = 50
        sam_service._offset = 20
        sam_service._limit = 20

        sam_service.prev_page()
        assert sam_service._offset == 0

    def test_prev_page_clamps_to_zero(self, sam_service, http_mock):
        sam_service._total = 50
        sam_service._offset = 0
        sam_service._limit = 20

        sam_service.prev_page()
        assert sam_service._offset == 0

    def test_has_next_page(self, sam_service):
        sam_service._total = 50
        sam_service._offset = 0
        sam_service._limit = 20
        assert sam_service.has_next_page is True

        sam_service._offset = 40
        assert sam_service.has_next_page is False

    def test_has_prev_page(self, sam_service):
        sam_service._offset = 0
        assert sam_service.has_prev_page is False

        sam_service._offset = 20
        assert sam_service.has_prev_page is True
