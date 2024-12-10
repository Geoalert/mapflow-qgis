import json
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QNetworkReply

from ..schema.project import CreateProjectSchema, UpdateProjectSchema, MapflowProject


class ProjectService(QObject):
    projectsUpdated = pyqtSignal(str)

    def __init__(self, http, server):
        super().__init__()
        self.http = http
        self.server = server
        self.projects = []

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


    def get_project(self, project_id):
        self.http.get(url=f"{self.server}/projects/{project_id}",
                          headers={},
                          callback=self.get_project_callback,
                          use_default_error_handler=True,
                          timeout=5)

    def get_projects(self, current_project_id: Optional[str] = None):
        self.http.get(url=f"{self.server}/projects",
                          headers={},
                          callback=self.get_projects_callback,
                          callback_kwargs ={'current_project_id': current_project_id},
                          use_default_error_handler=True,
                          timeout=10)

    def get_projects_callback(self, response: QNetworkReply, current_project_id: Optional[str] = None):
        self.projects = [MapflowProject.from_dict(data) for data in json.loads(response.readAll().data())]
        self.projectsUpdated.emit(current_project_id or "Default")

