from typing import Callable, Optional

from PyQt5.QtCore import QObject

from ...schema.project import CreateProjectSchema, UpdateProjectSchema, ProjectsRequest
from ...http import Http, RequestMode


class ProjectApi(QObject):
    """Project requests.

    A read takes the request `mode` from its caller, which knows what triggered it; a request that
    changes server state is always `INTERACTIVE`, because it must never be sent twice
    (spec/005 § Request modes).
    """
    def __init__(self,
                 http: Http):
        super().__init__()
        self.http = http

    def create_project(self, project: CreateProjectSchema, callback: Callable):
        self.http.post(path="projects",
                       body=project.as_json().encode(),
                       headers={},
                       callback=callback,
                       use_default_error_handler=True,
                       timeout=5,
                       mode=RequestMode.INTERACTIVE)

    def delete_project(self, project_id, callback: Callable):
        self.http.delete(path=f"projects/{project_id}",
                         headers={},
                         callback=callback,
                         use_default_error_handler=True,
                         timeout=5,
                         mode=RequestMode.INTERACTIVE)

    def update_project(self, project_id, project: UpdateProjectSchema, callback: Callable):
        self.http.put(path=f"projects/{project_id}",
                      body=project.as_json().encode(),
                      headers={},
                      callback=callback,
                      use_default_error_handler=True,
                      timeout=5,
                      mode=RequestMode.INTERACTIVE)

    def get_project(self, project_id, callback: Callable, error_handler: Callable, error_handler_kwargs: dict,
                    *, mode: RequestMode):
        self.http.get(path=f"projects/{project_id}",
                      headers={},
                      callback=callback,
                      use_default_error_handler= False,
                      error_handler=error_handler,
                      error_handler_kwargs=error_handler_kwargs,
                      timeout=5,
                      mode=mode)

    def get_projects(self,
                     request_body: ProjectsRequest,
                     callback: Callable,
                     *,
                     mode: RequestMode,
                     callback_kwargs: Optional[dict] = None):
        self.http.post(path="projects/page",
                       headers={},
                       body=request_body.as_json().encode(),
                       callback=callback,
                       callback_kwargs=callback_kwargs or {},
                       use_default_error_handler=True,
                       timeout=10,
                       mode=mode)
