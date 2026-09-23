"""The two dialogs for choosing a working directory, and the field that shows it.

Holds no service (`spec/007_architecture.md` § Layer rules): it asks, and returns what the user
answered. Whether the answer is usable is `WorkdirService`'s.
"""
from typing import Optional

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

from ...dialogs.main_dialog import MainDialog


class WorkdirView(QObject):
    """Picking a directory, and explaining why one is needed."""

    def __init__(self, dlg: MainDialog, main_window=None, plugin_name: str = "Mapflow"):
        super().__init__()
        self.dlg = dlg
        #: Parent for the 'why' prompt, so it is modal to QGIS rather than to the plugin panel —
        #: the panel is dockable and can be hidden while the prompt is up.
        self.main_window = main_window
        self.plugin_name = plugin_name

    def shown_path(self) -> str:
        return self.dlg.outputDirectory.text()

    def show_path(self, path: str) -> None:
        self.dlg.outputDirectory.setText(path)

    def ask_for_directory(self) -> Optional[str]:
        """The file dialog. Returns the chosen path, or an empty string if the user closed it."""
        return QFileDialog.getExistingDirectory(
            QApplication.activeWindow(), self.tr('Select output directory'))

    def offer_to_choose(self, message: str) -> bool:
        """Explain why a directory is needed and offer to pick one now.

        Returns True if the user chose to select one, False if they postponed — which the caller
        treats as cancelling whatever action needed the directory. Rich text, because the callers
        pass messages containing links.
        """
        box = QMessageBox(QMessageBox.Warning, self.plugin_name, message, parent=self.main_window)
        box.setTextFormat(Qt.RichText)
        select_button = box.addButton(self.tr("Select directory…"), QMessageBox.AcceptRole)
        box.addButton(self.tr("Later"), QMessageBox.RejectRole)
        box.exec()
        return box.clickedButton() is select_button
