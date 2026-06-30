from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMessageBox, QWidget

from ..app_context import AppContext
from ..service.alert_service import alert
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
                 app_context: AppContext):
        super().__init__()
        self.dlg = dlg
        self.processing_service = processing_service
        self.project_service = project_service
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
        """Navigation between projects, processings and in-template views."""
        # Left arrow: back one level (template -> processings -> projects).
        self.dlg.switchProjectsButton.clicked.connect(self.navigate_back)
        self.dlg.switchProcessingsButton.clicked.connect(lambda: self.show_processings(save_page=True))
        # Right arrow (the former placeholder): enter the selected template ("one step right").
        self.dlg.switchProcessingsFakeButton.clicked.connect(self.navigate_into_template)
        self.dlg.projectsTable.doubleClicked.connect(self._on_project_double_clicked)
        # Keep the "enter template" arrow enabled only when a single template is selected.
        self.dlg.processingsTable.itemSelectionChanged.connect(self._update_nav_buttons)
        self._update_nav_buttons()

    def _on_project_double_clicked(self, index):
        """Handle double-click on project row to navigate to processings."""
        project_id = self.dlg.projectsTable.item(index.row(), 0).text()
        self.app_context.current_project = self.project_service.projects.get(project_id)
        self.show_processings(save_page=True)

    # ==== IN-TEMPLATE NAVIGATION ==== #
    def navigate_back(self):
        """Left arrow: leave a template (back to processings) or go back to projects."""
        if self.processing_service.in_template_mode:
            self.exit_template()
        else:
            self.show_projects(open_saved_page=True)

    def navigate_into_template(self):
        """Right arrow: enter the currently selected template."""
        if self.processing_service.in_template_mode:
            return
        template = self.processing_service.selected_template()
        if not template or not self.processing_service.is_only_templates_selected():
            return
        self.enter_template(template)

    def enter_template(self, template):
        """Enter the in-template view for the given template."""
        self.processing_service.enter_template_view(template)
        self._set_processings_tab_text(str(template.name))
        self._update_nav_buttons()

    def exit_template(self):
        """Return from the in-template view to the project's processings list."""
        self.processing_service.exit_template_view()
        self.processing_service.setup_processings_table()
        self._set_processings_tab_text(self.tr("Processing"))
        self._update_nav_buttons()

    def _set_processings_tab_text(self, text: str):
        """Set the processings tab label (used as a breadcrumb for the template name)."""
        processings_tab = self.dlg.tabWidget.findChild(QWidget, "processingsTab")
        if processings_tab is None:
            return
        tab_index = self.dlg.tabWidget.indexOf(processings_tab)
        if tab_index >= 0:
            self.dlg.tabWidget.setTabText(tab_index, text)

    def _update_nav_buttons(self):
        """Enable the 'enter template' arrow only for a single-template selection."""
        in_template = self.processing_service.in_template_mode
        can_enter = (
            not in_template
            and self.processing_service.is_only_templates_selected()
            and self.processing_service.selected_template() is not None
        )
        self.dlg.switchProcessingsFakeButton.setEnabled(bool(can_enter))

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
            self.app_context.settings.setValue('projectsPage', projects_page)
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
        dialog.accepted.connect(lambda: self.processing_service.update_processing(processing_id=processing.id,
                                                                                  processing=dialog.processing()))
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

        # Remove old cost
        self.processing_service.update_processing_cost()

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
        if alert(self.tr('Do you really want to remove project {}? '
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
