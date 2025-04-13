import json
from typing import Optional, Callable

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QNetworkReply
from PyQt5.QtWidgets import QAbstractItemView

from ...dialogs.main_dialog import MainDialog
from ...config import Config
from ...schema.project import CreateProjectSchema, UpdateProjectSchema, MapflowProject, ProjectsRequest, ProjectsResult, ProjectSortBy, ProjectSortOrder
from ..api.project_api import ProjectApi
from ..view.project_view import ProjectView


class ProjectService(QObject):
    projectsUpdated = pyqtSignal()

    def __init__(self, http, server, settings, dlg: MainDialog):
        super().__init__()
        self.http = http
        self.server = server
        self.settings = settings
        self.dlg = dlg
        self.api = ProjectApi(self.http, self.server)
        self.view = ProjectView(self.dlg)
        self.projects_data = {}
        self.projects = []
        self.projects_page_limit = Config.PROJECTS_PAGE_LIMIT
        self.projects_page_offset = 0 # filtering and regular offsets are different, 
        self.projects_filtered_offset = 0 # so if we removed filter, we'll return to the page we were on
        # Connections
        self.dlg.projectsNextPageButton.clicked.connect(self.show_projects_next_page)
        self.dlg.projectsPreviousPageButton.clicked.connect(self.show_projects_previous_page)
        self.dlg.filterProjects.textEdited.connect(self.get_filtered_projects)
        self.dlg.sortProjectsCombo.activated.connect(self.get_projects)
    
    def create_project(self, project: CreateProjectSchema):
        self.api.create_project(project, self.create_project_callback)

    def create_project_callback(self, response: QNetworkReply):
        self.get_projects()
    
    def delete_project(self, project_id):
        # Remove and temporary forbid selection (until get_projects_callback)
        self.dlg.projectsTable.setSelectionMode(QAbstractItemView.NoSelection)
        self.dlg.projectsTable.clearSelection()
        self.api.delete_project(project_id, self.delete_project_callback)
    
    def delete_project_callback(self, response: QNetworkReply):
        self.get_projects()
    
    def update_project(self, project_id, project: UpdateProjectSchema):
        self.api.update_project(project_id, project, self.update_project_callback)
    
    def update_project_callback(self, response: QNetworkReply):
        self.get_projects()
    
    def get_project(self, project_id, callback: Callable, error_handler: Callable):
        self.api.get_project(project_id, callback, error_handler)
    
    def get_projects(self, open_saved_page: Optional[bool] = False):
        """Get projects depending on page parameters (offset, sorting, filtering).

        Either get saved projects page (e.g. we load plugin with processings of project from 2nd page, 
        and when going back to projects table, 2nd page should be shown).
        Or load projects based on current offset and UI (sorting index and filtering text).

        :param open_saved_page: A boolean that determines if we should get projects page from the settings or not.
        """
        # Open the page containing current project
        if open_saved_page is True:
            # Get values from settings
            projects_offset = self.settings.value('projectsOffset', self.projects_page_offset)
            sort_by = self.settings.value('projectsSortBy', ProjectSortBy.updated)
            sort_order = self.settings.value('projectsSortOrder', ProjectSortOrder.descending)
            projects_filter = self.settings.value('projectsFilter')
            # Set right (filtered or general) offset from settings to use later in callback
            if projects_filter:
                self.projects_filtered_offset = projects_offset
                self.dlg.filterProjects.setText(projects_filter)
            else:
                self.projects_page_offset = projects_offset
        # Load page getting params from offset and UI
        else:
            sort_by, sort_order = self.view.sort_projects()
            projects_filter = self.dlg.filterProjects.text()
            # Define right (filtered or general) offset from attributes
            if projects_filter:
                projects_offset = self.projects_filtered_offset
                self.dlg.filterProjects.setText(projects_filter)
            else:
                projects_offset = self.projects_page_offset
        # Send request with defined parameters
        request_body = ProjectsRequest(self.projects_page_limit, 
                                       projects_offset,
                                       projects_filter,
                                       sort_by, sort_order)
        self.api.get_projects(request_body, self.get_projects_callback)
        # Forbid clicking on pages controls before getting a response
        self.view.enable_projects_pages(False)
        self.dlg.projectsTable.clearSelection()
    
    def get_projects_callback(self, response: QNetworkReply):
        self.projects_data = ProjectsResult.from_dict(json.loads(response.readAll().data()))
        self.projects = [MapflowProject.from_dict(project) for project in self.projects_data.results]
        self.view.setup_projects_table(self.projects)
        # En(dis)able page controls based on total, limit and offset
        if self.projects_data.total > self.projects_page_limit:
            quotient, remainder = divmod(self.projects_data.total, self.projects_page_limit)
            projects_total_pages = quotient + (remainder > 0)
            if self.dlg.filterProjects.text():
                projects_offset = self.projects_filtered_offset
            else:
                projects_offset = self.projects_page_offset
            projects_page_number = int(projects_offset/self.projects_page_limit) + 1
            self.view.show_projects_pages(True, projects_page_number, projects_total_pages)
        else:
            self.view.show_projects_pages(False)
        self.projectsUpdated.emit()
        self.dlg.projectsTable.clearSelection()
        self.dlg.projectsTable.setSelectionMode(QAbstractItemView.SingleSelection)
    
    def select_project(self, project_id):
        self.view.select_project(project_id)
    
    def show_projects_next_page(self):
        if self.dlg.filterProjects.text():
            self.projects_filtered_offset += self.projects_page_limit
        else:
            self.projects_page_offset += self.projects_page_limit
        self.get_projects()

    def show_projects_previous_page(self):
        if self.dlg.filterProjects.text():
            self.projects_filtered_offset += -self.projects_page_limit
        else:
            self.projects_page_offset += -self.projects_page_limit
        self.get_projects()
    
    def switch_to_projects(self, open_saved_page: Optional[bool] = False):
        """Get projects and switch from processings to projects table in stacked widget.

        Allows to open saved projects page even after reload.
        But we don't need to do that when e.g. we are switching to a different projects page.

        :param open_saved_page: A boolean that determines if we should get projects page from the settings or not.
        """
        try: # if something changed and offset is now bigger than projects count
            if self.projects_page_offset > self.projects_data.total:
                self.projects_page_offset = 0 # show first page
        except AttributeError:
            pass # if projects is an empty dict
        self.get_projects(open_saved_page)
        self.view.switch_to_projects()

    def switch_to_processings(self, save_page: Optional[bool] = False):
        """Switch from projects to processings table in stacked widget.

        Allows to remember current projects page before switching (to later reopen it even after reload).
        But we only want to remember it if user chose a project (not when switching if no id was saved).

        :param save_page: A boolean that determines if we should save projects page parameters to settings or not.
        """
        if save_page:
            # Save current sorting
            sort_by, sort_order = self.view.sort_projects()
            self.settings.setValue('projectsSortBy', sort_by)
            self.settings.setValue('projectsSortOrder', sort_order)
            # Save current filter
            projects_filter = self.dlg.filterProjects.text()
            self.settings.setValue('projectsFilter', projects_filter)
            # Save current offset
            if projects_filter:
                self.settings.setValue('projectsOffset', self.projects_filtered_offset)
            else:
                self.settings.setValue('projectsOffset', self.projects_page_offset)            
        self.view.switch_to_processings()

    def get_filtered_projects(self):
        """Get projects, resetting filtered offset value.

        Is called when texted is edited by user (not just changed programmatically).
        So each time offset resets to 0 to show 1st page of newly filtered response.
        """
        self.projects_filtered_offset = 0
        self.get_projects()
