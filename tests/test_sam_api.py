"""Tests for SAM Interactive API client.

All HTTP calls are mocked — these tests verify that SamApi methods
call the correct Http method with the expected URL and body.
"""
import json

from mapflow.functional.api.sam_api import SamApi
from mapflow.schema.sam import (
    ProcessingCreateRequest,
    PromptCreateRequest,
    PromptCopyRequest,
    PromptUpdateRequest,
    PointPromptRequest,
    BboxPromptRequest,
    SessionInferenceCreateRequest,
    SessionNameUpdateRequest,
    InferenceCreateRequest,
    MergeStrategy,
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


class TestCopyPrompt:
    def test_calls_post_to_copy_endpoint(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        request = PromptCopyRequest(name="renamed", text_prompt="find barns")
        api.copy_prompt("prompt-42", request, callback=_noop)

        http_mock.post.assert_called_once()
        call_kwargs = http_mock.post.call_args[1]
        assert call_kwargs["url"] == f"{SERVER}/prompts/prompt-42/copy"
        body = json.loads(call_kwargs["body"].decode())
        assert body == {"name": "renamed", "text_prompt": "find barns"}

    def test_empty_request_serializes_to_empty_object(self, http_mock):
        # Both fields optional → backend applies copy defaults
        # (auto-suffixed name, FK reuse for text_prompt).
        api = SamApi(http=http_mock, server=SERVER)
        api.copy_prompt("prompt-42", PromptCopyRequest(), callback=_noop)

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

class TestGetSession:
    def test_calls_get(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.get_session("sess-1", callback=_noop)

        url = http_mock.get.call_args[1]["url"]
        assert url == f"{SERVER}/sessions/sess-1"


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
            processing_id="proc-1",
            prompt_id="prompt-1",
            geometry={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
            confidence_threshold=0.8,
            merge_strategy=MergeStrategy.NONE,
        )
        api.create_inference(request, callback=_noop)

        call_kwargs = http_mock.post.call_args[1]
        assert call_kwargs["url"] == f"{SERVER}/inference"
        body = json.loads(call_kwargs["body"].decode())
        assert body["processing_id"] == "proc-1"
        assert body["prompt_id"] == "prompt-1"
        assert "workflow_id" not in body
        assert body["confidence_threshold"] == 0.8
        assert body["merge_strategy"] == MergeStrategy.NONE.value


class TestCreateSessionInference:
    def test_calls_post_with_merge_strategy(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        request = SessionInferenceCreateRequest(
            geometry={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
            merge_strategy=MergeStrategy.INSTANCE_SEGMENTATION,
        )
        api.create_session_inference("sess-1", request, callback=_noop)

        call_kwargs = http_mock.post.call_args[1]
        assert call_kwargs["url"] == f"{SERVER}/sessions/sess-1/inferences"
        body = json.loads(call_kwargs["body"].decode())
        assert body["merge_strategy"] == MergeStrategy.INSTANCE_SEGMENTATION.value

    def test_calls_post_without_confidence_threshold_or_merge_strategy(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        request = SessionInferenceCreateRequest(
            geometry={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
        )
        api.create_session_inference("sess-1", request, callback=_noop)

        call_kwargs = http_mock.post.call_args[1]
        assert call_kwargs["url"] == f"{SERVER}/sessions/sess-1/inferences"
        body = json.loads(call_kwargs["body"].decode())
        assert "workflow_id" not in body
        assert "confidence_threshold" not in body
        assert "merge_strategy" not in body


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
# Spatial prompt raster preview download
# ---------------------------------------------------------------------------

class TestDownloadSpatialPromptRaster:
    def test_joins_relative_path_with_sam_base(self, http_mock):
        # `raster_url` arrives rooted at /sam-interactive (no server, no
        # /rest/sam-interactive prefix). SamApi must concatenate it with
        # `self.server` and not rewrite the prefix — the prefix encodes
        # the auth path (session-rooted vs prompt-rooted).
        api = SamApi(http=http_mock, server=SERVER)
        api.download_spatial_prompt_raster(
            raster_url="/sessions/sess-1/spatial_prompts/sp-42/raster",
            callback=_noop,
        )

        http_mock.get.assert_called_once()
        kwargs = http_mock.get.call_args[1]
        assert kwargs["url"] == (
            f"{SERVER}/sam-interactive"
            "/sessions/sess-1/spatial_prompts/sp-42/raster"
        )

    def test_preserves_prompt_rooted_path(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.download_spatial_prompt_raster(
            raster_url="/prompts/prm-7/spatial_prompts/sp-9/raster",
            callback=_noop,
        )

        url = http_mock.get.call_args[1]["url"]
        # Same join, different rooting prefix; we never rewrite which
        # parent owns the access check.
        assert url == (
            f"{SERVER}/sam-interactive"
            "/prompts/prm-7/spatial_prompts/sp-9/raster"
        )

    def test_forwards_callback_kwargs(self, http_mock):
        api = SamApi(http=http_mock, server=SERVER)
        api.download_spatial_prompt_raster(
            raster_url="/sessions/s/spatial_prompts/p/raster",
            callback=_noop,
            callback_kwargs={"sp_id": "sp-1", "geometry_type": "point"},
        )

        kwargs = http_mock.get.call_args[1]
        assert kwargs["callback_kwargs"] == {
            "sp_id": "sp-1",
            "geometry_type": "point",
        }


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestSchemas:
    def test_processing_list_response_parses_items(self):
        from mapflow.schema.sam import ProcessingListResponse
        data = {
            "has_more": True, "limit": 20, "offset": 0,
            "items": [
                {"id": "1", "name": "p1", "status": "ready"},
                {"id": "2", "name": "p2", "status": "pending", "unknown_field": "ignored"},
            ],
        }
        resp = ProcessingListResponse.from_dict(data)
        assert resp.has_more is True
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
            "confidence_threshold": 0.65,
            "inferences": [{"id": "i1", "status": "done"}],
            "layer_id": "l1", "tile_url": "https://tiles",
        }
        resp = SessionResponse.from_dict(data)
        assert len(resp.inferences) == 1
        assert resp.inferences[0].status == "done"
        assert resp.confidence_threshold == 0.65

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

    def test_session_response_parses_inference_summaries(self):
        from mapflow.schema.sam import SessionResponse, InferenceStatusSummary

        data = {
            "id": "s1",
            "processing_id": "p1",
            "name": "session-name",
            "confidence_threshold": 0.5,
            "inferences": [
                {"id": "inf1", "status": "in_progress",
                 "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
                 "created_at": "2026-04-01T10:00:00"},
                {"id": "inf2", "status": "done", "created_at": "2026-04-01T10:01:00"},
            ],
            "vector_layer": {
                "id": "vl1",
                "tile_url": "https://tiles/{z}/{x}/{y}",
                "tile_json_url": "https://tiles/tile.json",
            },
        }
        resp = SessionResponse.from_dict(data)

        assert len(resp.inferences) == 2
        assert all(isinstance(i, InferenceStatusSummary) for i in resp.inferences)
        assert resp.inferences[0].id == "inf1"
        assert resp.inferences[0].status == "in_progress"
        assert resp.inferences[0].geometry is not None
        assert resp.inferences[0].created_at == "2026-04-01T10:00:00"
        assert resp.inferences[1].geometry is None
        assert resp.vector_layer is not None
        assert resp.vector_layer.tile_url == "https://tiles/{z}/{x}/{y}"

    def test_session_response_parses_embedded_prompt_snapshot(self):
        # Post-A4 shape: text_prompt + spatial_prompts ride directly on the
        # session response, retiring the separate /sessions/{id}/prompts call.
        from mapflow.schema.sam import (
            SessionResponse, TextPromptSummary, SpatialPromptResponse,
        )

        data = {
            "id": "s1",
            "processing_id": "p1",
            "text_prompt": {"id": "tp1", "text": "find trees"},
            "spatial_prompts": [
                {"id": "sp1", "geometry_type": "point", "processing_id": "p1",
                 "geometry": {"type": "Point", "coordinates": [37.6, 55.7]},
                 "positive": True},
            ],
            "inferences": [],
        }
        resp = SessionResponse.from_dict(data)

        assert isinstance(resp.text_prompt, TextPromptSummary)
        assert resp.text_prompt.text == "find trees"
        assert len(resp.spatial_prompts) == 1
        assert isinstance(resp.spatial_prompts[0], SpatialPromptResponse)
        assert resp.spatial_prompts[0].geometry_type == "point"

    def test_session_list_item_carries_progress_aggregates(self):
        # Post-A2 shape: SessionListItem exposes inferences_total / done so
        # the sessions list table can show progress without per-row drill-in.
        from mapflow.schema.sam import SessionListResponse

        data = {
            "total": 1, "limit": 20, "offset": 0,
            "items": [
                {"id": "s1", "processing_id": "p1", "name": "sess",
                 "inferences_total": 5, "inferences_done": 2},
            ],
        }
        resp = SessionListResponse.from_dict(data)

        assert resp.items[0].inferences_total == 5
        assert resp.items[0].inferences_done == 2

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

    def test_session_list_response_parses(self):
        from mapflow.schema.sam import SessionListResponse
        data = {
            "total": 1, "limit": 20, "offset": 0,
            "items": [
                {"id": "s1", "processing_id": "p1", "inferences": []},
            ],
        }
        resp = SessionListResponse.from_dict(data)
        assert resp.total == 1
        assert len(resp.items) == 1
        assert resp.items[0].id == "s1"

    def test_session_response_empty_inferences(self):
        from mapflow.schema.sam import SessionResponse
        resp = SessionResponse.from_dict({"id": "s1", "processing_id": "p1"})
        assert resp.inferences == []
        assert resp.vector_layer is None


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
