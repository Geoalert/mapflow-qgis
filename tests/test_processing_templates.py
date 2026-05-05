import json
from unittest.mock import MagicMock

import pytest

from mapflow.functional.api.processing_api import ProcessingApi
from mapflow.schema.processing import (
    CreateProcessingTemplateSchema,
    UpdateProcessingTemplateSchema,
    RunTemplateProcessingSchema,
    ProcessingTemplateDTO,
    ProcessingTemplateDetails,
    SearchParams,
)


def _template_payload(template_id: str = "3fa85f64-5717-4562-b3fc-2c963f66afa6"):
    return {
        "id": template_id,
        "name": "Template A",
        "status": "READY",
        "createdAt": "2025-09-26T06:25:55.820336Z",
        "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "searchParams": {
            "aoiDetails": {"type": "FeatureCollection", "features": []},
            "acquisitionDateFrom": "2022-04-06T07:34:43.637Z",
            "acquisitionDateTo": "2025-09-24T07:34:43.637Z",
            "maxCloudCover": 50.0,
            "hideUnavailable": True,
            "dataProviders": ["arcgis_world_imagery"],
            "productTypes": ["IMAGE"]
        },
        "processingParams": None,
        "lastCheckedAt": None,
        "activeUntil": "2026-03-15T17:00:00Z",
        "projectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "newImagesCount": 4,
        "isActive": False,
        "isArchived": False,
        "maxAoiIntersectionPercent": 85.5,
    }


class TestTemplateSchemas:
    def test_template_dto_from_dict(self):
        dto = ProcessingTemplateDTO.from_dict(_template_payload())
        assert dto.name == "Template A"
        assert dto.status == "READY"
        assert dto.newImagesCount == 4
        assert dto.isArchived is False
        assert dto.maxAoiIntersectionPercent == 85.5

    def test_template_details_from_dict(self):
        details = ProcessingTemplateDetails.from_dict({
            "template": _template_payload(),
        })
        assert details.template.name == "Template A"
        assert details.template.status == "READY"

    def test_template_aoi_features_from_plain_aoi(self):
        payload = _template_payload()
        payload["searchParams"] = {
            "aoi": {
                "type": "Polygon",
                "coordinates": [[[13.0, 52.0], [14.0, 52.0], [14.0, 51.0], [13.0, 51.0], [13.0, 52.0]]],
            }
        }
        dto = ProcessingTemplateDTO.from_dict(payload)
        features = dto._aoi_features()
        assert len(features) == 1
        assert features[0]["geometry"]["type"] == "Polygon"

    def test_create_template_serialization(self):
        body = CreateProcessingTemplateSchema(
            name="T1",
            searchParams={
                "aoi": {
                    "type": "Polygon",
                    "coordinates": [[[13.0, 52.0], [14.0, 52.0], [14.0, 51.0], [13.0, 51.0], [13.0, 52.0]]],
                },
                "acquisitionDateFrom": "2022-09-24T17:00:00.000Z",
                "acquisitionDateTo": "2026-09-24T17:00:00.000Z",
                "productTypes": ["MOSAIC", "IMAGE"],
                "hideUnavailable": True,
                "dataProviders": ["arcgis_world_imagery"],
                "maxCloudCover": 43,
                "minAoiIntersectionPercent": 20,
                "minOffNadirAngle": 0,
                "maxOffNadirAngle": 25,
            },
            processingParams=None,
            projectId="3fa85f64-5717-4562-b3fc-2c963f66afa6",
            activeUntil="2026-05-06T11:03:37.743Z",
        )
        data = json.loads(body.as_json())
        assert data["name"] == "T1"
        assert data["projectId"] == "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        assert data["searchParams"]["aoi"]["type"] == "Polygon"
        assert "aoiDetails" not in data["searchParams"]
        assert "processingParams" not in data

    def test_create_template_serialization_with_search_params_schema(self):
        body = CreateProcessingTemplateSchema(
            name="T1",
            searchParams=SearchParams(
                aoi={
                    "type": "Polygon",
                    "coordinates": [[[13.0, 52.0], [14.0, 52.0], [14.0, 51.0], [13.0, 51.0], [13.0, 52.0]]],
                },
                acquisitionDateFrom="2022-09-24T17:00:00.000Z",
                acquisitionDateTo="2026-09-24T17:00:00.000Z",
                productTypes=["MOSAIC", "IMAGE"],
                hideUnavailable=True,
                dataProviders=["arcgis_world_imagery"],
                maxCloudCover=43,
                minAoiIntersectionPercent=20,
                minOffNadirAngle=0,
                maxOffNadirAngle=25,
            ),
            processingParams=None,
            projectId="3fa85f64-5717-4562-b3fc-2c963f66afa6",
            activeUntil="2026-05-06T11:03:37.743Z",
        )
        data = json.loads(body.as_json())
        assert data["searchParams"]["aoi"]["type"] == "Polygon"
        assert "aoiDetails" not in data["searchParams"]
        assert "processingParams" not in data

    @pytest.mark.parametrize(
        ("payload_updates", "expected_status"),
        [
            ({"status": "FAILED", "isActive": False}, "Failed"),
            ({"status": "READY", "isActive": False}, "Inactive"),
            ({"status": "READY", "isActive": True, "lastCheckedAt": None, "newImagesCount": 0}, "Created"),
            ({
                "status": "READY",
                "isActive": True,
                "lastCheckedAt": None,
                "newImagesCount": 3,
            }, "Created (3)"),
            ({
                "status": "READY",
                "isActive": True,
                "lastCheckedAt": "2026-03-10T17:00:00Z",
                "newImagesCount": 4,
            }, "Updated (4)"),
            ({
                "status": "READY",
                "isActive": True,
                "lastCheckedAt": "2026-03-10T17:00:00Z",
                "newImagesCount": 0,
            }, "Updated"),
        ],
    )
    def test_template_table_mapping(self, payload_updates, expected_status):
        dto = ProcessingTemplateDTO.from_dict({**_template_payload(), **payload_updates})
        table_row = dto.as_processing_table_dict()
        assert table_row["workflowDef"] == "Planned"
        assert table_row["status"] == expected_status
        assert table_row["aoiArea"] is None


