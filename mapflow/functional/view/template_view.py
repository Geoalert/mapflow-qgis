from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMessageBox

from ...dialogs.main_dialog import MainDialog


class TemplateView(QObject):
    """Template-specific widget reads/writes on the panel: the search/plan name field, the
    Search button's busy state, the "select a project" reminder in the problems label, and the
    too-large-AOI "Plan Search?" prompt.

    Holds no service (`spec/007_architecture.md` § Layer rules). `TemplateController` reads from
    here, calls `TemplateService`, and pushes effects back.
    """

    def __init__(self, dlg: MainDialog, iface):
        super().__init__()
        self.dlg = dlg
        self.iface = iface

    def template_name(self) -> str:
        return self.dlg.processingName.text().strip()

    def set_search_enabled(self, enabled: bool) -> None:
        """The 'Search / Plan search' button — disabled while a create request is in flight."""
        self.dlg.getMetadata.setEnabled(enabled)

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
