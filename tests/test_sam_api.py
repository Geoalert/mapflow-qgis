"""Tests for SAM Interactive API client.

All HTTP calls are mocked — these tests verify that SamApi methods
call the correct Http method with the expected URL and body.
"""
import json

from mapflow.functional.api.sam_api import SamApi
from mapflow.schema.sam import (
    ProcessingCreateRequest,
    PromptCreateRequest,
    PromptUpdateRequest,
    PointPromptRequest,
    BboxPromptRequest,
    SessionCreateRequest,
    SessionInferenceCreateRequest,
    SessionNameUpdateRequest,
    InferenceCreateRequest,
    parse_confidence_threshold,
)

SERVER = "https://whitemaps-test.mapflow.ai/rest"


def _noop(*args, **kwargs):
    """Dummy callback."""
    pass


# ---------------------------------------------------------------------------
# WDID endpoint
# ---------------------------------------------------------------------------

class TestGetWdid:
    def test_calls_get_with_correct_url(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.get_wdid(callback=_noop)

        http_mock.get.assert_called_once()
        url = http_mock.get.call_args[1]["url"]
        assert url == f"{SERVER}/sam-interactive/wdid"


# ---------------------------------------------------------------------------
# Processing endpoints
# ---------------------------------------------------------------------------

class TestCreateProcessing:
    def test_calls_post_with_correct_url_and_body(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        request = ProcessingCreateRequest(
            name="test-proc",
            projectId="proj-1",
            geometry={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
            params={"sourceParams": {}},
            text_prompt="detect buildings",
            confidence_threshold=0.65,
        )
        api.create_processing(request, callback=_noop)

        http_mock.post.assert_called_once()
        call_kwargs = http_mock.post.call_args[1]
        assert call_kwargs["url"] == f"{SERVER}/processings"
        body = json.loads(call_kwargs["body"].decode())
        assert body["name"] == "test-proc"
        assert body["text_prompt"] == "detect buildings"
        assert body["confidence_threshold"] == 0.65
        assert body["params"] == {"sourceParams": {}}
        assert "geometry" in body


class TestListProcessings:
    def test_default_pagination(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.list_processings(callback=_noop)

        http_mock.get.assert_called_once()
        url = http_mock.get.call_args[1]["url"]
        assert "processings/page" in url
        assert "limit=20" in url
        assert "offset=0" in url

    def test_with_filter(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.list_processings(callback=_noop, filter_="test")

        url = http_mock.get.call_args[1]["url"]
        assert "filter=test" in url


class TestGetProcessing:
    def test_calls_get_with_id(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.get_processing("proc-123", callback=_noop)

        url = http_mock.get.call_args[1]["url"]
        assert url == f"{SERVER}/processings/proc-123"


class TestGetProcessingWorkflows:
    def test_calls_get(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.get_processing_workflows("proc-123", callback=_noop)

        url = http_mock.get.call_args[1]["url"]
        assert url == f"{SERVER}/processings/proc-123/workflows"


class TestGetProcessingSessions:
    def test_calls_get(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.get_processing_sessions("proc-123", callback=_noop)

        url = http_mock.get.call_args[1]["url"]
        assert url == f"{SERVER}/processings/proc-123/sessions"


class TestGetProcessingResults:
    def test_calls_get(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.get_processing_results("proc-123", callback=_noop)

        url = http_mock.get.call_args[1]["url"]
        assert url == f"{SERVER}/processings/proc-123/results"


class TestGetWorkflow:
    def test_calls_get(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.get_workflow("wf-456", callback=_noop)

        url = http_mock.get.call_args[1]["url"]
        assert url == f"{SERVER}/workflows/wf-456"


# ---------------------------------------------------------------------------
# Prompt endpoints
# ---------------------------------------------------------------------------

class TestCreatePrompt:
    def test_calls_post(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        request = PromptCreateRequest(text_prompt="find roads")
        api.create_prompt(request, callback=_noop)

        http_mock.post.assert_called_once()
        call_kwargs = http_mock.post.call_args[1]
        assert call_kwargs["url"] == f"{SERVER}/prompts"
        body = json.loads(call_kwargs["body"].decode())
        assert body["text_prompt"] == "find roads"

    def test_empty_prompt(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        request = PromptCreateRequest()
        api.create_prompt(request, callback=_noop)

        body = json.loads(http_mock.post.call_args[1]["body"].decode())
        assert body == {}


class TestListPrompts:
    def test_default_pagination(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.list_prompts(callback=_noop)

        url = http_mock.get.call_args[1]["url"]
        assert "prompts/page" in url
        assert "limit=20" in url


class TestGetPrompt:
    def test_calls_get(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.get_prompt("prompt-789", callback=_noop)

        url = http_mock.get.call_args[1]["url"]
        assert url == f"{SERVER}/prompts/prompt-789"


class TestAddPointPrompt:
    def test_calls_post_with_geometry(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        request = PointPromptRequest(
            processing_id="proc-1",
            geometry={"type": "Point", "coordinates": [37.6, 55.7]},
            positive=True,
        )
        api.add_point_prompt("prompt-1", request, callback=_noop)

        call_kwargs = http_mock.post.call_args[1]
        assert call_kwargs["url"] == f"{SERVER}/prompts/prompt-1/point_prompts"
        body = json.loads(call_kwargs["body"].decode())
        assert body["geometry"]["type"] == "Point"
        assert body["positive"] is True


class TestAddBboxPrompt:
    def test_calls_post_with_polygon(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        bbox_geom = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
        }
        request = BboxPromptRequest(
            processing_id="proc-1",
            geometry=bbox_geom,
            positive=False,
        )
        api.add_bbox_prompt("prompt-1", request, callback=_noop)

        call_kwargs = http_mock.post.call_args[1]
        assert call_kwargs["url"] == f"{SERVER}/prompts/prompt-1/bbox_prompts"
        body = json.loads(call_kwargs["body"].decode())
        assert body["positive"] is False


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------

class TestCreateSession:
    def test_calls_post(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        request = SessionCreateRequest(processing_id="proc-1", prompt_id="prompt-1")
        api.create_session(request, callback=_noop)

        call_kwargs = http_mock.post.call_args[1]
        assert call_kwargs["url"] == f"{SERVER}/sessions"
        body = json.loads(call_kwargs["body"].decode())
        assert body["processing_id"] == "proc-1"
        assert body["prompt_id"] == "prompt-1"


class TestGetSession:
    def test_calls_get(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.get_session("sess-1", callback=_noop)

        url = http_mock.get.call_args[1]["url"]
        assert url == f"{SERVER}/sessions/sess-1"


class TestCopySession:
    def test_calls_post(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.copy_session("sess-1", callback=_noop)

        call_kwargs = http_mock.post.call_args[1]
        assert call_kwargs["url"] == f"{SERVER}/sessions/sess-1/copy"


class TestUpdateSessionName:
    def test_calls_patch(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        request = SessionNameUpdateRequest(name="Session A")
        api.update_session_name("sess-1", request, callback=_noop)

        http_mock.patch.assert_called_once()
        call_kwargs = http_mock.patch.call_args[1]
        assert call_kwargs["url"] == f"{SERVER}/sessions/sess-1"
        body = json.loads(call_kwargs["body"].decode())
        assert body["name"] == "Session A"


class TestUpdatePrompt:
    def test_calls_patch_with_name_and_text_prompt(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        request = PromptUpdateRequest(name="Prompt A", text_prompt="find roads")
        api.update_prompt("prompt-1", request, callback=_noop)

        http_mock.patch.assert_called_once()
        call_kwargs = http_mock.patch.call_args[1]
        assert call_kwargs["url"] == f"{SERVER}/prompts/prompt-1"
        body = json.loads(call_kwargs["body"].decode())
        assert body["name"] == "Prompt A"
        assert body["text_prompt"] == "find roads"


# ---------------------------------------------------------------------------
# Inference endpoints
# ---------------------------------------------------------------------------

class TestCreateInference:
    def test_calls_post(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        request = InferenceCreateRequest(
            prompt_id="prompt-1",
            workflow_id="wf-1",
            geometry={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
            confidence_threshold=0.8,
        )
        api.create_inference(request, callback=_noop)

        call_kwargs = http_mock.post.call_args[1]
        assert call_kwargs["url"] == f"{SERVER}/inference"
        body = json.loads(call_kwargs["body"].decode())
        assert body["prompt_id"] == "prompt-1"
        assert body["workflow_id"] == "wf-1"
        assert body["confidence_threshold"] == 0.8


class TestCreateSessionInference:
    def test_calls_post(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        request = SessionInferenceCreateRequest(
            workflow_id="wf-1",
            geometry={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
            confidence_threshold=0.25,
        )
        api.create_session_inference("sess-1", request, callback=_noop)

        call_kwargs = http_mock.post.call_args[1]
        assert call_kwargs["url"] == f"{SERVER}/sessions/sess-1/inferences"
        body = json.loads(call_kwargs["body"].decode())
        assert body["workflow_id"] == "wf-1"
        assert body["confidence_threshold"] == 0.25


class TestGetInference:
    def test_calls_get(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.get_inference("inf-1", callback=_noop)

        url = http_mock.get.call_args[1]["url"]
        assert url == f"{SERVER}/inference/inf-1"


# ---------------------------------------------------------------------------
# Result endpoints
# ---------------------------------------------------------------------------

class TestGetResult:
    def test_calls_get(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.get_result("sess-1", callback=_noop)

        url = http_mock.get.call_args[1]["url"]
        assert url == f"{SERVER}/result/sess-1"


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestSchemas:
    def test_processing_list_response_parses_items(self):
        from mapflow.schema.sam import ProcessingListResponse
        data = {
            "total": 2, "limit": 20, "offset": 0,
            "items": [
                {"id": "1", "name": "p1", "status": "ready"},
                {"id": "2", "name": "p2", "status": "pending", "unknown_field": "ignored"},
            ],
        }
        resp = ProcessingListResponse.from_dict(data)
        assert resp.total == 2
        assert len(resp.items) == 2
        assert resp.items[0].name == "p1"
        assert resp.items[1].status == "pending"

    def test_prompt_detail_parses_nested(self):
        from mapflow.schema.sam import PromptDetailResponse
        data = {
            "id": "p1",
            "text_prompt": "find trees",
            "spatial_prompts": [
                {"id": "pp1", "processing_id": "proc-1", "geometry_type": "point", "positive": True,
                 "geometry": {"type": "Point", "coordinates": [0, 0]}},
            ],
        }
        resp = PromptDetailResponse.from_dict(data)
        assert len(resp.spatial_prompts) == 1
        assert resp.spatial_prompts[0].positive is True
        assert resp.spatial_prompts[0].geometry_type == "point"

    def test_session_response_parses_inferences(self):
        from mapflow.schema.sam import SessionResponse
        data = {
            "id": "s1", "processing_id": "p1", "prompt_id": "pr1",
            "inferences": [{"id": "i1", "status": "done"}],
            "layer_id": "l1", "tile_url": "https://tiles",
        }
        resp = SessionResponse.from_dict(data)
        assert len(resp.inferences) == 1
        assert resp.inferences[0].status == "done"

    def test_serializable_skips_none(self):
        request = PromptCreateRequest()
        body = request.as_dict()
        assert body == {}

    def test_serializable_includes_values(self):
        request = PointPromptRequest(
            processing_id="p1",
            geometry={"type": "Point", "coordinates": [1, 2]},
            positive=True,
        )
        body = request.as_dict()
        assert body["processing_id"] == "p1"
        assert body["positive"] is True

    def test_parse_confidence_threshold_accepts_blank(self):
        value, error = parse_confidence_threshold("")

        assert value is None
        assert error is None

    def test_parse_confidence_threshold_accepts_value(self):
        value, error = parse_confidence_threshold("0.4")

        assert value == 0.4
        assert error is None

    def test_parse_confidence_threshold_rejects_out_of_range_value(self):
        value, error = parse_confidence_threshold("1.5")

        assert value is None
        assert error == "Confidence threshold must be between 0 and 1."

    def test_inference_response_parses_all_fields(self):
        from mapflow.schema.sam import InferenceResponse
        data = {
            "id": "inf1", "session_id": "s1", "status": "done",
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
            "we_workflow_id": 42, "we_workflow_status": "completed",
            "created_at": "2025-01-01", "updated_at": "2025-01-02",
        }
        resp = InferenceResponse.from_dict(data)
        assert resp.id == "inf1"
        assert resp.status == "done"
        assert resp.we_workflow_id == 42
        assert resp.geometry is not None

    def test_inference_response_defaults(self):
        from mapflow.schema.sam import InferenceResponse
        resp = InferenceResponse.from_dict({"id": "inf1", "session_id": "s1", "status": "pending"})
        assert resp.geometry is None
        assert resp.we_workflow_id is None
        assert resp.we_workflow_status is None

    def test_result_response_parses(self):
        from mapflow.schema.sam import ResultResponse
        data = {
            "id": "r1", "geometry": {"type": "Point", "coordinates": [1, 2]},
            "layer_id": "l1", "processing_id": "p1", "session_id": "s1",
        }
        resp = ResultResponse.from_dict(data)
        assert resp.id == "r1"
        assert resp.layer_id == "l1"

    def test_session_response_accepts_camelcase_text_prompt(self):
        from mapflow.schema.sam import SessionResponse

        data = {
            "id": "s1",
            "processing_id": "p1",
            "name": "session-name",
            "textPrompt": "detect roads",
            "inferences": [],
        }
        resp = SessionResponse.from_dict(data)

        assert resp.text_prompt == "detect roads"

    def test_prompt_response_name_defaults_to_text_prompt(self):
        from mapflow.schema.sam import PromptResponse

        data = {
            "id": "pr1",
            "text_prompt": "find trees",
        }
        resp = PromptResponse.from_dict(data)

        assert resp.name == "find trees"

    def test_prompt_response_name_preserved_when_present(self):
        from mapflow.schema.sam import PromptResponse

        data = {
            "id": "pr1",
            "name": "Prompt A",
            "text_prompt": "find trees",
        }
        resp = PromptResponse.from_dict(data)

        assert resp.name == "Prompt A"

    def test_result_response_defaults(self):
        from mapflow.schema.sam import ResultResponse
        resp = ResultResponse.from_dict({"id": "r1"})
        assert resp.geometry is None
        assert resp.layer_id is None

    def test_session_list_response_parses(self):
        from mapflow.schema.sam import SessionListResponse
        data = {
            "total": 1, "limit": 20, "offset": 0,
            "items": [
                {"id": "s1", "processing_id": "p1", "prompt_id": "pr1",
                 "inferences": [], "layer_id": "l1", "tile_url": "https://tiles"},
            ],
        }
        resp = SessionListResponse.from_dict(data)
        assert resp.total == 1
        assert len(resp.items) == 1
        assert resp.items[0].id == "s1"

    def test_session_response_empty_inferences(self):
        from mapflow.schema.sam import SessionResponse
        resp = SessionResponse.from_dict({"id": "s1", "processing_id": "p1", "prompt_id": "pr1"})
        assert resp.inferences == []


# ---------------------------------------------------------------------------
# _geojson_to_wkt tests
# ---------------------------------------------------------------------------

class TestGeojsonToWkt:
    def test_point(self):
        from mapflow.functional.view.sam_view import _geojson_to_wkt
        geojson = {"type": "Point", "coordinates": [37.6, 55.7]}
        assert _geojson_to_wkt(geojson) == "POINT(37.6 55.7)"

    def test_polygon(self):
        from mapflow.functional.view.sam_view import _geojson_to_wkt
        geojson = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
        }
        result = _geojson_to_wkt(geojson)
        assert result == "POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))"

    def test_polygon_with_hole(self):
        from mapflow.functional.view.sam_view import _geojson_to_wkt
        geojson = {
            "type": "Polygon",
            "coordinates": [
                [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]],
                [[2, 2], [8, 2], [8, 8], [2, 8], [2, 2]],
            ],
        }
        result = _geojson_to_wkt(geojson)
        assert "POLYGON(" in result
        assert result.count("(") == 3  # POLYGON( + 2 rings

    def test_unknown_type_returns_empty(self):
        from mapflow.functional.view.sam_view import _geojson_to_wkt
        assert _geojson_to_wkt({"type": "LineString", "coordinates": [[0, 0], [1, 1]]}) == ""
        assert _geojson_to_wkt({}) == ""
