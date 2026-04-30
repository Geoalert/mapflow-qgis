"""Tests for SAM Interactive service layer.

Pass 4: Processings + Workflows
Pass 5: Prompts + Point/Bbox

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
    PromptResponse,
    PromptDetailResponse,
    PromptListResponse,
    SpatialPromptResponse,
    SessionResponse,
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
    view.selected_session_id.return_value = None
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


class TestShowProcessingLayers:
    def test_calls_main_results_loader_only(self, sam_service):
        sam_service._load_processing_results_callback = MagicMock()

        sam_service.show_processing_layers("p1")

        sam_service._load_processing_results_callback.assert_called_once_with(processing_id="p1")


# ---------------------------------------------------------------------------
# Workflows are no longer user-facing — they were removed from SamService
# along with the workflow combo and per-workflow drill-down. Tests for those
# helpers were dropped; the underlying API endpoints (still on SamApi) are
# covered by tests/test_sam_api.py.
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


# ---------------------------------------------------------------------------
# create_prompt
# ---------------------------------------------------------------------------

class TestCreatePrompt:
    def test_calls_api_with_text_prompt(self, sam_service, http_mock):
        sam_service.create_prompt(text_prompt="find buildings")

        http_mock.post.assert_called_once()
        url = http_mock.post.call_args[1]["url"]
        assert "/prompts" in url
        body = json.loads(http_mock.post.call_args[1]["body"])
        assert body["text_prompt"] == "find buildings"

    def test_calls_api_with_empty_text(self, sam_service, http_mock):
        sam_service.create_prompt(text_prompt=None)

        http_mock.post.assert_called_once()


class TestCreatePromptCallback:
    PROMPT_DATA = {"id": "pr1", "text_prompt_id": "tp1", "text_prompt": "find buildings"}

    def test_appends_debug(self, sam_service, sam_view):
        reply = _make_reply(self.PROMPT_DATA)
        sam_service.create_prompt_callback(reply)

        sam_view.append_debug.assert_called_once()
        title, data = sam_view.append_debug.call_args[0]
        assert "Create Prompt" in title
        assert data["id"] == "pr1"

    def test_refreshes_prompts_list(self, sam_service, sam_view):
        reply = _make_reply(self.PROMPT_DATA)
        with patch.object(sam_service, 'list_prompts') as mock_list:
            sam_service.create_prompt_callback(reply)
            mock_list.assert_called_once()


# ---------------------------------------------------------------------------
# list_prompts
# ---------------------------------------------------------------------------

class TestListPrompts:
    def test_calls_api(self, sam_service, http_mock):
        sam_service.list_prompts()

        http_mock.get.assert_called_once()
        url = http_mock.get.call_args[1]["url"]
        assert "/prompts/page" in url


class TestListPromptsCallback:
    RESPONSE_DATA = {
        "total": 2,
        "limit": 20,
        "offset": 0,
        "items": [
            {"id": "pr1", "text_prompt_id": "tp1", "text_prompt": "find buildings"},
            {"id": "pr2", "text_prompt_id": None, "text_prompt": None},
        ],
    }

    def test_populates_view_with_prompts(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.list_prompts_callback(reply)

        sam_view.display_prompts.assert_called_once()
        items = sam_view.display_prompts.call_args[0][0]
        assert len(items) == 2
        assert items[0].id == "pr1"
        assert items[0].text_prompt == "find buildings"

    def test_appends_debug(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.list_prompts_callback(reply)

        sam_view.append_debug.assert_called_once()
        title, _ = sam_view.append_debug.call_args[0]
        assert "List Prompts" in title


# ---------------------------------------------------------------------------
# get_prompt_detail
# ---------------------------------------------------------------------------

class TestGetPromptDetailCallback:
    DETAIL_DATA = {
        "id": "pr1",
        "text_prompt_id": "tp1",
        "text_prompt": "find buildings",
        "spatial_prompts": [
            {"id": "pp1", "processing_id": "p1", "geometry_type": "point",
             "geometry": {"type": "Point", "coordinates": [37.6, 55.7]}, "positive": True},
            {"id": "bp1", "processing_id": "p1", "geometry_type": "bbox",
             "geometry": {"type": "Polygon", "coordinates": [[[37, 55], [38, 55], [38, 56], [37, 56], [37, 55]]]},
             "positive": False},
        ],
    }

    def test_populates_spatial_prompts_table(self, sam_service, sam_view):
        reply = _make_reply(self.DETAIL_DATA)
        sam_service.get_prompt_detail_callback(reply)

        sam_view.populate_spatial_prompts_table.assert_called_once()
        detail = sam_view.populate_spatial_prompts_table.call_args[0][0]
        assert len(detail) == 2
        assert isinstance(detail[0], SpatialPromptResponse)
        assert detail[0].positive is True
        assert detail[1].positive is False

    def test_stores_prompt_detail(self, sam_service, sam_view):
        reply = _make_reply(self.DETAIL_DATA)
        sam_service.get_prompt_detail_callback(reply)

        detail = sam_service._last_prompt_detail
        assert isinstance(detail, PromptDetailResponse)
        assert len(detail.spatial_prompts) == 2
        assert detail.spatial_prompts[0].positive is True
        assert detail.spatial_prompts[1].positive is False

    def test_appends_debug(self, sam_service, sam_view):
        reply = _make_reply(self.DETAIL_DATA)
        sam_service.get_prompt_detail_callback(reply)

        sam_view.append_debug.assert_called_once()
        title, _ = sam_view.append_debug.call_args[0]
        assert "Prompt Detail" in title


# ---------------------------------------------------------------------------
# add_point_prompt
# ---------------------------------------------------------------------------

class TestAddPointPrompt:
    def test_calls_api(self, sam_service, http_mock):
        geojson = {"type": "Point", "coordinates": [37.6, 55.7]}
        sam_service.add_point_prompt(
            prompt_id="pr1", processing_id="p1",
            geometry=geojson, positive=True,
        )

        http_mock.post.assert_called_once()
        url = http_mock.post.call_args[1]["url"]
        assert "/prompts/pr1/point_prompts" in url
        body = json.loads(http_mock.post.call_args[1]["body"])
        assert body["processing_id"] == "p1"
        assert body["geometry"] == geojson
        assert body["positive"] is True


class TestAddPointPromptCallback:
    RESPONSE_DATA = {
        "id": "pp1", "processing_id": "p1",
        "geometry": {"type": "Point", "coordinates": [37.6, 55.7]},
        "positive": True,
    }

    def test_appends_debug(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.add_point_prompt_callback(reply)

        sam_view.append_debug.assert_called_once()
        title, data = sam_view.append_debug.call_args[0]
        assert "Point Prompt" in title

    def test_adds_to_map_layer(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.add_point_prompt_callback(reply)

        sam_view.add_prompt_to_map.assert_called_once()
        prompt = sam_view.add_prompt_to_map.call_args[0][0]
        assert isinstance(prompt, SpatialPromptResponse)
        assert prompt.positive is True


# ---------------------------------------------------------------------------
# add_bbox_prompt
# ---------------------------------------------------------------------------

class TestAddBboxPrompt:
    def test_calls_api(self, sam_service, http_mock):
        geojson = {"type": "Polygon", "coordinates": [[[37, 55], [38, 55], [38, 56], [37, 56], [37, 55]]]}
        sam_service.add_bbox_prompt(
            prompt_id="pr1", processing_id="p1",
            geometry=geojson, positive=False,
        )

        http_mock.post.assert_called_once()
        url = http_mock.post.call_args[1]["url"]
        assert "/prompts/pr1/bbox_prompts" in url
        body = json.loads(http_mock.post.call_args[1]["body"])
        assert body["positive"] is False


class TestAddBboxPromptCallback:
    RESPONSE_DATA = {
        "id": "bp1", "processing_id": "p1",
        "geometry": {"type": "Polygon", "coordinates": [[[37, 55], [38, 55], [38, 56], [37, 56], [37, 55]]]},
        "positive": False,
    }

    def test_appends_debug(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.add_bbox_prompt_callback(reply)

        sam_view.append_debug.assert_called_once()
        title, _ = sam_view.append_debug.call_args[0]
        assert "Bbox Prompt" in title

    def test_adds_to_map_layer(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.add_bbox_prompt_callback(reply)

        sam_view.add_prompt_to_map.assert_called_once()
        prompt = sam_view.add_prompt_to_map.call_args[0][0]
        assert isinstance(prompt, SpatialPromptResponse)
        assert prompt.positive is False


# ---------------------------------------------------------------------------
# Session creation has no dedicated endpoint anymore — sessions are created
# implicitly by POST /inference. POST /sessions/{id}/copy was also removed.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# get_session_detail — drives session panels only; map/layer changes must
# be explicit (Result button) or deliberate (double-click), not single-click.
# ---------------------------------------------------------------------------

class TestGetSessionDetailCallback:
    RESPONSE_DATA = {
        "id": "s1", "processing_id": "p1",
        "inferences": [{"id": "i1", "status": "done"}],
        "vector_layer": {"id": "l1", "tile_url": "https://tiles", "tile_json_url": "https://tiles.json"},
    }
    IN_PROGRESS_DATA = {
        "id": "s1", "processing_id": "p1",
        "inferences": [{"id": "i1", "status": "in_progress"}],
        "vector_layer": None,
    }

    def test_displays_session(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.get_session_detail_callback(reply)

        sam_view.display_session.assert_called_once()
        session = sam_view.display_session.call_args[0][0]
        assert isinstance(session, SessionResponse)
        assert session.id == "s1"
        assert len(session.inferences) == 1

    def test_appends_debug(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.get_session_detail_callback(reply)

        title, _ = sam_view.append_debug.call_args_list[0][0]
        assert "Session Detail" in title

    def test_does_not_fetch_partial_result_automatically(self, sam_service, http_mock):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.get_session_detail_callback(reply)

        # Session detail updates view state only. Result fetching stays
        # explicit via get_result() / Result button.
        result_calls = [c for c in http_mock.get.call_args_list
                        if "/result/s1" in c[1]["url"]]
        assert len(result_calls) == 0

    def test_skips_partial_result_when_all_in_progress(self, sam_service, http_mock):
        reply = _make_reply(self.IN_PROGRESS_DATA)
        sam_service.get_session_detail_callback(reply)

        result_calls = [c for c in http_mock.get.call_args_list
                        if "/result/s1" in c[1]["url"]]
        assert len(result_calls) == 0

    def test_no_separate_prompts_call(self, sam_service, http_mock):
        # The frozen prompt snapshot is embedded in SessionResponse, so the
        # session detail flow no longer issues GET /sessions/{id}/prompts.
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.get_session_detail_callback(reply)

        prompt_calls = [c for c in http_mock.get.call_args_list
                        if "/sessions/s1/prompts" in c[1]["url"]]
        assert len(prompt_calls) == 0


# ---------------------------------------------------------------------------
# refresh_session_status — manual session-level polling entry point.
# ---------------------------------------------------------------------------

class TestRefreshSessionStatus:
    def test_calls_get_session(self, sam_service, http_mock):
        sam_service.refresh_session_status("s1")

        session_calls = [c for c in http_mock.get.call_args_list
                         if c[1]["url"].endswith("/sessions/s1")]
        assert len(session_calls) == 1


# ---------------------------------------------------------------------------
# list_sessions
# ---------------------------------------------------------------------------

class TestListSessionsCallback:
    RESPONSE_DATA = {
        "items": [
            {"id": "s1", "processing_id": "p1",
             "inferences": [], "vector_layer": {"id": "l1", "tile_url": "https://tiles", "tile_json_url": "https://tiles.json"}},
            {"id": "s2", "processing_id": "p1",
             "inferences": [], "vector_layer": {"id": "l2", "tile_url": "https://tiles2", "tile_json_url": "https://tiles2.json"}},
        ],
    }

    def test_displays_sessions(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.list_sessions_callback(reply)

        sam_view.display_sessions.assert_called_once()
        sessions = sam_view.display_sessions.call_args[0][0]
        assert len(sessions) == 2
        assert isinstance(sessions[0], SessionResponse)
        assert sessions[0].id == "s1"

    def test_appends_debug(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.list_sessions_callback(reply)

        sam_view.append_debug.assert_called_once()
        title, _ = sam_view.append_debug.call_args[0]
        assert "List Sessions" in title

    def test_empty_response_non_list(self, sam_service, sam_view):
        reply = _make_reply({})
        sam_service.list_sessions_callback(reply)

        sam_view.display_sessions.assert_called_once()
        sessions = sam_view.display_sessions.call_args[0][0]
        assert len(sessions) == 0

    def test_fetches_selected_session_detail_after_list_refresh(self, sam_service, sam_view):
        sam_view.selected_session_id.return_value = "s2"
        sam_service.get_session_detail = MagicMock()

        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.list_sessions_callback(reply)

        sam_service.get_session_detail.assert_called_once_with("s2")

    def test_clears_session_display_when_no_session_selected(self, sam_service, sam_view):
        reply = _make_reply({"items": []})
        sam_service.list_sessions_callback(reply)

        sam_view.clear_session_display.assert_called_once()


# ---------------------------------------------------------------------------
# create_inference
# ---------------------------------------------------------------------------

class TestCreateInferenceService:
    def test_calls_api_with_confidence_threshold(self, sam_service, http_mock):
        geojson = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        sam_service.create_inference(
            "proc-1",
            "prompt-1",
            geojson,
            confidence_threshold=0.55,
        )

        http_mock.post.assert_called_once()
        url = http_mock.post.call_args[1]["url"]
        assert "/inference" in url
        body = json.loads(http_mock.post.call_args[1]["body"])
        assert body["processing_id"] == "proc-1"
        assert body["prompt_id"] == "prompt-1"
        assert body["confidence_threshold"] == 0.55


class TestCreateInferenceCallback:
    # POST /inference now returns SessionResponse with the N inferences
    # just dispatched (one per workflow whose AOI intersects the request).
    RESPONSE_DATA = {
        "id": "s1", "processing_id": "p1",
        "inferences": [
            {"id": "inf1", "status": "in_progress"},
            {"id": "inf2", "status": "in_progress"},
        ],
        "vector_layer": {"id": "l1", "tile_url": "https://tiles",
                          "tile_json_url": "https://tiles.json"},
    }

    def test_renders_session(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.create_inference_callback(reply)

        sam_view.display_session.assert_called_once()
        session = sam_view.display_session.call_args[0][0]
        assert isinstance(session, SessionResponse)
        assert len(session.inferences) == 2

    def test_adds_session_to_table(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.create_inference_callback(reply)

        sam_view.add_session_to_table.assert_called_once()
        session = sam_view.add_session_to_table.call_args[0][0]
        assert isinstance(session, SessionResponse)
        assert session.id == "s1"

    def test_appends_debug(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.create_inference_callback(reply)

        sam_view.append_debug.assert_called_once()
        title, data = sam_view.append_debug.call_args[0]
        assert "Create Inference" in title
        assert data["id"] == "s1"

    def test_enables_inference_refresh(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.create_inference_callback(reply)

        sam_view.set_inference_refresh_enabled.assert_called_once_with(True)


class TestCreateSessionInferenceService:
    def test_calls_api_without_confidence_threshold(self, sam_service, http_mock):
        geojson = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        sam_service.create_session_inference(
            "session-1",
            geojson,
        )

        http_mock.post.assert_called_once()
        url = http_mock.post.call_args[1]["url"]
        assert "/sessions/session-1/inferences" in url
        body = json.loads(http_mock.post.call_args[1]["body"])
        assert "workflow_id" not in body
        assert "confidence_threshold" not in body


class TestCreateSessionInferenceCallback:
    # POST /sessions/{id}/inferences also returns the updated SessionResponse.
    RESPONSE_DATA = {
        "id": "s1", "processing_id": "p1",
        "inferences": [
            {"id": "inf1", "status": "done"},
            {"id": "inf3", "status": "in_progress"},
        ],
        "vector_layer": {"id": "l1", "tile_url": "https://tiles",
                          "tile_json_url": "https://tiles.json"},
    }

    def test_renders_session(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.create_session_inference_callback(reply)

        sam_view.display_session.assert_called_once()
        session = sam_view.display_session.call_args[0][0]
        assert isinstance(session, SessionResponse)
        assert len(session.inferences) == 2

    def test_appends_debug(self, sam_service, sam_view):
        reply = _make_reply(self.RESPONSE_DATA)
        sam_service.create_session_inference_callback(reply)

        sam_view.append_debug.assert_called_once()
        title, data = sam_view.append_debug.call_args[0]
        assert "Session Inference" in title
        assert data["id"] == "s1"


# ---------------------------------------------------------------------------
# Per-inference WE drill-down was removed — the abstract status from the
# session-level call is the only signal the user-facing UI exposes.
# GET /inference/{id} stays available on SamApi for debug, but the service
# no longer wires it to a click handler.
# ---------------------------------------------------------------------------
# get_result — backend now returns a raw GeoJSON FeatureCollection (or 204).
# ---------------------------------------------------------------------------

class TestGetResultCallback:
    GEOJSON = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": {"type": "Polygon",
                                              "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
             "properties": {}},
        ],
    }

    def test_loads_result_layer_with_session_id(self, sam_service, sam_view):
        reply = _make_reply(self.GEOJSON)
        sam_service.get_result_callback(reply, session_id="s1")

        sam_view.load_result_layer.assert_called_once_with(self.GEOJSON, session_id="s1")

    def test_silently_skips_empty_response(self, sam_service, sam_view):
        # 204 No Content — backend returns no body when no result is ready.
        reply = MagicMock()
        reply.readAll.return_value.data.return_value = b""
        sam_service.get_result_callback(reply, session_id="s1")

        sam_view.load_result_layer.assert_not_called()
