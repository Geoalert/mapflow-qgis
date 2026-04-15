import json
from unittest.mock import MagicMock

from mapflow.functional.api.processing_api import ProcessingApi
from mapflow.schema.processing import (
    CreateProcessingTemplateSchema,
    UpdateProcessingTemplateSchema,
    RunTemplateProcessingSchema,
    ProcessingTemplateDTO,
    ProcessingTemplateDetails,
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

    def test_create_template_serialization(self):
        body = CreateProcessingTemplateSchema(
            name="T1",
            searchParams={"aoi": {"type": "Polygon"}},
            processingParams={"wdId": "wf-1"},
            projectId="3fa85f64-5717-4562-b3fc-2c963f66afa6",
            activeUntil="2026-05-06T11:03:37.743Z",
        )
        data = json.loads(body.as_json())
        assert data["name"] == "T1"
        assert data["projectId"] == "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    def test_template_table_mapping(self):
        dto = ProcessingTemplateDTO.from_dict(_template_payload())
        table_row = dto.as_processing_table_dict()
        assert table_row["workflowDef"] == "Template"
        assert table_row["status"] == "READY"
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
            processingParams={"wdId": "wf-1"},
            projectId="p-1",
            activeUntil="2026-05-06T11:03:37.743Z",
        )

        self.api.create_template(data=body, callback=callback, error_handler=error_handler)

        self.http.post.assert_called_once()
        kwargs = self.http.post.call_args.kwargs
        assert kwargs["path"] == "processings/template"
        assert json.loads(kwargs["body"].decode())["name"] == "T1"

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
            wdName="Model",
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
