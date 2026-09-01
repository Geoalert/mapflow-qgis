from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMessageBox, QWidget

from ..app_context import AppContext
from ..service.alert_service import alert
from ..service.processing_service import ProcessingService
from ..service.project_service import ProjectService
from ...config import config
from ...dialogs import CreateProjectDialog, UpdateProjectDialog, MainDialog, UpdateProcessingDialog
from ...dialogs.processing_details_dialog import ProcessingDetailsDialog
from ...schema import ImagerySearchParams, MyImageryParams, UserDefinedParams
from ...schema.project import UserRole


class ProjectProcessingController(QObject):
    """
    Controller that coordinates navigation and interactions between
    Projects and Processings views.

    Responsibilities:
    - Wire UI events to service methods
    - Handle navigation between projects and processings views
    - Connect signals between services
    - Own what the processings table offers for the current selection: its context menu, the
      Delete button, and the details dialog
    """

    def __init__(self, dlg: MainDialog,
                 processing_service: ProcessingService,
                 project_service: ProjectService,
                 template_service,
                 app_context: AppContext,
                 aoi_service=None,
                 data_catalog_service=None,
                 result_loader=None,
                 processing_view=None):
        super().__init__()
        self.dlg = dlg
        self.processing_service = processing_service
        self.project_service = project_service
        #: Subscribed to for "the table needs refreshing" after a template action, and asked which
        #: view the table is showing — that choice is this controller's region.
        self.template_service = template_service
        self.app_context = app_context
        #: Read for `session_active`: no AOI action may start while another edit/draw session runs.
        self.aoi_service = aoi_service
        #: The two other places a processing's imagery source can be reopened from.
        self.data_catalog_service = data_catalog_service
        self.result_loader = result_loader
        self.processing_view = processing_view

        self._setup_processing_bindings()
        self._setup_project_bindings()
        self._setup_navigation()

        self.project_connection = None
    
    def _setup_processing_bindings(self):
        """Processing-specific UI connections."""
        self.dlg.startProcessing.clicked.connect(self.processing_service.start_processing)
        self.dlg.processing_update_action.triggered.connect(self.update_processing)
        self.dlg.options_menu.aboutToShow.connect(self.update_processing_options_menu)
        self.dlg.see_details_action.triggered.connect(self.show_selected_details)
        # The Delete button follows the selection for a contributor. `ProcessingController`
        # subscribes to this same signal for the Start button: two regions reading one widget
        # signal, rather than one controller calling the other (`spec/007_architecture.md`).
        self.dlg.processingsTable.itemSelectionChanged.connect(self.update_delete_button_state)
        # The poll tick, and every action that wants the table refreshed, come here rather than
        # going straight to a service: the table serves two views and picking between them is
        # navigation, which is this controller's region.
        self.processing_service.processing_fetch_timer.timeout.connect(self.refresh_table)
        self.processing_service.refreshRequested.connect(self.refresh_table)
        self.processing_service.rerenderRequested.connect(self.rerender_rows)
        self.processing_service.templateRehydrateRequested.connect(self.rehydrate_template)
        self.template_service.refreshRequested.connect(self.refresh_table)
        # The in-template view holds no widget and owns no timer, so its rebuilt rows and its
        # slower poll cadence arrive here to be applied.
        self.template_service.templateRowsChanged.connect(
            self.processing_service.view.update_processing_table)
        self.template_service.pollIntervalChanged.connect(self._set_poll_interval)
        # `ProcessingService` turns a table selection into objects, so it needs to know which view
        # the table is showing — but it must not reach into `TemplateService` to find out. The
        # answer is pushed to it from here, which is the region that owns the choice.
        self.template_service.templateOpened.connect(self.processing_service.set_open_template)
        self.template_service.templateClosed.connect(self._on_template_closed)
        self.template_service.visibleProcessingsChanged.connect(
            self.processing_service.set_visible_processings)

    def _on_template_closed(self, _closed=None):
        """`templateClosed` carries the template that was closed, so it cannot be connected to
        `set_open_template` directly — 'closed' has to arrive as None."""
        self.processing_service.set_open_template(None)

    # ==== WHICH VIEW THE PROCESSINGS TABLE IS SHOWING ==== #
    #
    # One table, two views: the project's processings+templates, or an open template's
    # AOIs+processings. Both services would otherwise have to ask each other which is showing —
    # `ProcessingService` needing `TemplateService` and vice versa — so the choice lives here
    # instead, the way `SearchService` already leaves regular-vs-template search to a controller.

    def refresh_table(self):
        """Re-fetch whatever the table is showing."""
        if self.template_service.in_template_mode:
            self.template_service.refresh_template_view()
        else:
            self.processing_service.get_processings()

    def rerender_rows(self):
        """Re-render the rows already held, for a sort that needs no request."""
        if self.template_service.in_template_mode:
            rows = self.template_service.combined_template_rows()
        else:
            rows = self.processing_service.combined_processing_rows()
        self.processing_service.view.update_processing_table(rows)

    def rehydrate_template(self):
        """A processing was started inside a template: re-hydrate so it binds to its AOI."""
        self.template_service.refresh_active_template()

    def _set_poll_interval(self, interval_ms: int):
        """Apply a view's poll cadence: the in-template view polls slower than the project list.
        The timer belongs to `ProcessingService`, so the service that wants the change asks."""
        self.processing_service.processing_fetch_timer.setInterval(interval_ms)
        self.processing_service.processing_fetch_timer.start()
    
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
        # Entering a template is async when its aoiDetails must be fetched (the project poll
        # omits them), so `in_template_mode` flips only in the hydrate callback. Refresh the nav
        # buttons on the actual open/close signals — otherwise the "enter template" arrow stays
        # enabled until the next selection change.
        self.template_service.templateOpened.connect(self._update_nav_buttons)
        self.template_service.templateClosed.connect(self._update_nav_buttons)
        self._update_nav_buttons()

    def _on_project_double_clicked(self, index):
        """Handle double-click on project row to navigate to processings."""
        project_id = self.dlg.projectsTable.item(index.row(), 0).text()
        self.app_context.current_project = self.project_service.projects.get(project_id)
        self.show_processings(save_page=True)

    # ==== IN-TEMPLATE NAVIGATION ==== #
    def navigate_back(self):
        """Left arrow: leave a template (back to processings) or go back to projects."""
        if self.template_service.in_template_mode:
            self.exit_template()
        else:
            self.show_projects(open_saved_page=True)

    def navigate_into_template(self):
        """Right arrow: enter the currently selected template."""
        if self.template_service.in_template_mode:
            return
        template = self.processing_service.selected_template()
        if not template or not self.processing_service.is_only_templates_selected():
            return
        self.enter_template(template)

    def enter_template(self, template):
        """Enter the in-template view for the given template."""
        self.template_service.enter_template_view(template)
        self._set_processings_tab_text(str(template.name))
        self._update_nav_buttons()

    def exit_template(self):
        """Return from the in-template view to the project's processings list."""
        self.template_service.exit_template_view()
        self.processing_service.setup_processings_table()
        self._set_processings_tab_text(self.tr("Processing"))
        self._update_nav_buttons()

    MAX_TAB_TEXT_LENGTH = 15

    def _set_processings_tab_text(self, text: str):
        """Set the processings tab label (a breadcrumb for the template name). Long template names
        are truncated with an ellipsis so the tab stays a sane width; the full name is kept as the
        tab's tooltip."""
        processings_tab = self.dlg.tabWidget.findChild(QWidget, "processingsTab")
        if processings_tab is None:
            return
        tab_index = self.dlg.tabWidget.indexOf(processings_tab)
        if tab_index < 0:
            return
        label = text if len(text) <= self.MAX_TAB_TEXT_LENGTH \
            else text[:self.MAX_TAB_TEXT_LENGTH - 1] + "…"
        self.dlg.tabWidget.setTabText(tab_index, label)
        self.dlg.tabWidget.setTabToolTip(tab_index, text)

    def _update_nav_buttons(self, *args):
        """Enable the 'enter template' arrow only for a single-template selection.

        Accepts optional signal arguments (``templateOpened``/``templateClosed`` emit the
        template object) so it can be wired directly to those signals."""
        in_template = self.template_service.in_template_mode
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

    # ==== WHAT THE TABLE OFFERS FOR THE CURRENT SELECTION ==== #

    def update_processing_options_menu(self):
        """Render processing options menu depending on selected row type."""
        menu = self.dlg.options_menu
        menu.clear()

        selected_template = self.processing_service.selected_template()
        selected_processing = self.processing_service.selected_processing()

        # In-template view: AOI add/rename/delete (only for AOI rows / empty selection;
        # a selected processing row falls through to the normal processing actions below).
        if self.template_service.in_template_mode and not selected_processing:
            can_edit = self.app_context.can_edit_template(self.template_service.active_template)
            selected_aoi = self.template_service.selected_aoi()
            # No AOI action can start while another edit/draw session is running.
            no_session = not self.aoi_service.session_active
            if selected_aoi:
                self.dlg.aoi_rename_action.setEnabled(can_edit and selected_aoi.can_rename)
                menu.addAction(self.dlg.aoi_rename_action)
                self.dlg.aoi_delete_action.setEnabled(can_edit and selected_aoi.can_rename)
                menu.addAction(self.dlg.aoi_delete_action)
                # Edit the selected AOI's geometry on the map (vertex editing, in place).
                self.dlg.aoi_update_geometry_action.setEnabled(
                    can_edit and selected_aoi.can_rename and no_session)
                menu.addAction(self.dlg.aoi_update_geometry_action)
            self.dlg.aoi_add_action.setEnabled(can_edit and no_session)
            menu.addAction(self.dlg.aoi_add_action)
            self.dlg.aoi_draw_action.setEnabled(can_edit and no_session)
            menu.addAction(self.dlg.aoi_draw_action)
            return

        # In-template view, a processing row is backed by the v1 TemplateProcessingSchema
        # (flat params, no ProcessingParams) — offer only the read-only result actions, not
        # restart/duplicate which need v2 source params.
        if self.template_service.in_template_mode and selected_processing:
            menu.addAction(self.dlg.save_result_action)
            menu.addAction(self.dlg.see_details_action)
            # Subtract this processing's already-processed area from the template's AOIs (feature 3).
            # This edits the open template's geometry, so it follows template-edit rights.
            if self.app_context.can_edit_template(self.template_service.active_template):
                menu.addAction(self.dlg.exclude_from_search_action)
            return

        # Template selection: only template details action.
        if selected_template and not selected_processing:
            menu.addAction(self.dlg.see_details_action)
            menu.addAction(self.dlg.see_search_results_action)
            menu.addAction(self.dlg.see_processings_action)
            # A contributor may edit/control their OWN templates; maintainer+ may edit any.
            can_edit_template = self.app_context.can_edit_template(selected_template)
            if can_edit_template:
                menu.addAction(self.dlg.template_rename_action)
                # NB: "Update search parameters" is offered only from *inside* the template
                # (below), where the filter widgets reflect the template (populated on open).
                # In this project-list selection they hold unrelated values, so it is not shown.
            # Add pause/resume/restart based on template status. Run-state control follows the
            # same template-edit rights (maintainer+, or a contributor on their own template).
            can_control = can_edit_template
            # A FAILED template can still be isActive, so check FAILED first (mirrors
            # ProcessingTemplateDTO.table_status precedence): it offers Restart, not Pause.
            if selected_template.is_failed:
                self.dlg.template_restart_action.setEnabled(can_control)
                menu.addAction(self.dlg.template_restart_action)
            elif selected_template.isActive:
                self.dlg.template_pause_action.setEnabled(can_control)
                menu.addAction(self.dlg.template_pause_action)
            else:
                self.dlg.template_resume_action.setEnabled(can_control)
                menu.addAction(self.dlg.template_resume_action)
            return

        # Processing selection: show processing-related actions.
        if not selected_processing:
            return

        menu.addAction(self.dlg.save_result_action)
        menu.addAction(self.dlg.download_aoi_action)
        menu.addAction(self.dlg.see_details_action)

        if self.app_context.user_role.can_delete_rename_review_processing:
            menu.addAction(self.dlg.processing_update_action)

        if self.app_context.user_role.can_start_processing:
            menu.addAction(self.dlg.processing_restart_action)
            menu.addAction(self.dlg.processing_duplicate_action)

    def update_delete_button_state(self, *args):
        """Contributor-only: the Delete button follows the selection — enabled only when every
        selected row is a template the contributor owns (they may delete their own templates but
        never a processing). Other roles keep the fixed, role-based state from
        ``enable_shared_project``, so this leaves them untouched."""
        if self.app_context.user_role != UserRole.contributor:
            return
        can_delete = self.processing_service.all_selected_templates_editable()
        self.dlg.deleteProcessings.setEnabled(can_delete)
        self.dlg.deleteProcessings.setToolTip(
            "" if can_delete
            else self.tr("Contributors can only delete their own planned processings"))

    # ==== THE DETAILS DIALOG ==== #

    def show_selected_details(self, *args):
        """Open details based on selected entity type."""
        template = self.processing_service.selected_template()
        if template and not self.processing_service.selected_processing():
            self.template_service.show_template_details(template)
            return
        self.show_details()

    def show_details(self):
        processing = self.processing_service.selected_processing()
        if not processing:
            return
        error = None
        if processing.messages:
            error = processing.error_message(raw=config.SHOW_RAW_ERROR)
        dialog = ProcessingDetailsDialog(self.dlg)
        dialog.toSourceButton.clicked.connect(
            lambda: self.show_processing_source(processing=processing, window=dialog))
        dialog.setup(processing, error or None)
        dialog.deleteLater()

    def show_processing_source(self, processing, window) -> None:
        """'Go to source' on the details dialog: reopen whatever imagery the processing ran on.
        Where that lives depends on the source, which is why the fork is here rather than in any
        one of the three regions it dispatches to."""
        source_params = processing.params.sourceParams
        if isinstance(source_params, ImagerySearchParams):
            # The search table is filled from the AOI, so the download has to finish first.
            self.result_loader.download_aoi_file(
                pid=processing.id, callback=self.processing_service.duplicate_aoi_callback)
        elif isinstance(source_params, MyImageryParams):
            self.data_catalog_service.show_my_imagery_source(source_params)
        elif isinstance(source_params, UserDefinedParams):
            alert(self.processing_view.show_user_provider_info(source_params),
                  icon=QMessageBox.Information)
        window.close()

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
