from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidgetItem
from qgis.core import QgsSettings

from mapflow.config import config
from mapflow.dialogs.main_dialog import MainDialog
from mapflow.schema.sam import MergeStrategy


def _create_dialog() -> MainDialog:
    return MainDialog(parent=None, settings=QgsSettings())


def test_processings_filter_combines_text_and_sam_checkbox():
    dialog = _create_dialog()
    try:
        model_column = config.PROCESSING_TABLE_COLUMNS.index("workflowDef")
        dialog.processingsTable.setRowCount(2)

        sam_name = QTableWidgetItem()
        sam_name.setData(Qt.DisplayRole, "SAM Trees")
        dialog.processingsTable.setItem(0, 0, sam_name)
        sam_model = QTableWidgetItem()
        sam_model.setData(Qt.DisplayRole, "SAM3-interactive")
        sam_model.setData(Qt.UserRole, True)
        dialog.processingsTable.setItem(0, model_column, sam_model)

        plain_name = QTableWidgetItem()
        plain_name.setData(Qt.DisplayRole, "Roads")
        dialog.processingsTable.setItem(1, 0, plain_name)
        plain_model = QTableWidgetItem()
        plain_model.setData(Qt.DisplayRole, "Road extractor")
        plain_model.setData(Qt.UserRole, False)
        dialog.processingsTable.setItem(1, model_column, plain_model)

        dialog.filter_processings_table("road")
        assert dialog.processingsTable.isRowHidden(0) is True
        assert dialog.processingsTable.isRowHidden(1) is False

        dialog.samOnlyFilter.setChecked(True)
        dialog.filter_processings_table("")
        assert dialog.processingsTable.isRowHidden(0) is False
        assert dialog.processingsTable.isRowHidden(1) is True
    finally:
        dialog.close()


def test_debug_output_is_hidden_when_group_is_collapsed():
    dialog = _create_dialog()
    try:
        assert dialog.samDebugGroup.isChecked() is False
        assert dialog.samDebugOutput.isHidden() is True

        dialog.samDebugGroup.setChecked(True)
        assert dialog.samDebugOutput.isHidden() is False

        dialog.samDebugGroup.setChecked(False)
        assert dialog.samDebugOutput.isHidden() is True
    finally:
        dialog.close()


def test_processing_confidence_threshold_is_available_in_sam_sidebar():
    dialog = _create_dialog()
    try:
        assert dialog.samProcessingConfidenceThresholdLabel.text() == "Confidence:"
        assert dialog.samProcessingConfidenceThresholdInput.value() == 0.5
        assert dialog.samProcessingConfidenceThresholdInput.minimum() == 0.25
        assert dialog.samProcessingConfidenceThresholdInput.maximum() == 0.75
    finally:
        dialog.close()


def test_inference_merge_strategy_selector_defaults_to_instance_segmentation():
    expected_values = [strategy.value for strategy in MergeStrategy]
    dialog = _create_dialog()
    try:
        inference_values = [
            dialog.samMergeStrategyInput.itemText(i)
            for i in range(dialog.samMergeStrategyInput.count())
        ]

        assert dialog.samMergeStrategyLabel.text() == "Merge:"
        assert inference_values == expected_values
        assert dialog.samMergeStrategyInput.currentText() == (
            MergeStrategy.INSTANCE_SEGMENTATION.value
        )
    finally:
        dialog.close()
