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

    def __init__(self, http, server, dlg: MainDialog):
        super().__init__()
        self.http = http
        self.server = server
        self.dlg = dlg
        self.api = ProjectApi(self.http, self.server)
        self.view = ProjectView(self.dlg)
        self.projects_data = {}
        self.projects = []
        self.projects_page_offset = 0
        self.projects_page_limit = Config.PROJECTS_PAGE_LIMIT
        # Connections
        self.dlg.projectsNextPageButton.clicked.connect(self.show_projects_next_page)
        self.dlg.projectsPreviousPageButton.clicked.connect(self.show_projects_previous_page)
        self.dlg.filterProjects.textChanged.connect(self.get_sorted_projects)
        self.dlg.sortProjectsCombo.activated.connect(self.get_sorted_projects)
    
    def create_project(self, project: CreateProjectSchema):
        self.api.create_project(project, self.create_project_callback)

    def create_project_callback(self, response: QNetworkReply):
        self.get_sorted_projects()
    
    def delete_project(self, project_id):
        # Remove and temporary forbid selection (until get_projects_callback)
        self.dlg.projectsTable.setSelectionMode(QAbstractItemView.NoSelection)
        self.dlg.projectsTable.clearSelection()
        self.api.delete_project(project_id, self.delete_project_callback)
    
    def delete_project_callback(self, response: QNetworkReply):
        self.get_sorted_projects()
    
    def update_project(self, project_id, project: UpdateProjectSchema):
        self.api.update_project(project_id, project, self.update_project_callback)
    
    def update_project_callback(self, response: QNetworkReply):
        self.get_sorted_projects()
    
    def get_project(self, project_id, callback: Callable):
        self.api.get_project(project_id, callback)
    
    def get_projects(self,
                     sort_by: Optional[ProjectSortBy] = ProjectSortBy.updated,
                     sort_order: Optional[ProjectSortOrder] = ProjectSortOrder.descending):
        projects_filter = self.dlg.filterProjects.text()
        request_body = ProjectsRequest(self.projects_page_limit, 
                                       self.projects_page_offset, 
                                       projects_filter, 
                                       sort_by, sort_order)
        self.api.get_projects(request_body, self.get_projects_callback)
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
            projects_page_number = int(self.projects_page_offset/self.projects_page_limit) + 1
            self.view.show_projects_pages(True, projects_page_number, projects_total_pages)
        else:
            self.view.show_projects_pages(False)
        self.projectsUpdated.emit()
        self.dlg.projectsTable.clearSelection()
        self.dlg.projectsTable.setSelectionMode(QAbstractItemView.SingleSelection)
    
    def select_project(self, project_id):
        self.view.select_project(project_id)
    
    def show_projects_next_page(self):
        self.projects_page_offset += self.projects_page_limit
        self.get_sorted_projects()

    def show_projects_previous_page(self):
        self.projects_page_offset += -self.projects_page_limit
        self.get_sorted_projects()
    
    def switch_to_projects(self):
        try: # if something changed and offset is now bigger than projects count
            if self.projects_page_offset > self.projects_data.total:
                self.projects_page_offset = 0 # show first page
        except AttributeError:
            pass # if projects is an empty dict
        self.get_sorted_projects()
        self.view.switch_to_projects()

    def switch_to_processings(self):
        self.view.switch_to_processings()
    
    def get_sorted_projects(self):
        sort_by, sort_order = self.view.sort_projects()
        self.get_projects(sort_by=sort_by, sort_order=sort_order)
