from typing import List, Optional
from uuid import UUID
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtWidgets import QAbstractItemView, QTableWidgetItem, QMessageBox
from PyQt5.QtGui import QColor
from ...dialogs.main_dialog import MainDialog
from ...schema.processing import ProcessingDTO, ProcessingUIParams
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
            name = self.dlg.processingName or None,
            wd_name = self.dlg.modelCombo.currentText(),
            data_source_index = self.dlg.providerIndex(),
            # todo: add other params
        )

    def clear_processing_name(self, name):
        # If the name is expected, we clear it after the processsing is launched;
        # Otherwise it means that the user has altered the text already and it should be preserved
        if self.dlg.processingName.text == name:
            self.dlg.processingName.clear()

    def disable_processing_start(self, reason: str, clear_area: bool):
        self.dlg.disable_processing_start(reason=reason, clear_area=clear_area)

    def create_table_items(self, processing: ProcessingDTO):
        table_items = []
        set_color = False
        processing_dict = processing.as_processing_table_dict()
        if processing.status.is_ok and processing.review_expires:
            # setting color for close review
            set_color = True
            color = QColor(255, 220, 200)
        for col, attr in enumerate(config.PROCESSING_TABLE_COLUMNS):
            table_item = QTableWidgetItem()
            table_item.setData(Qt.DisplayRole, processing_dict[attr])
            if processing.status.is_failed:
                table_item.setToolTip(processing.error_message(raw=config.SHOW_RAW_ERROR))
            elif processing.reviewUntil:
                table_item.setToolTip(self.tr("Please review or accept this processing until {}."
                                              " Double click to add results"
                                              " to the map").format(
                    processing.reviewUntil.strftime('%Y-%m-%d %H:%M') if processing.reviewUntil else ""))
            elif processing.status.is_ok:
                table_item.setToolTip(self.tr("Double click to add results to the map."
                                              ))
            if set_color:
                table_item.setBackground(color)
            table_items.append(table_item)
        return table_items

    def update_processing_table(self, processings: List[ProcessingDTO]):
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
        self.dlg.processingsTable.setSortingEnabled(True)
        # Restore extended selection and filtering
        self.dlg.processingsTable.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.dlg.filter_processings_table(self.dlg.filterProcessings.text())

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


    def delete_processings_from_table(self, processing_ids):
        rows = [self.dlg.processingsTable.findItems(id_, Qt.MatchExactly)[0].row() for id_ in processing_ids]
        rows.sort(reverse=True)
        for row in rows:
            self.dlg.processingsTable.removeRow(row)

    def set_processing_cost(self, cost: int):
        self.dlg.processingProblemsLabel.setPalette(self.dlg.default_palette)
        self.dlg.processingProblemsLabel.setText(self.tr("Processsing cost: {cost} credits").format(cost=cost))
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
