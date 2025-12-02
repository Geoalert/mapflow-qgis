from typing import Optional
from PyQt5.QtCore import QObject, QSettings
from PyQt5.QtWidgets import QMessageBox

from ..app_context import AppContext
from ..service.processing_service import ProcessingService
from ..service.project_service import ProjectService
from ...dialogs import CreateProjectDialog, UpdateProjectDialog, MainDialog, UpdateProcessingDialog


class ProjectProcessingController(QObject):
    """
    Controller that coordinates navigation and interactions between 
    Projects and Processings views.
    
    Responsibilities:
    - Wire UI events to service methods
    - Handle navigation between projects and processings views
    - Connect signals between services
    """
    
    def __init__(self, dlg: MainDialog,
                 processing_service: ProcessingService,
                 project_service: ProjectService,
                 settings: QSettings,
                 app_context: AppContext):
        super().__init__()
        self.dlg = dlg
        self.processing_service = processing_service
        self.project_service = project_service
        self.settings = settings
        self.app_context = app_context
        
        self._setup_processing_bindings()
        self._setup_project_bindings()
        self._setup_navigation()

        self.project_connection = None
    
    def _setup_processing_bindings(self):
        """Processing-specific UI connections."""
        self.dlg.startProcessing.clicked.connect(self.processing_service.start_processing)
        self.dlg.processing_update_action.triggered.connect(self.update_processing)
        self.processing_service.processing_fetch_timer.timeout.connect(
            self.processing_service.get_processings
        )
    
    def _setup_project_bindings(self):
        """Project-specific UI connections."""
        # Project service already sets up its own pagination/filter bindings in __init__
        # Projects
        self.dlg.createProject.clicked.connect(self.create_project)
        self.dlg.deleteProject.clicked.connect(self.delete_project)
        self.dlg.updateProject.clicked.connect(self.update_project)
        self.project_service.projectsUpdated.connect(self.project_service.update_projects)
        self.project_service.projectsFiltered.connect(self.connect_projects)

    def _setup_navigation(self):
        """Navigation between projects and processings views."""
        # Connect UI navigation buttons
        self.dlg.switchProjectsButton.clicked.connect(lambda: self.show_projects(open_saved_page=True))
        self.dlg.switchProcessingsButton.clicked.connect(lambda: self.show_processings(save_page=True))
        self.dlg.projectsTable.doubleClicked.connect(self._on_project_double_clicked)
    
    def _on_project_double_clicked(self, index):
        """Handle double-click on project row to navigate to processings."""
        project_id = self.dlg.projectsTable.item(index.row(), 0).text()
        self.app_context.current_project = self.project_service.projects.get(project_id)
        self.show_processings(save_page=True)

    def show_processings(self, save_page: bool = False):
        """
        Navigate to processings view for current/specified project.
        
        Args:
            save_page: If True, save current projects page state to settings
            project_id: The project ID to show processings for. If None, uses current project.
        """
        if not self.app_context.project_id:
            return

        # Save current projects page state before switching
        if save_page:
            sort_by, sort_order = self.project_service.view.sort_projects()
            projects_page = {
                'offset': self.project_service.projects_page_offset,
                'sort_by': sort_by,
                'sort_order': sort_order,
                'filter': self.project_service.view.projects_filter
            }
            self.settings.setValue('projectsPage', projects_page)
        # Load processing history
        self.processing_service.load_processing_history()
        # Switch view
        self.project_service.view.switch_to_processings()

        # Setup processings table for the project
        self.processing_service.setup_processings_table()

    def update_processing(self):
        processing = self.processing_service.selected_processing()
        if not processing:
            return
        dialog = UpdateProcessingDialog(self.dlg)
        dialog.accepted.connect(lambda: self.processing_service.update_processing(processing.id,
                                                                                  dialog.processing()))
        dialog.setup(processing)
        dialog.deleteLater()

    # ==== PROJECTS ==== #
    def show_projects(self, open_saved_page: bool = False):
        """
        Navigate to projects view.
        
        Args:
            open_saved_page: If True, restore previously saved page state from settings
        """
        # Stop processing polling when leaving processings view
        self.processing_service.processing_fetch_timer.stop()
        
        # Fetch projects (handles saved page restoration internally)
        self.project_service.get_projects(open_saved_page)
        
        # Switch view
        self.project_service.view.switch_to_projects()

    def create_project(self):
        dialog = CreateProjectDialog(self.dlg)
        dialog.accepted.connect(lambda: self.project_service.create_project(dialog.project()))
        dialog.setup()
        dialog.deleteLater()

    def update_project(self):
        dialog = UpdateProjectDialog(self.dlg)
        dialog.accepted.connect(lambda: self.project_service.update_project(self.app_context.current_project.id,
                                                                            dialog.project()))
        dialog.setup(self.app_context.current_project)
        dialog.deleteLater()

    def delete_project(self):
        if self.alert(self.tr('Do you really want to remove project {}? '
                              'This action cannot be undone, all processings will be lost!').format(
            self.app_context.current_project.name),
                      icon=QMessageBox.Question):
            # Unload current project as we are deleting it
            to_delete = self.app_context.project_id
            self.app_context.project_id = None
            self.app_context.current_project = None
            self.project_service.delete_project(to_delete)

    def connect_projects(self):
        """
        Reset connection between project table selection and project change
        """
        if self.project_connection is not None:
            self.dlg.projectsTable.itemSelectionChanged.disconnect(self.project_connection)
            self.project_connection = None
        self.project_connection = self.dlg.projectsTable.itemSelectionChanged.connect(self.project_service.on_project_change)
