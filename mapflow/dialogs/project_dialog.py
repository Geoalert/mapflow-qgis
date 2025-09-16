from PyQt5 import uic
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QWidget, QDialogButtonBox

from .processing_dialog import plugin_icon, ui_path
from ..schema.project import MapflowProject, CreateProjectSchema, UpdateProjectSchema


class ProjectDialog(*uic.loadUiType(ui_path/'project_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """A dialog for creating or editing projects."""
        super().__init__(parent)
        self.setupUi(self)
        self.ok = self.buttonBox.button(QDialogButtonBox.Ok)

        # we store here the provider that we are editing right now
        self.current_project = None
        self.result = None

        self.projectName.textChanged.connect(self.on_name_change)

    def on_name_change(self):
        if not self.projectName.text():
            self.ok.setEnabled(False)
            self.ok.setToolTip(self.tr("Project name must not be empty!"))
        else:
            self.ok.setEnabled(True)
            self.ok.setToolTip("")

class CreateProjectDialog(ProjectDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.ok.setEnabled(False)

    def setup(self):
        self.setWindowTitle(self.tr("Create project"))
        self.projectName.setText("")
        self.projectDescription.setText("")
        self.exec()

    def project(self):
        if not self.projectName:
            raise AssertionError("Project name must not be empty!")
        return CreateProjectSchema(name = self.projectName.text(),
                                   description = self.projectDescription.text() or None)

class UpdateProjectDialog(ProjectDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.ok.setEnabled(True)

    def setup(self, project: MapflowProject):
        if not project:
            raise TypeError("UpdateProjectDialog requires a project to update")
        self.setWindowTitle(QCoreApplication.translate('ProjectDialog', "Edit project ") + project.name)
        self.projectName.setText(project.name)
        self.projectDescription.setText(project.description or "")
        self.exec()


    def project(self):
        if not self.projectName:
            raise AssertionError("Project name must not be empty!")
        return UpdateProjectSchema(name = self.projectName.text(),
                                   description = self.projectDescription.text() or None)
