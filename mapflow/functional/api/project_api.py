import json
from typing import Optional, Callable

from PyQt5.QtCore import QObject

from ...schema.project import CreateProjectSchema, UpdateProjectSchema, ProjectsRequest
from ...http import Http


class ProjectApi(QObject):
    def __init__(self,
                 http: Http,
                 server: str):
        super().__init__()
        self.server = server
        self.http = http

    def create_project(self, project: CreateProjectSchema, callback: Callable):
        self.http.post(url=f"{self.server}/projects",
                       body=project.as_json().encode(),
                       headers={},
                       callback=callback,
                       use_default_error_handler=True,
                       timeout=5)
        
    def delete_project(self, project_id, callback: Callable):
        self.http.delete(url=f"{self.server}/projects/{project_id}",
                         headers={},
                         callback=callback,
                         use_default_error_handler=True,
                         timeout=5)
    
    def update_project(self, project_id, project: UpdateProjectSchema, callback: Callable):
        self.http.put(url=f"{self.server}/projects/{project_id}",
                      body=project.as_json().encode(),
                      headers={},
                      callback=callback,
                      use_default_error_handler=True,
                      timeout=5)

    def get_project(self, project_id, callback):
        self.http.get(url=f"{self.server}/projects/{project_id}",
                      headers={},
                      callback=callback,
                      use_default_error_handler=True,
                      timeout=5)
    
    def get_projects(self, 
                     request_body: ProjectsRequest, 
                     callback: Callable):
        self.http.post(url=f"{self.server}/projects/page",
                       headers={},
                       body=request_body.as_json().encode(),
                       callback=callback,
                       use_default_error_handler=True,
                       timeout=10)
