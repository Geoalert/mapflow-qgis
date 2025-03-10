import json
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QNetworkReply

from ..dialogs.main_dialog import MainDialog
from ..config import Config
from ..schema.project import CreateProjectSchema, UpdateProjectSchema, MapflowProject, MapflowProjectInfo, ProjectsRequest, ProjectsResult


class ProjectService(QObject):
    projectsUpdated = pyqtSignal(str)

    def __init__(self, http, server, dlg: MainDialog):
        super().__init__()
        self.http = http
        self.server = server
        self.dlg = dlg
        self.projects_data = {}
        self.projects = []
        self.project = None
        self.projects_page_offset = 0
        self.projects_page_limit = Config.PROJECTS_PAGE_LIMIT
        self.projects_filter = None
        self.dlg.projectsNextPageButton.clicked.connect(self.show_projects_next_page)
        self.dlg.projectsPreviousPageButton.clicked.connect(self.show_projects_previous_page)
        self.dlg.filterProjects.textChanged.connect(self.get_projects)

    def create_project(self, project: CreateProjectSchema):
        self.http.post(url=f"{self.server}/projects",
                       body=project.as_json().encode(),
                       headers={},
                       callback=self.create_project_callback,
                       use_default_error_handler=True,
                       timeout=5)

    def create_project_callback(self, response: QNetworkReply):
        project = MapflowProject.from_dict(json.loads(response.readAll().data()))
        new_project_id = project.id
        self.get_projects(current_project_id = new_project_id)

    def delete_project(self, project_id):
        self.http.delete(url=f"{self.server}/projects/{project_id}",
                      headers={},
                      callback=self.delete_project_callback,
                      use_default_error_handler=True,
                      timeout=5)

    def delete_project_callback(self, response: QNetworkReply):
        self.get_projects()

    def update_project(self, project_id, project: UpdateProjectSchema):
        self.http.put(url=f"{self.server}/projects/{project_id}",
                       body=project.as_json().encode(),
                       headers={},
                       callback=self.update_project_callback,
                       use_default_error_handler=True,
                       timeout=5)

    def update_project_callback(self, response: QNetworkReply):
        project = MapflowProject.from_dict(json.loads(response.readAll().data()))
        new_project_id = project.id
        self.get_projects(current_project_id=new_project_id)

    def get_project(self, project_id, callback):
        self.http.get(url=f"{self.server}/projects/{project_id}",
                          headers={},
                          callback=callback,
                          use_default_error_handler=True,
                          timeout=5)

    def get_projects(self, current_project_id: Optional[str] = None):
        self.projects_filter = self.dlg.filterProjects.text()
        request_body = ProjectsRequest(self.projects_page_limit, self.projects_page_offset, self.projects_filter)
        self.http.post(url=f"{self.server}/projects/page",
                          headers={},
                          body=request_body.as_json().encode(),
                          callback=self.get_projects_callback,
                          callback_kwargs ={'current_project_id': current_project_id},
                          use_default_error_handler=True,
                          timeout=10)
        self.dlg.projectsNextPageButton.setEnabled(False)
        self.dlg.projectsPreviousPageButton.setEnabled(False)

    def get_projects_callback(self, response: QNetworkReply, current_project_id: Optional[str] = None):
        self.projects_data = ProjectsResult.from_dict(json.loads(response.readAll().data()))
        self.projects = [MapflowProject.from_dict(project) for project in self.projects_data.results]
        self.projectsUpdated.emit(current_project_id or "Default")
        self.dlg.setup_projects_table(self.projects)
        # En(dis)able page controls based on total, limit and offset
        if self.projects_data.total > self.projects_page_limit:
            quotient, remainder = divmod(self.projects_data.total, self.projects_page_limit)
            projects_total_pages = quotient + (remainder > 0)
            projects_page_number = int(self.projects_page_offset/self.projects_page_limit) + 1
            self.dlg.enable_projects_pages(True, projects_page_number, projects_total_pages)
            # Disable next arrow for the last page
            if projects_page_number == projects_total_pages:
                self.dlg.projectsNextPageButton.setEnabled(False)
            else:
                self.dlg.projectsNextPageButton.setEnabled(True)
            # Disable previous arrow for the first page
            if projects_page_number == 1:
                self.dlg.projectsPreviousPageButton.setEnabled(False)
            else:
                self.dlg.projectsPreviousPageButton.setEnabled(True)
        else:
            self.dlg.enable_projects_pages(False)
        self.dlg.projectsTable.clearSelection()

    def show_projects_next_page(self):
        self.projects_page_offset += self.projects_page_limit
        self.get_projects()

    def show_projects_previous_page(self):
        self.projects_page_offset += -self.projects_page_limit
        self.get_projects()
