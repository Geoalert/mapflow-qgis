"""SAM Interactive tab view — UI state management.

Handles display of processings table, workflows, and debug output.
No business logic or API calls.
"""
import json
from typing import List, Optional

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView

from ...dialogs.main_dialog import MainDialog
from ...schema.sam import (
    ProcessingSummaryResponse,
    ProcessingDetailResponse,
    WorkflowSummaryResponse,
)


class SamView(QObject):
    def __init__(self, dlg: MainDialog):
        super().__init__()
        self.dlg = dlg
        self._setup_processings_table()

    def _setup_processings_table(self):
        table = self.dlg.samProcessingsTable
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "Name", "Status", "Created"])
        table.setColumnHidden(0, True)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def display_processings(self, items: List[ProcessingSummaryResponse]):
        table = self.dlg.samProcessingsTable
        table.setRowCount(len(items))
        for row, proc in enumerate(items):
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, proc.id)
            table.setItem(row, 0, id_item)

            name_item = QTableWidgetItem()
            name_item.setData(Qt.DisplayRole, proc.name)
            table.setItem(row, 1, name_item)

            status_item = QTableWidgetItem()
            status_item.setData(Qt.DisplayRole, proc.status)
            table.setItem(row, 2, status_item)

            created_item = QTableWidgetItem()
            created_item.setData(Qt.DisplayRole, proc.created_at or "")
            table.setItem(row, 3, created_item)

    def selected_processing_id(self) -> Optional[str]:
        table = self.dlg.samProcessingsTable
        selected = table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        item = table.item(row, 0)
        return item.data(Qt.DisplayRole) if item else None

    def display_processing_detail(self, detail: ProcessingDetailResponse):
        pass

    def display_workflows(self, workflows: List[WorkflowSummaryResponse]):
        pass

    def append_debug(self, title: str, data):
        try:
            debug_text = json.dumps(data, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            debug_text = str(data)
        self.dlg.samDebugOutput.append(f"--- {title} ---\n{debug_text}\n")

    def update_pagination_buttons(self, has_prev: bool, has_next: bool,
                                  offset: int, limit: int, total: int):
        pass
