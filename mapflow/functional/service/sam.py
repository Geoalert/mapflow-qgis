"""SAM Interactive service — business logic for the SAM tab.

Coordinates SamApi (HTTP calls) and SamView (UI state).
Manages pagination state and response parsing.
"""
import json
from typing import Optional

from PyQt5.QtCore import QObject
from PyQt5.QtNetwork import QNetworkReply

from ..api.sam_api import SamApi
from ..view.sam_view import SamView
from ...dialogs.main_dialog import MainDialog
from ...schema.sam import (
    ProcessingListResponse,
    ProcessingDetailResponse,
    WorkflowSummaryResponse,
)


class SamService(QObject):
    def __init__(self, dlg: MainDialog, sam_api: SamApi):
        super().__init__()
        self.dlg = dlg
        self.api = sam_api
        self.view = SamView(dlg)

        # Pagination state for processings list
        self._offset = 0
        self._limit = 20
        self._total = 0

    # ------------------------------------------------------------------
    # Processings
    # ------------------------------------------------------------------

    def list_processings(self, filter_: Optional[str] = None):
        self.api.list_processings(
            callback=self.list_processings_callback,
            filter_=filter_,
            limit=self._limit,
            offset=self._offset,
        )

    def list_processings_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        result = ProcessingListResponse.from_dict(data)
        self._total = result.total
        self.view.display_processings(result.items)
        self.view.append_debug("List Processings", data)
        self.view.update_pagination_buttons(
            self.has_prev_page, self.has_next_page,
            self._offset, self._limit, self._total,
        )

    def get_processing(self, processing_id: str):
        self.api.get_processing(
            processing_id=processing_id,
            callback=self.get_processing_callback,
        )

    def get_processing_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        detail = ProcessingDetailResponse.from_dict(data)
        self.view.display_processing_detail(detail)
        self.view.append_debug("Processing Detail", data)

    # ------------------------------------------------------------------
    # Workflows
    # ------------------------------------------------------------------

    def list_workflows(self, processing_id: str):
        self.api.get_processing_workflows(
            processing_id=processing_id,
            callback=self.list_workflows_callback,
        )

    def list_workflows_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        workflows = [WorkflowSummaryResponse.from_dict(w) for w in data]
        self.view.display_workflows(workflows)
        self.view.append_debug("Workflows", data)

    def get_workflow(self, workflow_id: str):
        self.api.get_workflow(
            workflow_id=workflow_id,
            callback=self.get_workflow_callback,
        )

    def get_workflow_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        self.view.append_debug("Workflow Detail", data)

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    @property
    def has_next_page(self) -> bool:
        return self._offset + self._limit < self._total

    @property
    def has_prev_page(self) -> bool:
        return self._offset > 0

    def next_page(self):
        if self.has_next_page:
            self._offset += self._limit
            self.list_processings()

    def prev_page(self):
        if self.has_prev_page:
            self._offset = max(0, self._offset - self._limit)
            self.list_processings()