class TestTemplateApi:
    def setup_method(self):
        self.http = MagicMock()
        self.api = ProcessingApi(http=self.http, dlg=MagicMock(), iface=MagicMock(), result_loader=MagicMock())

    def test_get_templates_path(self):
        callback = MagicMock()
        self.api.get_templates(callback=callback)
        self.http.get.assert_called_once()
        assert self.http.get.call_args.kwargs["path"] == "processings/template"

    def test_get_template_by_id_path(self):
        callback = MagicMock()
        self.api.get_template(template_id="tpl-1", callback=callback)
        assert self.http.get.call_args.kwargs["path"] == "processings/template/tpl-1"

    def test_create_template_body(self):
        callback = MagicMock()
        error_handler = MagicMock()
        body = CreateProcessingTemplateSchema(
            name="T1",
            searchParams={"aoi": {}},
            processingParams=None,
            projectId="p-1",
            activeUntil="2026-05-06T11:03:37.743Z",
        )

        self.api.create_template(data=body, callback=callback, error_handler=error_handler)

        self.http.post.assert_called_once()
        kwargs = self.http.post.call_args.kwargs
        assert kwargs["path"] == "processings/template"
        payload = json.loads(kwargs["body"].decode())
        assert payload["name"] == "T1"
        assert payload["searchParams"] == {"aoi": {}}
        assert "processingParams" not in payload

    def test_update_template_path(self):
        callback = MagicMock()
        body = UpdateProcessingTemplateSchema(
            name="T1",
            searchParams={"aoi": {}},
            processingParams={"wdId": "wf-1"},
            activeUntil="2026-05-06T11:03:37.743Z",
        )

        self.api.update_template(template_id="tpl-2", data=body, callback=callback)

        self.http.put.assert_called_once()
        assert self.http.put.call_args.kwargs["path"] == "processings/template/tpl-2"

    def test_run_template_v2_path(self):
        callback = MagicMock()
        error_handler = MagicMock()
        body = RunTemplateProcessingSchema(
            name="Run 1",
            description=None,
            wdName=None,
            wdId="wf-1",
            geometry={"type": "Polygon", "coordinates": []},
            params={},
            meta={},
            blocks=[],
            updateTemplateGeometry=True,
        )

        self.api.run_template_processing(
            template_id="tpl-3",
            data=body,
            callback=callback,
            error_handler=error_handler,
        )

        self.http.post.assert_called_once()
        assert self.http.post.call_args.kwargs["path"] == "processings/template/tpl-3/v2"
