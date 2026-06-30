from typing import List, Union
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtWidgets import QAbstractItemView, QTableWidgetItem, QMessageBox, QCheckBox, QMenu
from PyQt5.QtGui import QColor
from ...dialogs.main_dialog import MainDialog
from ...dialogs import icons
from ...schema.processing import (ProcessingDTO, ProcessingTemplateDTO, TemplateAoiDTO,
                                  AoiProcessingLink, TemplateProcessingSchema,
                                  NoAoiProcessingsRow,
                                  ProcessingUIParams, ProcessingSortBy, ProcessingSortOrder)
from ...config import config
from ..service.alert_service import alert

class ProcessingView:
    """
    This class incorporates everything we take responsible for the processing start and cost update

    - readings from the UI elements
    - some checks on the correspondence of UI controls
    - changes in the UI with the processing start(?)
    - display of the finished processings in the table (not yet?)
    """
    def __init__(self, dlg: MainDialog):
        self.dlg = dlg
        self._header_sort_by = None   # column-based override; None = use combo
        self._header_sort_desc = True
        # Setup pagination icons
        self.dlg.processingsPreviousPageButton.setIcon(icons.arrow_left_icon)
        self.dlg.processingsNextPageButton.setIcon(icons.arrow_right_icon)
        # Hide pagination controls initially
        self.dlg.processingsPreviousPageButton.setVisible(False)
        self.dlg.processingsNextPageButton.setVisible(False)
        self.dlg.processingsPageLabel.setVisible(False)
        # Setup sort combo
        self.dlg.sortProcessingsCombo.addItems([
            self.tr("Newest first"),
            self.tr("Oldest first"),
            self.tr("A-Z"),
            self.tr("Z-A"),
            self.tr("Status A-Z"),
            self.tr("Status Z-A"),
        ])
        self.dlg.sortProcessingsCombo.setCurrentIndex(0)
        self.dlg.filterProcessings.setPlaceholderText(self.tr("Filter processings"))

    # Column index -> sort_by value mapping
    _COLUMN_SORT_MAP = {
        0: "NAME",           # name
        1: "WORKFLOW",       # workflowDef
        2: "STATUS",         # status
        3: "PROGRESS",       # percentCompleted
        4: "AREA",           # aoiArea
        5: "COST",           # cost
        6: "CREATED",        # created
        7: "REVIEW_UNTIL",   # reviewUntil
    }

    def connect_header_sort(self, on_sort_changed):
        """Connect column header clicks to a templates-first re-sort."""
        self.dlg.processingsTable.horizontalHeader().sectionClicked.connect(
            lambda col: self._on_header_clicked(col, on_sort_changed)
        )

    def _on_header_clicked(self, column: int, on_sort_changed):
        sort_by = self._COLUMN_SORT_MAP.get(column)
        if sort_by is None:
            return  # non-sortable column
        if self._header_sort_by == sort_by:
            self._header_sort_desc = not self._header_sort_desc
        else:
            self._header_sort_by = sort_by
            self._header_sort_desc = True
        # Update the visual indicator on the header
        order = Qt.DescendingOrder if self._header_sort_desc else Qt.AscendingOrder
        self.dlg.processingsTable.horizontalHeader().setSortIndicator(column, order)
        on_sort_changed()

    def setup_context_menu(
        self,
        on_open_template_details,
        on_pause_template,
        on_resume_template,
        on_delete_template,
        is_only_templates_selected,
    ):
        """
        Setup context menu for the processings table.
        
        Args:
            on_open_template_details: Callback for opening template details
            on_pause_template: Callback for pause template action
            on_resume_template: Callback for resume template action
            on_delete_template: Callback for delete template action
            is_only_templates_selected: Callback that returns True only for template-only selection
        """
        self.dlg.processingsTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dlg.processingsTable.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(
                pos,
                on_open_template_details,
                on_pause_template,
                on_resume_template,
                on_delete_template,
                is_only_templates_selected,
            )
        )
    
    def _show_context_menu(
        self,
        pos,
        on_open_template_details,
        on_pause_template,
        on_resume_template,
        on_delete_template,
        is_only_templates_selected,
    ):
        """Show context menu for templates."""
        item = self.dlg.processingsTable.itemAt(pos)
        if not item:
            return
        
        row = item.row()
        id_column_index = config.PROCESSING_TABLE_ID_COLUMN_INDEX
        id_item = self.dlg.processingsTable.item(row, id_column_index)
        
        if not id_item:
            return
        
        # Keep selection in sync with right-clicked row.
        selected_rows = {index.row() for index in self.dlg.processingsTable.selectionModel().selectedIndexes()}
        if row not in selected_rows:
            self.dlg.processingsTable.clearSelection()
            self.dlg.processingsTable.selectRow(row)

        if not is_only_templates_selected():
            return

        menu = QMenu(self.dlg.processingsTable)
        menu.addAction(self.tr("Open Details")).triggered.connect(on_open_template_details)
        menu.addSeparator()
        menu.addAction(self.tr("Pause Template")).triggered.connect(on_pause_template)
        menu.addAction(self.tr("Resume Template")).triggered.connect(on_resume_template)
        menu.addSeparator()
        menu.addAction(self.tr("Delete Template")).triggered.connect(on_delete_template)
        menu.exec_(self.dlg.processingsTable.mapToGlobal(pos))

    def tr(self, message: str) -> str:
        """Translate message using QCoreApplication."""
        return QCoreApplication.translate('ProcessingView', message)

    @property
    def processing_name(self):
        # this is a sample function, maybe we'll not need it
        return self.dlg.processingName.text()

    @property
    def processing_name_valid(self):
        # this is a sample function, maybe we'll not need it
        return self.processing_name != ""

    def read_processing_start_params(self):
        return ProcessingUIParams(
            name = self.dlg.processingName.text() or None,
            wd_name = self.dlg.modelCombo.currentText(),
            data_source_index = self.dlg.providerIndex(),
            zoom = int(self.dlg.zoomCombo.currentText()) if self.dlg.zoomCombo.currentIndex() != 0 else None, 
            model_options = [self.dlg.modelOptionsLayout.itemAt(i).widget().text() 
                             for i in range(self.dlg.modelOptionsLayout.count())
                             if isinstance(i, QCheckBox) and
                             self.dlg.modelOptionsLayout.itemAt(i).widget().isChecked()]
        )

    def clear_processing_name(self, name):
        # If the name is expected, we clear it after the processsing is launched;
        # Otherwise it means that the user has altered the text already and it should be preserved
        if self.dlg.processingName.text == name:
            self.dlg.processingName.clear()

    def disable_processing_start(self, reason: str, clear_area: bool):
        self.dlg.disable_processing_start(reason=reason, clear_area=clear_area)

    def create_table_items(self, processing: Union[ProcessingDTO, ProcessingTemplateDTO]):
        table_items = []
        set_color = False
        processing_dict = processing.as_processing_table_dict()
        is_template = isinstance(processing, ProcessingTemplateDTO)
        is_aoi = isinstance(processing, TemplateAoiDTO)
        is_separator = isinstance(processing, NoAoiProcessingsRow)
        # An AOI's processing, whether the lighter aoiDetails link or the full schema.
        is_template_processing = isinstance(processing, (AoiProcessingLink, TemplateProcessingSchema))
        if is_template:
            set_color = True
            color = QColor(207, 242, 249)  # light blue for templates    #! Dark theme?
        elif is_aoi:
            set_color = True
            color = QColor(207, 226, 243)  # blue tint for AOI rows (matches the AOI map layer)
        elif is_template_processing:
            set_color = True
            color = QColor(223, 240, 223)  # green tint for an AOI's processings (matches the map)
        elif is_separator:
            set_color = True
            color = QColor(230, 230, 230)  # neutral grey for the 'No AOI' separator
        elif processing.status.is_ok and processing.review_expires:
            # setting color for close review
            set_color = True
            color = QColor(255, 220, 200)
        for _col, attr in enumerate(config.PROCESSING_TABLE_COLUMNS):
            table_item = QTableWidgetItem()
            table_item.setData(Qt.DisplayRole, processing_dict[attr])
            if is_template:
                template_tip = self.tr("Planned processing")
                if processing.newImagesCount and processing.newImagesCount > 0:
                    template_tip = self.tr("Planned processing. New images: {count}").format(
                        count=processing.newImagesCount
                    )
                table_item.setToolTip(template_tip)
            elif is_aoi:
                aoi_tip = self.tr("Template AOI")
                if processing.hasNewImages:
                    aoi_tip = self.tr("Template AOI with new images")
                table_item.setToolTip(aoi_tip)
            elif is_template_processing:
                table_item.setToolTip(self.tr("Processing from this AOI. Double-click to load results."))
            elif is_separator:
                table_item.setToolTip(self.tr("Processings not intersecting any AOI"))
            elif processing.status.is_failed:
                table_item.setToolTip(processing.error_message(raw=config.SHOW_RAW_ERROR))
            elif processing.reviewUntil:
                table_item.setToolTip(self.tr("Please review or accept this processing until {}."
                                              " Double click to add results"
                                              " to the map").format(
                    processing.reviewUntil.astimezone().strftime('%Y-%m-%d %H:%M') if processing.reviewUntil else ""))
            elif processing.status.is_ok:
                table_item.setToolTip(self.tr("Double click to add results to the map."
                                              ))
            if set_color:
                table_item.setBackground(color)
            table_items.append(table_item)
        return table_items

    def update_processing_table(self, processings: List[Union[ProcessingDTO, ProcessingTemplateDTO]]):
        # UPDATE THE TABLE
        # Memorize the selection to restore it after table update
        selected_processings = self.selected_processing_ids()
        # Explicitly clear selection since resetting row count won't do it
        self.dlg.processingsTable.clearSelection()
        # Temporarily enable multi selection so that selectRow won't clear previous selection
        self.dlg.processingsTable.setSelectionMode(QAbstractItemView.MultiSelection)
        # Row insertion triggers sorting -> row indexes shift -> duplicate rows, so turn sorting off
        self.dlg.processingsTable.setSortingEnabled(False)
        self.dlg.processingsTable.setRowCount(len(processings))
        # Fill out the table
        for row, proc in enumerate(processings):
            table_items = self.create_table_items(processing=proc)
            for col, item in enumerate(table_items):
                self.dlg.processingsTable.setItem(row, col, item)
            if proc.id in selected_processings:
                self.dlg.processingsTable.selectRow(row)
        # Keep Qt sorting disabled — row order is set by combined_processing_rows (templates first).
        # Re-show sort indicator if a header sort is active (setSortingEnabled(False) hides it)
        if self._header_sort_by is not None:
            col = next(c for c, s in self._COLUMN_SORT_MAP.items() if s == self._header_sort_by)
            order = Qt.DescendingOrder if self._header_sort_desc else Qt.AscendingOrder
            header = self.dlg.processingsTable.horizontalHeader()
            header.setSortIndicatorShown(True)
            header.setSortIndicator(col, order)
        # Restore extended selection and filtering
        self.dlg.processingsTable.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def add_new_processing(self, processing: ProcessingDTO):
        self.dlg.processingsTable.insertRow(0)
        table_items = self.create_table_items(processing=processing)
        for col, item in enumerate(table_items):
            self.dlg.processingsTable.setItem(0, col, item)

    def update_processing_name(self, processing_id: str, new_name: str) -> bool:
        """
        Update the name of a processing in the table by finding its row using processing ID.
        
        Args:
            processing_id: The ID of the processing to update
            new_name: The new name to set
            
        Returns:
            bool: True if the processing was found and updated, False otherwise
        """
        table = self.dlg.processingsTable
        id_column_index = config.PROCESSING_TABLE_ID_COLUMN_INDEX
        name_column_index = config.PROCESSING_TABLE_COLUMNS.index('name')
        
        # Find items with matching processing ID in the ID column
        id_items = table.findItems(str(processing_id), Qt.MatchExactly)
        
        # Filter to only items in the ID column (in case ID appears in other columns)
        for item in id_items:
            if item.column() == id_column_index:
                # Get the name item in the same row and update it
                name_item = table.item(item.row(), name_column_index)
                if name_item:
                    name_item.setData(Qt.DisplayRole, new_name)
                else:
                    # Create new name item if it doesn't exist
                    name_item = QTableWidgetItem()
                    name_item.setData(Qt.DisplayRole, new_name)
                    table.setItem(item.row(), name_column_index, name_item)
                return True
        
        # Processing ID not found in table
        return False

    def set_table_loading(self):
        table_item = QTableWidgetItem(self.tr("Loading..."))
        table_item.setToolTip(self.tr('Fetching your processings from server, please wait'))
        self.dlg.processingsTable.setRowCount(1)
        self.dlg.processingsTable.setItem(0, 0, table_item)
        for column in range(1, self.dlg.processingsTable.columnCount()):
            empty_item = QTableWidgetItem("")
            self.dlg.processingsTable.setItem(0, column, empty_item)

    def show_processings_pages(self, enable: bool = False, page_number: int = 1, total_pages: int = 1):
        self.dlg.processingsPreviousPageButton.setVisible(enable)
        self.dlg.processingsNextPageButton.setVisible(enable)
        self.dlg.processingsPageLabel.setVisible(enable)
        if enable is True:
            self.dlg.processingsPageLabel.setText(f"{page_number}/{total_pages}")
        # Disable next arrow for the last page
        if page_number == total_pages:
            self.dlg.processingsNextPageButton.setEnabled(False)
        else:
            self.dlg.processingsNextPageButton.setEnabled(True)
        # Disable previous arrow for the first page
        if page_number == 1:
            self.dlg.processingsPreviousPageButton.setEnabled(False)
        else:
            self.dlg.processingsPreviousPageButton.setEnabled(True)

    def enable_processings_pages(self, enable: bool = False):
        self.dlg.processingsNextPageButton.setEnabled(enable)
        self.dlg.processingsPreviousPageButton.setEnabled(enable)

    def sort_processings(self):
        # Header click overrides the combo if set
        if self._header_sort_by is not None:
            sort_by = self._header_sort_by
            sort_order = "DESC" if self._header_sort_desc else "ASC"
            return sort_by, sort_order
        index = self.dlg.sortProcessingsCombo.currentIndex()
        # Sort by
        if index in (0, 1):  # Newest/Oldest first
            sort_by = ProcessingSortBy.created
        elif index in (2, 3):  # A-Z / Z-A
            sort_by = ProcessingSortBy.name
        else:  # Status A-Z / Z-A
            sort_by = ProcessingSortBy.status
        # Sort order
        if index in (1, 2, 4):  # Oldest, A-Z, Status A-Z
            sort_order = ProcessingSortOrder.ascending
        else:  # Newest, Z-A, Status Z-A
            sort_order = ProcessingSortOrder.descending
        return sort_by.value, sort_order.value

    def delete_processings_from_table(self, processing_ids):
        rows = [self.dlg.processingsTable.findItems(id_, Qt.MatchExactly)[0].row() for id_ in processing_ids]
        rows.sort(reverse=True)
        for row in rows:
            self.dlg.processingsTable.removeRow(row)

    def set_processing_cost(self, cost: int):
        self.dlg.processingProblemsLabel.setPalette(self.dlg.default_palette)
        self.dlg.processingProblemsLabel.setText(self.tr("Processing cost: {cost} credits").format(cost=cost))
        self.dlg.startProcessing.setEnabled(True)

    def alert_failed_processings(self, failed_processings):
        if not failed_processings:
            return
            # this means that some of processings have failed since last update and the limit must have been returned
        if len(failed_processings) == 1:
            proc = failed_processings[0]
            alert(
                proc.name +
                self.tr(' failed with error:\n') + proc.error_message(self.config.SHOW_RAW_ERROR),
                QMessageBox.Critical,
                blocking=False)
        elif 1 < len(failed_processings) < 10:
            # If there are more than one failed processing, we will not
            alert(self.tr('{} processings failed: \n {} \n '
                               'See tooltip over the processings table'
                               ' for error details').format(len(failed_processings),
                                                            '\n'.join((proc.name for proc in failed_processings))),
                       QMessageBox.Critical,
                       blocking=False)
        else:  # >= 10
            alert(self.tr(
                '{} processings failed: \n '
                'See tooltip over the processings table for error details').format(len(failed_processings)),
                       QMessageBox.Critical,
                       blocking=False)

    def alert_finished_processings(self, finished_processings):
        if not finished_processings:
            return
        if len(finished_processings) == 1:
            # Print error message from first failed processing
            proc = finished_processings[0]
            alert(
                proc.name +
                self.tr(' finished. Double-click it in the table to download the results.'),
                QMessageBox.Information,
                blocking=False  # don't repeat if user doesn't close the alert
            )
        elif 1 < len(finished_processings) < 10:
            # If there are more than one failed processing, we will not
            alert(self.tr(
                '{} processings finished: \n {} \n '
                'Double-click it in the table '
                'to download the results').format(len(finished_processings),
                                                  '\n'.join((proc.name for proc in finished_processings))),
                       QMessageBox.Information,
                       blocking=False)
        else:  # >= 10
            alert(self.tr(
                '{} processings finished. \n '
                'Double-click it in the table to download the results').format(len(finished_processings)),
                       QMessageBox.Information,
                       blocking=False)

    def selected_processing_ids(self, limit=None):
        # add unique selected rows
        selected_rows = list(set(index.row() for index in self.dlg.processingsTable.selectionModel().selectedIndexes()))
        if not selected_rows:
            return []
        pids = [self.dlg.processingsTable.item(row,
                                               config.PROCESSING_TABLE_ID_COLUMN_INDEX).text()
                for row in selected_rows[:limit]]
        return pids
