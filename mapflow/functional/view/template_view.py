from typing import List, Optional

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox

from ...dialogs.icons import new_image_icon
from ...dialogs.main_dialog import MainDialog


class TemplateView(QObject):
    """Template-specific widget reads/writes on the panel: the search/plan name field, the
    Search button's busy state, the "select a project" reminder in the problems label, the
    too-large-AOI "Plan Search?" prompt, and the seen-image markers / status cells across the
    metadata-results and processings tables.

    Holds no service (`spec/007_architecture.md` § Layer rules). `TemplateController` reads from
    here, calls `TemplateService`, and pushes effects back.
    """

    def __init__(self, dlg: MainDialog, iface, config):
        super().__init__()
        self.dlg = dlg
        self.iface = iface
        self.config = config

    def template_name(self) -> str:
        return self.dlg.processingName.text().strip()

    def set_search_enabled(self, enabled: bool) -> None:
        """The 'Search / Plan search' button — disabled while a create request is in flight."""
        self.dlg.getMetadata.setEnabled(enabled)

    def set_update_template_visible(self, visible: bool) -> None:
        """The 'Update template' button. It sits on the search tab but is the template's own
        control — saving the current filters into the open template only means anything while one
        is open, so it is shown on enter and hidden on leave."""
        self.dlg.updateTemplateSearch.setVisible(visible)

    def show_project_required(self, message: str) -> None:
        self.dlg.processingProblemsLabel.setPalette(self.dlg.alert_palette)
        self.dlg.processingProblemsLabel.setText(message)

    def clear_project_required(self, message: str) -> None:
        """Clear the label only if it currently shows *our* message — never the cost or another
        reason."""
        if self.dlg.processingProblemsLabel.text() == message:
            self.dlg.processingProblemsLabel.clear()

    def prompt_plan_search(self, plugin_name: str) -> bool:
        """Offer a Planned Search when the AOI is too large for an immediate one (T8). Returns
        True when the user chooses to plan it."""
        box = QMessageBox(
            QMessageBox.Question,
            plugin_name,
            self.tr("The search area is too large for immediate processing. The Planned Search "
                    "will be created and run in the background. You will be notified when "
                    "results are available."),
            parent=self.iface.mainWindow(),
        )
        box.addButton(QMessageBox.Cancel)
        plan_button = box.addButton(self.tr("Plan Search"), QMessageBox.AcceptRole)
        box.setDefaultButton(plan_button)
        box.exec()
        return box.clickedButton() is plan_button

    # ---------- seen markers on the metadata-results table ----------

    def selected_metadata_rows(self) -> List[int]:
        return sorted({item.row() for item in self.dlg.metadataTable.selectedItems()})

    def metadata_row_count(self) -> int:
        return self.dlg.metadataTable.rowCount()

    def image_id_at(self, row: int) -> Optional[str]:
        id_item = self.dlg.metadataTable.item(row, self.config.SEARCH_ID_COLUMN_INDEX)
        return id_item.text() if id_item else None

    def _new_image_marker_column(self) -> int:
        """Leftmost visible column — where the 'new image' icon shows. Skips columns the user hid
        via the search-column checkboxes, so the marker never lands on a hidden column."""
        start = self.config.NEW_IMAGE_MARKER_COLUMN_INDEX
        table = self.dlg.metadataTable
        for col in range(start, table.columnCount()):
            if not table.isColumnHidden(col):
                return col
        return start

    def set_new_image_marker(self, row: int, is_new: bool) -> None:
        cell = self.dlg.metadataTable.item(row, self._new_image_marker_column())
        if cell is not None:
            cell.setIcon(new_image_icon if is_new else QIcon())

    # ---------- template status cell on the processings table ----------

    def refresh_template_status_cell(self, template) -> None:
        """Update a template's status cell text + tooltip in the processings table."""
        id_col = self.config.PROCESSING_TABLE_ID_COLUMN_INDEX
        status_col = list(self.config.PROCESSING_TABLE_COLUMNS).index('status')
        table = self.dlg.processingsTable
        for row in range(table.rowCount()):
            id_item = table.item(row, id_col)
            if id_item and id_item.text() == str(template.id):
                status_item = table.item(row, status_col)
                if status_item:
                    status_item.setData(Qt.DisplayRole, template.table_status)
                    tip = self.tr("Planned processing")
                    if template.newImagesCount and template.newImagesCount > 0:
                        tip = self.tr("Planned processing. New images: {count}").format(
                            count=template.newImagesCount)
                    status_item.setToolTip(tip)
                break
