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
    projectChanged = pyqtSignal(str)  # Emits project_id when project selection changes

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
        self.project_id = None
        self.projects_page_limit = Config.PROJECTS_PAGE_LIMIT
        self.projects_page_offset = 0
        # Connections
        self.dlg.projectsNextPageButton.clicked.connect(self.show_projects_next_page)
        self.dlg.projectsPreviousPageButton.clicked.connect(self.show_projects_previous_page)
        self.dlg.filterProjects.textEdited.connect(self.get_filtered_projects)
        self.dlg.sortProjectsCombo.activated.connect(self.get_projects)
    
    def create_project(self, project: CreateProjectSchema):
        self.api.create_project(project, self.create_project_callback)

    def create_project_callback(self, response: QNetworkReply):
        project = MapflowProject.from_dict(json.loads(response.readAll().data()))
        self.project_id = project.id
        self.projectChanged.emit(str(project.id))
        self.get_projects()
    
    def delete_project(self, project_id):
        # Remove and temporary forbid selection (until get_projects_callback)
        self.dlg.projectsTable.setSelectionMode(QAbstractItemView.NoSelection)
        self.dlg.projectsTable.clearSelection()
        self.api.delete_project(project_id, self.delete_project_callback)
    
    def delete_project_callback(self, response: QNetworkReply):
        self.projects_data.total += -1
        self.get_projects()
    
    def update_project(self, project_id, project: UpdateProjectSchema):
        self.api.update_project(project_id, project, self.update_project_callback)
    
    def update_project_callback(self, response: QNetworkReply):
        project = MapflowProject.from_dict(json.loads(response.readAll().data()))
        self.project_id = project.id
        self.projectChanged.emit(str(project.id))
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
        try: # if something changed and offset is now >= projects count
            if self.projects_page_offset >= self.projects_data.total:
                self.projects_page_offset = 0 # show first page
        except AttributeError:
            pass # if projects is an empty dict
        # Open the page containing current project
        if open_saved_page is True:
            # Get each page parameter from dict in settings (if no dict - create one with default values)
            projects_page = self.settings.value('projectsPage', {'offset' : self.projects_page_offset,
                                                                 'sort_by' : ProjectSortBy.updated,
                                                                 'sort_order' : ProjectSortOrder.descending,
                                                                 'filter': ""})
            self.projects_page_offset = int(projects_page['offset'])
            sort_by = projects_page['sort_by']
            sort_order = projects_page['sort_order']
            projects_filter = projects_page['filter']
            # Set saved filtering and sorting in UI
            if projects_filter:
                self.dlg.filterProjects.setText(projects_filter)
            # Find pairs of sorting combo indecies from sort_by (not knowing sort_order)
            if sort_by == ProjectSortBy.name:
                by = (0, 1)
            elif sort_by == ProjectSortBy.created:
                by = (2, 3)
            else: # sort_by == ProjectSortBy.updated
                by = (4, 5)
            # Find triples of sorting combo indecies from sort_order (not knowing sort_by)
            if sort_order == ProjectSortOrder.ascending: # A-Z, Oldest first, Updated long ago
                order = (0, 3, 5)
            else: # ProjectSortOrder.descending: Z-A, Newest first, Updated recently
                order = (1, 2, 4)
            # Get and set the only element of the intersection of sort_by and sort_order indecies
            index = set(by).intersection(set(order)).pop()
            self.dlg.sortProjectsCombo.setCurrentIndex(index)
        # Load page getting params from UI and don't change self.projects_page_offset
        else:
            sort_by, sort_order = self.view.sort_projects()
            projects_filter = self.dlg.filterProjects.text()
        # Send request with defined parameters
        request_body = ProjectsRequest(self.projects_page_limit, 
                                       self.projects_page_offset,
                                       projects_filter,
                                       sort_by, sort_order)
        self.api.get_projects(request_body, self.get_projects_callback)
        # Forbid clicking on pages controls before getting a response
        self.view.enable_projects_pages(False)
        self.dlg.projectsTable.clearSelection()
    
    def get_projects_callback(self, response: QNetworkReply):
        self.projects_data = ProjectsResult.from_dict(json.loads(response.readAll().data()))
        self.projects = [MapflowProject.from_dict(project) for project in self.projects_data.results]
        self.dlg.projectsTable.setSortingEnabled(False) # temporary disable sorting by clicking the header
        self.view.setup_projects_table(self.projects)
        # En(dis)able page controls based on total, limit and offset
        if self.projects_data.total > self.projects_page_limit:
            quotient, remainder = divmod(self.projects_data.total, self.projects_page_limit)
            projects_total_pages = quotient + (remainder > 0)
            projects_page_number = int(self.projects_page_offset/self.projects_page_limit) + 1
            self.view.show_projects_pages(True, projects_page_number, projects_total_pages)
        else:
            # When no projects found, but no filter specified (should be at lest 'Default')
            if not self.projects_data.total and len(self.dlg.filterProjects.text()) <= 1:
                self.get_projects() # request first page without any parameters
            else: # when total is just less than the limit
                self.view.show_projects_pages(False) # show first page and no controls
        self.projectsUpdated.emit()
        self.dlg.projectsTable.clearSelection()
        self.dlg.projectsTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.select_project(self.project_id)
    
    def select_project(self, project_id):
        self.view.select_project(project_id)
    
    def show_projects_next_page(self):
        self.projects_page_offset += self.projects_page_limit
        self.get_projects()

    def show_projects_previous_page(self):
        self.projects_page_offset += -self.projects_page_limit
        self.get_projects()
    
    def switch_to_projects(self, open_saved_page: Optional[bool] = False):
        """Get projects and switch from processings to projects table in stacked widget.

        Allows to open saved projects page even after reload.
        But we don't need to do that when e.g. we are switching to a different projects page.

        :param open_saved_page: A boolean that determines if we should get projects page from the settings or not.
        """
        self.get_projects(open_saved_page)
        self.view.switch_to_projects()

    def switch_to_processings(self, 
                              save_page: Optional[bool] = False,
                              project_id: Optional[int]  = None):
        """Switch from projects to processings table in stacked widget.

        Allows to remember current projects page before switching (to later reopen it even after reload).
        But we only want to remember it if user chose a project (not when switching if no id was saved).

        :param save_page: A boolean that determines if we should save projects page parameters to settings or not.
        """
        if save_page:
            # Save current offset, sorting and filter
            sort_by, sort_order = self.view.sort_projects()
            projects_filter = self.dlg.filterProjects.text()
            projects_page = {'offset' : self.projects_page_offset,
                             'sort_by' : sort_by,
                             'sort_order' : sort_order,
                             'filter': projects_filter}
            self.settings.setValue('projectsPage', projects_page)
        self.view.switch_to_processings()
        self.project_id = project_id
        if project_id:
            self.projectChanged.emit(str(project_id))

    def get_filtered_projects(self):
        """Get projects, resetting filtered offset value.

        Is called when texted is edited by user (not just changed programmatically).
        So each time offset resets to 0 to show 1st page of newly filtered response.
        """
        self.projects_page_offset = 0
        self.project_id = None
        self.get_projects()
