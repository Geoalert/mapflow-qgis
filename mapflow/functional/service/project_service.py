"""Projects: fetching them, which one is open, and what the current user may do with it.

Holds no widget and no view (`spec/007_architecture.md` § Layer rules). What the projects panel
must show leaves as signals; what the panel says arrives as arguments. `ProjectProcessingController`
connects the two — it already owns the projects/processings table and the navigation between them.
"""
import json
from typing import Optional, Callable

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QNetworkReply

from .. import helpers
from ..app_context import AppContext
from ...config import Config
from ...schema.project import (CreateProjectSchema, UpdateProjectSchema, MapflowProject,
                               ProjectsRequest, ProjectsResult, ProjectSortBy, ProjectSortOrder,
                               UserRole)
from ..api.project_api import ProjectApi


class ProjectService(QObject):
    #: The projects list arrived, as a `ProjectsResult`. The controller fills the table and the
    #: pager from it — how many pages that is, is arithmetic the controller does not need to know,
    #: so `pagerChanged` carries the answer separately.
    projectsLoaded = pyqtSignal(object)
    #: (show controls, page number, total pages).
    pagerChanged = pyqtSignal(bool, int, int)
    #: A different project is open, or none (`None`). Carries the project so the controller can
    #: name it in the header; the elision needs the live label width, so it is the view's.
    currentProjectChanged = pyqtSignal(object)
    #: The window title for the current project, role and owner.
    windowTitleChanged = pyqtSignal(str)
    #: (reason, may edit) for the rename/delete controls.
    projectChangeRightsChanged = pyqtSignal(str, bool)
    #: This project is shared and the user's role limits what they may do.
    sharedRoleApplied = pyqtSignal(object)
    #: True while a request that renumbers the table is in flight, so the table must not be
    #: selectable — clicking during that window selects whatever lands on the row aimed at.
    selectionLocked = pyqtSignal(bool)

    projectsUpdated = pyqtSignal()
    projectsFiltered = pyqtSignal()

    def __init__(self, http, app_context: AppContext, config: Config):
        super().__init__()
        self.http = http
        self.app_context = app_context
        self.config = config
        self.api = ProjectApi(self.http)
        self.projects_data = None
        self.projects = {}
        self.app_context.project_id = self.app_context.project_id
        self.projects_page_limit = Config.PROJECTS_PAGE_LIMIT
        self.projects_page_offset = 0
        #: What the last request filtered by, so the empty-result branch can tell "nothing matches
        #: this filter" from "this account has no projects at all".
        self._last_filter = ""
        self.area_calculator_service = None  # set later to avoid a circular import

    def set_current_project(self, project: MapflowProject):
        self.app_context.project_id = project.id
        self.app_context.current_project = project
        self.apply_project_aoi_area_limit(project)
        if project.shareProject:
            self.app_context.user_role = project.shareProject.get_user_role(self.app_context.username)
        else:
            self.app_context.user_role = UserRole.owner

    def apply_project_aoi_area_limit(self, project: Optional[MapflowProject]):
        """Set the AOI area limit (sq.km) from the open project's owner (``user.aoiAreaLimit``,
        sq.m), or None when there is no project / limit. For a shared project this is the owner's
        limit — the one that actually applies — not the logged-in user's default-project limit."""
        user = project.user if project else None
        limit = user.aoiAreaLimit if user else None
        self.app_context.aoi_area_limit = limit * 1e-6 if limit is not None else None

    def create_project(self, project: CreateProjectSchema):
        self.api.create_project(project, self.create_project_callback)

    def create_project_callback(self, response: QNetworkReply):
        project = MapflowProject.from_dict(json.loads(response.readAll().data()))
        self.set_current_project(project)
        self.get_projects()

    def delete_project(self, project_id):
        # The list renumbers when this returns, so nothing may be selected until it does.
        self.selectionLocked.emit(True)
        self.api.delete_project(project_id, self.delete_project_callback)

    def delete_project_callback(self, response: QNetworkReply):
        self.projects_data.total += -1
        self.get_projects()

    def update_project(self, project_id, project: UpdateProjectSchema):
        self.api.update_project(project_id, project, self.update_project_callback)

    def update_project_callback(self, response: QNetworkReply):
        project = MapflowProject.from_dict(json.loads(response.readAll().data()))
        self.set_current_project(project)
        self.get_projects()

    def get_project(self, project_id, callback: Callable, error_handler: Callable, error_handler_kwargs: dict):
        self.api.get_project(project_id, callback, error_handler, error_handler_kwargs)

    def get_project_callback(self, response: QNetworkReply):
        self.app_context.current_project = MapflowProject.from_dict(json.loads(response.readAll().data()))
        self.apply_project_aoi_area_limit(self.app_context.current_project)
        if self.app_context.current_project:
            self.app_context.project_id = self.app_context.current_project.id
            self.currentProjectChanged.emit(self.app_context.current_project)
        self.get_project_sharing()
        self.setup_project_change_rights()
        self.app_context.settings.setValue("project_id", self.app_context.project_id)
        # Manually toggle function to avoid race condition
        # TODO: Can we avoid this? Calling the function from here is ugly
        self.area_calculator_service.calculate_aoi_area_use_image_extent()

    def get_project_error_handler(self, response: QNetworkReply, **kwargs):
        pass

    @staticmethod
    def sort_combo_index(sort_by, sort_order) -> int:
        """The sort combo's index for a stored (sort_by, sort_order) pair.

        The combo pairs each field with both directions, so neither value alone identifies a row —
        the index is the single element common to the field's pair and the direction's triple.
        `ProjectView.sort_projects` is the inverse.
        """
        if sort_by == ProjectSortBy.name:
            by = (0, 1)
        elif sort_by == ProjectSortBy.created:
            by = (2, 3)
        else:  # ProjectSortBy.updated
            by = (4, 5)
        if sort_order == ProjectSortOrder.ascending:  # A-Z, Oldest first, Updated long ago
            order = (0, 3, 5)
        else:  # descending: Z-A, Newest first, Updated recently
            order = (1, 2, 4)
        return set(by).intersection(set(order)).pop()

    def saved_projects_page(self) -> dict:
        """The page, sort and filter last left behind, so the user returns where they were."""
        return self.app_context.settings.value('projectsPage',
                                               {'offset': self.projects_page_offset,
                                                'sort_by': ProjectSortBy.updated,
                                                'sort_order': ProjectSortOrder.descending,
                                                'filter': ""})

    def get_projects(self,
                     sort_by=ProjectSortBy.updated,
                     sort_order=ProjectSortOrder.descending,
                     projects_filter: str = "",
                     offset: Optional[int] = None):
        """Request a page of projects. Sorting and filtering come from the panel, so the caller
        reads them and passes them in; `offset` is for restoring a remembered page."""
        if offset is not None:
            self.projects_page_offset = offset
        try:  # if something changed and offset is now >= projects count
            if self.projects_page_offset >= self.projects_data.total:
                self.projects_page_offset = 0  # show first page
        except AttributeError:
            pass  # if projects is an empty dict
        self._last_filter = projects_filter
        request_body = ProjectsRequest(self.projects_page_limit,
                                       self.projects_page_offset,
                                       projects_filter,
                                       sort_by, sort_order)
        self.api.get_projects(request_body, self.get_projects_callback)
        # Forbid clicking on pages controls before getting a response
        self.pagerChanged.emit(False, 1, 1)
        self.selectionLocked.emit(True)

    def get_projects_callback(self, response: QNetworkReply):
        self.projects_data = ProjectsResult.from_dict(json.loads(response.readAll().data()))
        self.projects = {project.id: project for project in self.projects_data.results}
        self.projectsLoaded.emit(self.projects_data.results)
        # En(dis)able page controls based on total, limit and offset
        if self.projects_data.total > self.projects_page_limit:
            quotient, remainder = divmod(self.projects_data.total, self.projects_page_limit)
            projects_total_pages = quotient + (remainder > 0)
            projects_page_number = int(self.projects_page_offset / self.projects_page_limit) + 1
            self.pagerChanged.emit(True, projects_page_number, projects_total_pages)
        elif not self.projects_data.total and len(self._last_filter) <= 1:
            # No projects and no filter to explain it — every account has at least 'Default', so
            # this is a stale page rather than an empty account. Ask for the first page unfiltered.
            self.get_projects()
            return
        else:  # total is just less than the limit
            self.pagerChanged.emit(False, 1, 1)
        self.projectsUpdated.emit()
        self.selectionLocked.emit(False)

    # The offset is this service's state, but re-requesting needs the panel's sort and filter —
    # so these move the cursor and the caller asks for the page.

    def to_next_page(self) -> None:
        self.projects_page_offset += self.projects_page_limit

    def to_previous_page(self) -> None:
        self.projects_page_offset += -self.projects_page_limit

    def to_first_page(self) -> None:
        """The filter text changed, so whichever page the user was on no longer means anything."""
        self.projects_page_offset = 0
        self.app_context.project_id = None

    # ========== Projects ========== #

    def on_project_change(self, selected_id):
        """A row was selected in the projects table (or the selection was cleared).

        ``selected_id`` is read from the table by the caller — a service may not read a widget.
        """
        if selected_id is not None and selected_id == self.app_context.project_id \
                and self.app_context.workflow_defs:
            # we look at workflow defs because if they are NOT initialized, it means that the project
            # is not initialized yet (at plugin's startup) and we still need to set it up
            # otherwise, if the WDs are set, we assume that the project hasn't changed and skip further setup
            return
        if selected_id is None:
            self.app_context.current_project = self.app_context.project_id = None
            self.apply_project_aoi_area_limit(None)  # no project open -> no AOI area limit
            self.app_context.settings.setValue("project_id", None)
            self.setup_project_change_rights()
            self.windowTitleChanged.emit(
                helpers.generate_plugin_header(self.app_context.plugin_name,
                                               env=self.config.MAPFLOW_ENV))
            self.currentProjectChanged.emit(None)
            return
        self.app_context.project_id = selected_id
        for pid, project in self.projects.items():
            if selected_id == pid:
                self.app_context.current_project = project
                self.currentProjectChanged.emit(project)
        if self.app_context.current_project:
            self.apply_project_aoi_area_limit(self.app_context.current_project)
            self.get_project_sharing()
        self.setup_project_change_rights()
        self.app_context.settings.setValue("project_id", self.app_context.project_id)

        # Manually toggle function to avoid race condition
        # TODO: Can we avoid this? Calling the function from here is ugly
        self.area_calculator_service.calculate_aoi_area_use_image_extent()

    def setup_project_change_rights(self):
        project_editable = True
        if not self.app_context.current_project:
            project_editable = False
            reason = self.tr("No project selected")
        elif self.app_context.current_project.isDefault:
            reason = self.tr("You can't remove or modify default project")
            project_editable = False
        elif not self.app_context.user_role.can_delete_rename_project:
            reason = self.tr('Not enough rights to delete or update shared project ({})').format(
                self.app_context.user_role.value)
        else:
            reason = ""
        self.projectChangeRightsChanged.emit(
            reason, project_editable and self.app_context.user_role.can_delete_rename_project)

    def update_projects(self, name_filter: str = ""):
        self.filter_projects(name_filter)

    def filter_projects(self, name_filter):
        if not name_filter:
            filtered_projects = self.projects
        else:
            filtered_projects = {pid: p for pid, p in self.projects.items() if name_filter.lower() in p.name.lower()}
        if self.app_context.project_id in self.projects \
                and self.app_context.project_id not in filtered_projects:
            # We maintain the current project in the combo even if it not found to prevent over-requesting
            # until it is changed explicitly
            filtered_projects.update({self.app_context.project_id: self.projects[self.app_context.project_id]})
        self.projectsFiltered.emit()

    def get_project_sharing(self):
        if not self.app_context.current_project:
            return
        if self.app_context.current_project.shareProject:
            # Get user role, if project is shared
            self.app_context.user_role = self.app_context.current_project.shareProject.get_user_role(
                self.app_context.username)
            project_owner = self.app_context.current_project.shareProject.owners[0].email
            self.sharedRoleApplied.emit(self.app_context.user_role)
        else:
            self.app_context.user_role = UserRole.owner
            project_owner = self.app_context.username
        self.windowTitleChanged.emit(
            helpers.generate_plugin_header(self.app_context.plugin_name,
                                           env=self.config.MAPFLOW_ENV,
                                           project_name=self.app_context.current_project.name,
                                           user_role=self.app_context.user_role,
                                           project_owner=project_owner))
