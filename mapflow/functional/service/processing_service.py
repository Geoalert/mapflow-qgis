import json
from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Dict, Optional, List
from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtNetwork import QNetworkReply
from PyQt5.QtWidgets import QMessageBox, QApplication, QInputDialog
from .provider_service import (get_provider_params, 
                               setup_provider_info, 
                               validate_provider_params, 
                               duplicate_aoi_based_on_provider,
                               duplicate_provider_and_model)
                               
from .. import helpers
from ...dialogs.main_dialog import MainDialog
from ...dialogs.confirm_processing_start_dialog import ConfirmProcessingStartDialog
from ...errors import (BadProcessingInput,
                       ErrorMessage,
                       PluginError,
                       ImageIdRequired,
                       AoiNotIntersectsImage)
from ...http import Http, api_message_parser
from ..view.processing_view import ProcessingView
from ..api.processing_api import ProcessingApi
from ...schema import ProcessingDTO, UpdateProcessingSchema, ProcessingStatus, BillingType, ProcessingHistory, PostProcessingSchemaV2
from ...schema.processing import (
    ProcessingsRequest,
    ProcessingsResult,
    RunTemplateProcessingSchema,
    UpdateProcessingTemplateSchema,
)
from ...schema.processing import ProcessingTemplateDTO
from ..service.alert_service import alert
from ..app_context import AppContext
from ...entity.provider import ImagerySearchProvider
from ...config import Config
from ...functional.layer_utils import ResultsLoader
from ...http import get_error_report_body
from ...dialogs.error_message_widget import ErrorMessageWidget

class ProcessingService(QObject):
    """
    A service to store & query the mapflow processings.
    """

    def __init__(self,
                 http: Http,
                 dlg: MainDialog,
                 iface,
                 result_loader: ResultsLoader,
                 app_context: AppContext,
                 timer_interval):
        super().__init__()
        self.http = http
        self.dlg = dlg
        self.iface = iface
        self.result_loader = result_loader
        self.app_context = app_context
        self.view = ProcessingView(dlg=dlg)
        self.api = ProcessingApi(http=http,
                                 dlg=dlg,
                                 iface=iface,
                                 result_loader=self.result_loader)
        self.processings = {}
        self.templates = {}
        self.processings_data = None  # ProcessingsResult
        self.processings_page_limit = Config.PROCESSINGS_PAGE_LIMIT
        self.processings_page_offset = 0
        self.processings_history = None # ProcessingHistory() - local storage for active processings list
        self.processing_fetch_timer = QTimer(dlg)
        self.processing_fetch_timer.setInterval(timer_interval)
        self.processing_cost = 0
        self._delete_state = {}  # Store state for template deletion callback
        self._resume_template_state = {}

    def load_processing_history(self):
        """
        Loads processing history to set up the notifications after the processings are fetched
        """
        # Update processing history context for the new project
        if self.app_context.current_project:
            try:
                self.processings_history = ProcessingHistory.from_settings(
                    self.app_context.settings, UUID(self.app_context.current_project.id)
                )
            except (ValueError, KeyError):
                # If no history exists for this project, create new one
                self.processings_history = ProcessingHistory(project_id=UUID(self.app_context.current_project.id))

        # Optionally refresh processings for the new project
        # self.get_processings()  # Uncomment when this method is implemented

    # ================  CREATE  ====================== #
    def validate_processing_params(self, processing_params, allow_empty_name: bool = False):
        error = None
        disable_start = True

        if not processing_params:
            error = self.tr("Specify processing parameters")
            return error, disable_start
        
        try:
            if not processing_params.name and not allow_empty_name:
                error = self.tr('Please, specify a name for your processing')
                alert(error)
                disable_start = False
            if not self.app_context.aoi:
                if self.dlg.polygonCombo.currentLayer():
                    raise BadProcessingInput(self.tr('Processing area layer is corrupted or has invalid projection'))
                else:
                    raise BadProcessingInput(self.tr('Please, select a valid area of interest'))
            if self.app_context.aoi_area_limit < self.app_context.aoi_size:
                raise BadProcessingInput(self.tr(
                    'Up to {} sq km can be processed at a time. '
                    'Try splitting your area(s) into several processings.').format(self.app_context.aoi_area_limit))
            min_area, provider_name = self._selected_search_min_area()
            if min_area is not None and self.app_context.aoi_size is not None \
                    and self.app_context.aoi_size < min_area:
                # Intersection of the AOI with the selected image is below the provider's
                # minimum: reject client-side so we never send the cost/start request.
                raise BadProcessingInput(ErrorMessage(
                    code="ProviderMinAreaError",
                    parameters={
                        "aoiArea": round(self.app_context.aoi_size, 2),
                        "providerName": provider_name or self.tr("the selected"),
                        "providerMinArea": round(min_area, 2),
                    },
                ).to_str())
        except AoiNotIntersectsImage:
            error = self.tr("Selected AOI does not intersect the selected imagery")
        except ImageIdRequired:
            error = self.tr("This provider requires image ID. Use search tab to find imagery for you requirements, "
                            "and select image in the table.")
        except PluginError as e:
            error = str(e)
        return error, disable_start

    def _selected_search_min_area(self):
        """Provider minimum AOI area for the currently selected search image(s).

        The minimum lives on the provider (from ``/user/status``, see
        ``app_context.provider_min_areas``); the selected footprints supply the
        ``providerName`` to look it up. Returns ``(min_area_sqkm, provider_name)`` with the
        most restrictive minimum, or ``(None, None)`` when nothing relevant is selected.
        """
        # Only imagery search ties the AOI to a provider's per-image minimum; for any other
        # provider the metadata-table selection (possibly stale) is irrelevant — bail early.
        if not isinstance(self.app_context.data_provider, ImagerySearchProvider):
            return None, None
        selected = self.dlg.metadataTable.selectedItems()
        if not selected:
            return None, None
        footprints = self.app_context.search_footprints or {}
        provider_min_areas = getattr(self.app_context, "provider_min_areas", None) or {}
        # Track the binding (largest) minimum so the reported provider name matches it.
        binding_min, binding_provider = None, None
        for row in sorted({item.row() for item in selected}):
            index_item = self.dlg.metadataTable.item(row, Config.LOCAL_INDEX_COLUMN)
            if not index_item:
                continue
            try:
                feature = footprints.get(int(index_item.text()))
            except (TypeError, ValueError):
                feature = None
            if feature is None:
                continue
            try:
                name = feature.attribute("providerName")
            except (TypeError, KeyError):
                name = None
            if name in (None, "", "NULL"):
                continue
            min_area = provider_min_areas.get(str(name).lower())
            if min_area is not None and (binding_min is None or min_area > binding_min):
                binding_min, binding_provider = min_area, name
        return binding_min, binding_provider

    def validate_context_params(self):
        error = None
        planned_selection_error = self.planned_processing_selection_error()
        if planned_selection_error:
            return planned_selection_error
        if not self.app_context.aoi:
            # Here the button must already be disabled, and the warning text set
            if self.view.dlg.startProcessing.isEnabled():
                if not self.app_context.user_role.can_start_processing:
                    error = self.tr('Not enough rights to start processing in a shared project ({})').format(self.app_context.user_role.value)
                else:
                    error = self.tr("Set AOI to start processing")
        elif not self.app_context.workflow_defs:
            error = self.tr("Error! Models are not initialized.\n"
                            "Please, make sure you have selected a project")
        elif self.app_context.billing_type != BillingType.credits:
            self.view.dlg.startProcessing.setEnabled(True)
            self.view.dlg.processingProblemsLabel.clear()
            error = None
        return error

    def planned_processing_selection_error(self) -> Optional[str]:
        """Return error when template is selected but no search result images are selected."""
        template = self.selected_template()
        if not template or self.selected_processing():
            return None
        selected_rows = {item.row() for item in self.dlg.metadataTable.selectedItems()}
        if selected_rows:
            return None
        return self.tr("Select one or more images in search results to start planned processing")

    def start_processing(self):
        self.processing_fetch_timer.stop()

        processing_params, error = self.validate_all_processing_params(allow_empty_name=False)
        if error:
            self.dlg.disable_processing_start(error, clear_area=error)
            return
        elif not processing_params: # neither error nor params => return w/o disabling (empty name)
            return
        
        # Check processing limits
        if not self.check_processing_limits():
            return
        
        # Handle confirmation dialog or direct submission
        self.handle_processing_submission(processing_params)

    def check_processing_limits(self) -> bool:
        """
        Check if user has sufficient credits/limits for processing.
        Returns True if limits are sufficient, False otherwise.
        """
        if not helpers.check_processing_limit(
            billing_type=self.app_context.billing_type,
            remaining_limit=self.app_context.remaining_limit,
            remaining_credits=self.app_context.remaining_credits,
            aoi_size=self.app_context.aoi_size,
            processing_cost=self.processing_cost
        ):
            alert(
                self.tr('Processing limit exceeded. '
                    'Visit "<a href=\"https://app.mapflow.ai/account/balance\">Mapflow</a>" '
                    'to top up your balance'),
                icon=QMessageBox.Warning
            )
            return False
        return True
        
    def handle_processing_submission(self, processing_params: PostProcessingSchemaV2):
        """
        Handle the actual processing submission, either directly or after confirmation.
        """
        def post_processing():
            try:
                self.dlg.startProcessing.setEnabled(False)
                template = self.selected_template()
                if template:
                    self.iface.messageBar().pushInfo(
                        self.app_context.plugin_name,
                        self.tr('Starting planned processing...')
                    )
                    self.api.run_template_processing(
                        template_id=template.id,
                        data=self._build_run_template_processing_schema(processing_params),
                        callback=self.start_processing_callback,
                        error_handler=self.start_processing_error_handler,
                    )
                else:
                    self.iface.messageBar().pushInfo(
                        self.app_context.plugin_name,
                        self.tr('Starting the processing...')
                    )
                    self.api.create_processing(
                        processing_params,
                        self.start_processing_callback,
                        self.start_processing_error_handler
                    )
            except Exception as e:
                alert(self.tr("Could not launch processing! Error: {}.").format(str(e)))
        
        # Show confirmation dialog if enabled
        if self.dlg.cornfirmProcessingStart.isChecked():
            self.show_confirmation_dialog(processing_params, post_processing)
        else:
            post_processing()

    def _build_run_template_processing_schema(
        self,
        processing_params: PostProcessingSchemaV2,
    ) -> RunTemplateProcessingSchema:
        wd_id = processing_params.wdId
        wd_name = None if wd_id else self.dlg.modelCombo.currentText()
        return RunTemplateProcessingSchema(
            name=processing_params.name,
            description=processing_params.description,
            wdName=wd_name,
            wdId=wd_id,
            geometry=processing_params.geometry,
            params=processing_params.params,
            meta=processing_params.meta or {},
            blocks=processing_params.blocks or [],
            updateTemplateGeometry=False,
        )

    def show_confirmation_dialog(self, processing_params: PostProcessingSchemaV2, callback):
        """
        Show the processing confirmation dialog with current parameters.
        """
        dialog = ConfirmProcessingStartDialog(self.dlg)
        
        def set_start_confirmation():
            if not dialog.checkBox.isChecked() != self.dlg.cornfirmProcessingStart.isChecked():
                self.dlg.cornfirmProcessingStart.setChecked(not dialog.checkBox.isChecked())
                self.app_context.settings.setValue(
                    "confirmProcessingStart", 
                    str(not dialog.checkBox.isChecked())
                )
        
        dialog.checkBox.toggled.connect(set_start_confirmation)
        dialog.accepted.connect(callback)
        
        # Prepare dialog parameters
        price = self.tr("{cost} credits").format(cost=self.processing_cost) if self.app_context.billing_type == BillingType.credits else None
        
        ui_start_params = self.view.read_processing_start_params()
        
        dialog.setup(
            name=processing_params.name,
            price=price,
            provider=setup_provider_info(self.app_context.data_provider),
            zoom=str(ui_start_params.zoom),
            area=str(round(self.app_context.aoi_size, 2)) + self.tr(" sq.km"),
            model=self.dlg.modelCombo.currentText(),
            blocks=[self.dlg.modelOptionsLayout.itemAt(i).widget()
                    for i in range(self.dlg.modelOptionsLayout.count())]
        )
        dialog.deleteLater()
        
    def get_processing_schema(self, ui_start_params, provider):
        if not provider or not self.app_context.aoi:
            return None
        
        wd = self.app_context.get_workflow_def(ui_start_params.wd_name)
        if not wd:
            return None
        if len(wd.blocks) > 0 and len(self.dlg.modelOptions) == 0:
            # Wait till options are added and this function is  re-called
            blocks = []
        else:
            blocks = wd.get_enabled_blocks(self.dlg.enabled_blocks())

        provider_params, processing_meta = get_provider_params(provider=provider,
                                                               zoom=ui_start_params.zoom)
        
        processing_params = PostProcessingSchemaV2(
            name=ui_start_params.name,
            description=None,
            projectId=self.app_context.project_id,
            wdId=wd.id,
            geometry=json.loads(self.app_context.aoi.asJson()),
            params=provider_params,
            meta=processing_meta,
            blocks=blocks)

        return processing_params

    def start_processing_callback(self, response: QNetworkReply) -> None:
        """Display a success message and clear the processing name field."""
        alert(
            self.tr("Success! We'll notify you when the processing has finished."),
            QMessageBox.Information
        )
        response_data = json.loads(response.readAll().data())
        new_processing = None
        # Template start responses may differ from processing-create responses.
        # Try optimistic local update only when payload looks like a Processing DTO.
        if isinstance(response_data, dict) and response_data.get("id") and response_data.get("name"):
            new_processing = ProcessingDTO.from_dict(response_data)
            self.view.clear_processing_name(new_processing.name)
        self.processing_fetch_timer.start()  # start monitoring
        if new_processing is not None:
            # Add to history
            self.processings[new_processing.id] = new_processing
            self.processings_history.add(new_processing.id, new_processing.status)
            # display
            self.view.add_new_processing(new_processing)
        # Always refresh full list because template-started processings can affect
        # both processings and template status/counts in table.
        self.get_processings()
        self.dlg.startProcessing.setEnabled(True)

    def start_processing_error_handler(self, response: QNetworkReply) -> None:        
        """Error handler for processing creation requests.

        :param response: The HTTP response.
        """
        error = response.error()
        response_body = response.readAll().data().decode()
        if error == QNetworkReply.ContentAccessDenied \
                and "data provider" in response_body.lower():
            alert(self.tr('The selected data provider is unavailable on your plan. \n '
                          'Upgrade your subscription to get access to the data. \n'
                          'See pricing at <a href=\"https://mapflow.ai/pricing\">mapflow.ai</a>'),
                       QMessageBox.Information)
            # provider ID is the last "word" in the message.
            # In this case, when "data provider" is in the message, there can't be index error
        else:
            error_summary, email_body = get_error_report_body(response=response,
                                                              response_body=response_body,
                                                              plugin_version=self.app_context.plugin_version,
                                                              error_message_parser=api_message_parser)
            ErrorMessageWidget(parent=QApplication.activeWindow(),
                               text= error_summary,
                               title=self.tr('Processing creation failed'),
                               email_body=email_body).show()
        if not False in self.app_context.allow_enable_processing.values():
            self.dlg.startProcessing.setEnabled(True)

    # =============  REQUEST ================= #
    def setup_processings_table(self):
        if not self.app_context.current_project:
            return
        self.processings_page_offset = 0
        self.view.set_table_loading()
        self.get_processings()
        self.processing_fetch_timer.start()

    def connect_processings_pagination(self):
        """Connect pagination, sorting and filtering signals. Called once during plugin init."""
        self.dlg.processingsNextPageButton.clicked.connect(self.show_processings_next_page)
        self.dlg.processingsPreviousPageButton.clicked.connect(self.show_processings_previous_page)
        self.dlg.filterProcessings.textEdited.connect(self.get_filtered_processings)
        self.dlg.sortProcessingsCombo.activated.connect(self._on_combo_sort_changed)
        self.view.connect_header_sort(self._on_header_sort_changed)

    def _on_combo_sort_changed(self):
        """Combo sort resets any header-click override and re-fetches."""
        self.view._header_sort_by = None
        self.get_processings()

    def _on_header_sort_changed(self):
        """Re-render the table with current data using the header sort."""
        self.view.update_processing_table(self.combined_processing_rows())

    def get_processings(self):
        if not self.app_context.current_project:
            return
        # Clamp offset if it exceeds total
        try:
            if self.processings_data and self.processings_page_offset >= self.processings_data.total:
                self.processings_page_offset = 0
        except (AttributeError, TypeError):
            pass
        sort_by, sort_order = self.view.sort_processings()
        terms = self.dlg.filterProcessings.text() or None
        request_body = ProcessingsRequest(
            limit=self.processings_page_limit,
            offset=self.processings_page_offset,
            terms=terms,
            sortBy=sort_by,
            sortOrder=sort_order,
        )
        self.api.get_processings(
            project_id=self.app_context.current_project.id,
            request_body=request_body,
            callback=self.get_processings_callback,
        )
        self.view.enable_processings_pages(False)

    def get_processings_callback(self, response: QNetworkReply):
        """Update the processing table and user limit.

        :param response: The HTTP response.
        """
        response_data = json.loads(response.readAll().data())
        self.processings_data = ProcessingsResult.from_dict(response_data)
        processings = self.processings_data.results
        if all(p.is_final_state for p in processings):
            self.processing_fetch_timer.stop()
        self.processings = {processing.id: processing for processing in processings}
        # Update pagination UI
        if self.processings_data.total > self.processings_page_limit:
            quotient, remainder = divmod(self.processings_data.total, self.processings_page_limit)
            total_pages = quotient + (remainder > 0)
            page_number = int(self.processings_page_offset / self.processings_page_limit) + 1
            self.view.show_processings_pages(True, page_number, total_pages)
        else:
            self.view.show_processings_pages(False)
        self.update_local_processings(processings)
        current_project_id = getattr(self.app_context.current_project, "id", None)
        if current_project_id:
            self.api.get_templates_by_project(
                project_id=current_project_id,
                callback=self.get_templates_callback,
            )
        else:
            self.templates = {}
            self.view.update_processing_table(self.combined_processing_rows())

    def get_templates_callback(self, response: QNetworkReply):
        """Build templates from the project-scoped list.

        The project endpoint omits ``searchParams``; they are hydrated lazily when a
        template is opened (see ``Mapflow._open_template``). Keeping the poll to this
        single request avoids a second full-list fetch on every tick.
        """
        response_data = json.loads(response.readAll().data())
        if isinstance(response_data, dict):
            template_items = response_data.get("templates") or response_data.get("results") or []
        else:
            template_items = response_data or []
        self._set_templates_from_items(template_items)

    def _set_templates_from_items(self, template_items):
        """Build and render template DTOs from raw template item list."""

        current_project_id = str(getattr(self.app_context.current_project, "id", ""))
        templates = []
        for item in template_items:
            if not isinstance(item, dict):
                continue
            normalized_item = dict(item)
            normalized_item.setdefault("searchParams", {})
            try:
                template = ProcessingTemplateDTO.from_dict(normalized_item)
            except (TypeError, ValueError, KeyError):
                continue
            if current_project_id and str(template.projectId) != current_project_id:
                continue
            templates.append(template)

        self.templates = {template.id: template for template in templates}
        self.view.update_processing_table(self.combined_processing_rows())

    def _sort_key(self, item, sort_by: str):
        is_processing = isinstance(item, ProcessingDTO)
        if sort_by == "NAME":
            return (item.name or "").lower()
        if sort_by == "WORKFLOW":
            return (item.workflowDef.name if is_processing else "Planned").lower()
        if sort_by == "STATUS":
            if is_processing:
                if item.reviewStatus and not item.reviewStatus.is_none:
                    return (item.reviewStatus.reviewStatus.display_value or "").lower()
                return (item.status.display_value or "").lower()
            return item.table_status.lower()
        if sort_by == "PROGRESS":
            return (item.percentCompleted or 0) if is_processing else -1
        if sort_by == "AREA":
            return (item.aoiArea or 0) if is_processing else (item.aoi_area or 0)
        if sort_by == "COST":
            return (item.cost or 0) if is_processing else 0
        if sort_by == "REVIEW_UNTIL":
            if is_processing and item.reviewUntil:
                return item.reviewUntil
            return datetime.min.replace(tzinfo=timezone.utc)
        # CREATED (default)
        return item.created if is_processing else item.createdAt

    def combined_processing_rows(self):
        sort_by, sort_order = self.view.sort_processings()
        reverse = sort_order == "DESC"
        templates = sorted(self.templates.values(), key=lambda t: self._sort_key(t, sort_by), reverse=reverse)
        processings = sorted(self.processings.values(), key=lambda p: self._sort_key(p, sort_by), reverse=reverse)
        return list(templates) + list(processings)

    def show_processings_next_page(self):
        self.processings_page_offset += self.processings_page_limit
        self.get_processings()

    def show_processings_previous_page(self):
        self.processings_page_offset -= self.processings_page_limit
        if self.processings_page_offset < 0:
            self.processings_page_offset = 0
        self.get_processings()

    def get_filtered_processings(self):
        """Reset to first page when filter text changes."""
        self.processings_page_offset = 0
        self.get_processings()

    def update_local_processings(self, processings: List[ProcessingDTO]):
        """
        Update local processing history and notify user of status changes.

        Does NOT render the table: the poll renders once with the combined
        (templates + processings) rows after templates resolve, so the table
        doesn't flash through a processings-only intermediate state.

        Args:
            processings: List of ProcessingDTO from server
        """
        if not self.processings_history:
            return

        # Convert list to dict for history update
        processings_dict = {p.id: p for p in processings}

        # Update history and get report of terminal status changes
        terminal_changes = self.processings_history.update(processings_dict, self.app_context.settings)

        # Notify user of newly completed/failed processings
        self._notify_status_changes(terminal_changes, processings_dict)

    def _notify_status_changes(self, 
                               terminal_changes: Dict[str, List[UUID]], 
                               processings: Dict[UUID, ProcessingDTO]) -> None:
        """
        Notify user about processing status changes.
        
        Args:
            terminal_changes: Dict of status -> list of processing IDs
            processings: Dict of all current processings for name lookup
        """
        # Notify about completed processings
        finished_ids = terminal_changes.get(ProcessingStatus.ok.value, [])
        for pid in finished_ids:
            processing = processings.get(pid)
            if processing:
                self.iface.messageBar().pushSuccess(
                    self.tr("Processing completed"),
                    self.tr("Processing '{name}' has finished successfully").format(name=processing.name)
                )
        
        # Notify about failed processings
        failed_ids = terminal_changes.get(ProcessingStatus.failed.value, [])
        for pid in failed_ids:
            processing = processings.get(pid)
            if processing:
                self.iface.messageBar().pushWarning(
                    self.tr("Processing failed"),
                    self.tr("Processing '{name}' has failed").format(name=processing.name)
                )

    def save_processing(self, new_processing: ProcessingDTO):
        """Add new processing status to history and persist to settings."""
        if self.processings_history:
            self.processings_history.add(new_processing.id, new_processing.status)
            self.processings_history.to_settings(self.app_context.settings)

    def update_processing(self, processing_id: Optional[UUID] = None, processing: Optional[UpdateProcessingSchema] = None):
        if not processing:
            return
        self.api.update_processing(processing_id=processing_id, 
                                   processing=processing, 
                                   callback=self.update_processing_callback)

    def update_processing_callback(self, response: QNetworkReply):
        response_data = json.loads(response.readAll().data())
        processing = ProcessingDTO.from_dict(response_data)
        self.save_processing(processing)
        self.view.update_processing_name(processing_id=processing.id, new_name=processing.name)
        self.processings[processing.id] = processing

    def update_template(self):
        """Rename selected template using update-template API."""
        template = self.selected_template()
        print (template.id)
        if not template:
            return

        new_name, ok = QInputDialog.getText(
            self.dlg,
            self.tr("Rename template"),
            self.tr("Template name:"),
            text=str(template.name or ""),
        )
        if not ok:
            return

        new_name = (new_name or "").strip()
        if not new_name:
            alert(self.tr("Please, specify template name"), QMessageBox.Warning)
            return
        if new_name == template.name:
            return

        payload = UpdateProcessingTemplateSchema(
            name=new_name,
            # Rename-only flow: do not send searchParams to avoid geometry update rejection.
            searchParams=None,
            # Keep processing params unchanged on backend; omit field to avoid decoding issues
            processingParams=None,
            activeUntil=None,
        )

        self.api.update_template(
            template_id=template.id,
            data=payload,
            callback=self.update_template_callback,
            error_handler=self.update_template_error_handler,
        )

    def update_template_callback(self, response: QNetworkReply):
        """Handle template update response and refresh table."""
        try:
            response_data = json.loads(response.readAll().data())
        except Exception:
            response_data = {}
        
        print (response_data)

        template_data = response_data.get("template", response_data)
        try:
            if isinstance(template_data, dict) and template_data.get("id"):
                updated_template = ProcessingTemplateDTO.from_dict(template_data)
                self.templates[updated_template.id] = updated_template
                self.view.update_processing_name(
                    processing_id=updated_template.id,
                    new_name=updated_template.name,
                )
        except Exception:
            pass
        self.get_processings()

    def update_template_error_handler(self, error: str):
        """Handle template update error."""
        alert(self.tr("Error renaming template: {}" ).format(error), QMessageBox.Critical)

    # Processing cost
    def update_processing_cost(self):
        """Update the processing cost based on current AOI and workflow.
        
        Uses app_context for: aoi, workflow_defs, user_role, billing_type
        """
        processing_params, error = self.validate_all_processing_params(allow_empty_name=True)

        if error:
            self.dlg.disable_processing_start(error, clear_area=error)
            return

        self.api.get_cost(data=processing_params,
                          callback=self.calculate_processing_cost_callback,
                          error_handler=self.disable_processing_start)

    def calculate_processing_cost_callback(self, response: QNetworkReply):
        self.processing_cost = int(response.readAll().data().decode())
        self.view.set_processing_cost(self.processing_cost)

    def disable_processing_start(self, response: QNetworkReply):
        """
        We do not display the result in case of error,
        the errors are also not displayed to not confuse the user.

        If the user tries to start the processing, he will see the errors
        """
        response_text = response.readAll().data().decode()
        if response_text is not None:
            try:
                message = api_message_parser(response_text)
            except Exception:
                message = None

            if not message or str(message).strip().lower() in {"none", "null"}:
                network_error = ""
                try:
                    network_error = (response.errorString() or "").strip()
                except Exception:
                    network_error = ""
                message = network_error or self.tr("Unknown server error")

            if not self.app_context.user_role.can_start_processing:
                reason = self.tr('Not enough rights to start processing in a shared project ({})').format(self.app_context.user_role.value)
            else:
                reason = self.tr('Processing cost is not available:\n{message}').format(message=message)
            self.view.disable_processing_start(reason, clear_area=False)

    def confirm_delete_processings(self) -> None:
        """Delete one or more processings or templates from the server.

        Asks for confirmation in a pop-up dialog. Multiple items can be selected.
        Is called by clicking the deleteProcessings ('Delete') button.
        """
        # Pause refreshing processings table to avoid conflicts
        self.processing_fetch_timer.stop()
        selected_ids = self.view.selected_processing_ids()
        # Filter to only items that exist (templates or processings)
        valid_ids = [pid for pid in selected_ids if pid in self.processings or pid in self.templates]
        # Ask for confirmation if there are selected rows
        if valid_ids and alert(
                self.tr('Delete selected items?'), QMessageBox.Question
        ):
            self.delete_processings(response=None, items=valid_ids, deleted=[], failed=[])
            
    def delete_processings(self, 
                           response: QNetworkReply, 
                           items: List,
                           deleted: List, 
                           failed: List):
        # todo: save and report error responses?
        if len(items) == 0:
            self.view.delete_processings_from_table(deleted)
            if len(failed) > 0:
                failed_ids = ', <br>'.join(str(f) for f in failed)
                alert(self.tr(f"Failed to remove items with following ids: <center> {failed_ids}"))
            self.processing_fetch_timer.start()
        else:
            item_to_delete = items[0]
            remaining_items = items[1:]
            
            # Determine if this is a template or processing
            if item_to_delete in self.templates:
                # Delete template
                self.api.delete_template(
                    template_id=item_to_delete,
                    callback=self.delete_processings_callback,
                    error_handler=self.delete_processings_error_handler,
                )
                # Store state for callback
                self._delete_state = {
                    'remaining_items': remaining_items,
                    'deleted': list(deleted) + [item_to_delete],
                    'failed': failed
                }
            else:
                # Delete processing
                self.api.delete_processing(
                    processing_id=item_to_delete,
                    callback=self.delete_processings,
                    error_handler=self.delete_processings,
                    callback_kwargs={'items': remaining_items,
                                     'deleted': list(deleted) + [item_to_delete],
                                     'failed': failed},
                    error_handler_kwargs={'items': remaining_items,
                                          'deleted': deleted,
                                          'failed': list(failed) + [item_to_delete]})
    
    def delete_processings_callback(self, response: QNetworkReply):
        """Callback for template deletion to continue with remaining items."""
        state = self._delete_state
        self.delete_processings(
            response=response,
            items=state['remaining_items'],
            deleted=state['deleted'],
            failed=state['failed']
        )
    
    def delete_processings_error_handler(self, response: QNetworkReply):
        """Error handler for template deletion to continue with remaining items."""
        state = self._delete_state
        self.delete_processings(
            response=response,
            items=state['remaining_items'],
            deleted=state['deleted'],
            failed=list(state['failed']) + [state['deleted'][-1]]
        )

    # ============ TEMPLATE ACTIONS ============ #
    
    def pause_template(self):
        """Pause the selected template."""
        template = self.selected_template()
        if not template:
            return
        if template.isActive:
            template_id = template.id
            self.api.stop_template(template_id=template_id,
                                  callback=self.pause_template_callback,
                                  error_handler=self.pause_template_error_handler)
        else:
            alert(self.tr("Template is not active"), QMessageBox.Information)
    
    def pause_template_callback(self, response: QNetworkReply):
        """Handle pause template response."""
        try:
            self.get_processings()  # Refresh to get updated template status
            alert(self.tr("Template paused successfully"), QMessageBox.Information)
        except Exception as e:
            alert(self.tr("Failed to pause template: {}").format(str(e)), QMessageBox.Critical)
    
    def pause_template_error_handler(self, error: str):
        """Handle pause template error."""
        alert(self.tr("Error pausing template: {}").format(error), QMessageBox.Critical)
    
    def resume_template(self):
        """Resume the selected template."""
        template = self.selected_template()
        if not template:
            return
        if not template.isActive:
            self._resume_template_state = {
                'template_id': template.id,
                'template_name': template.name,
            }
            template_id = template.id
            self.api.resume_template(template_id=template_id,
                                    callback=self.resume_template_update_active_until,
                                    error_handler=self.resume_template_error_handler)
        else:
            alert(self.tr("Template is already active"), QMessageBox.Information)

    def resume_template_update_active_until(self, response: QNetworkReply):
        """After resume succeeds, extend activeUntil to 6 months from now."""
        state = getattr(self, '_resume_template_state', {}) or {}
        template_id = state.get('template_id')
        template_name = state.get('template_name')
        if not template_id or not template_name:
            self.resume_template_callback(response)
            return

        active_until = datetime.utcnow() + timedelta(days=180) - timedelta(minutes=1)
        payload = UpdateProcessingTemplateSchema(
            name=template_name,
            searchParams=None,
            processingParams=None,
            activeUntil=active_until.strftime('%Y-%m-%dT%H:%M:%S.0Z'),
        )

        self.api.update_template(
            template_id=template_id,
            data=payload,
            callback=self.resume_template_callback,
            error_handler=self.resume_template_error_handler,
        )
    
    def resume_template_callback(self, response: QNetworkReply):
        """Handle resume template response."""
        try:
            self._resume_template_state = {}
            self.get_processings()  # Refresh to get updated template status
            alert(self.tr("Template resumed successfully"), QMessageBox.Information)
        except Exception as e:
            alert(self.tr("Failed to resume template: {}").format(str(e)), QMessageBox.Critical)
    
    def resume_template_error_handler(self, error: str):
        """Handle resume template error."""
        self._resume_template_state = {}
        alert(self.tr("Error resuming template: {}").format(error), QMessageBox.Critical)

    def restart_template(self):
        """Restart the selected failed template."""
        template = self.selected_template()
        if not template:
            return
        if (template.status or "").upper() != "FAILED":
            alert(self.tr("Only failed templates can be restarted"), QMessageBox.Information)
            return
        self.api.restart_template(
            template_id=template.id,
            callback=self.restart_template_callback,
            error_handler=self.restart_template_error_handler,
        )

    def restart_template_callback(self, response: QNetworkReply):
        """Handle restart template response."""
        try:
            self.get_processings()  # Refresh to get updated template status
            alert(self.tr("Template restarted successfully"), QMessageBox.Information)
        except Exception as e:
            alert(self.tr("Failed to restart template: {}").format(str(e)), QMessageBox.Critical)

    def restart_template_error_handler(self, error: str):
        """Handle restart template error."""
        alert(self.tr("Error restarting template: {}").format(error), QMessageBox.Critical)
    
    def delete_template(self):
        """Delete the selected template after confirmation."""
        template = self.selected_template()
        if not template:
            return
        
        reply = QMessageBox.question(
            self.dlg,
            self.tr("Delete Template"),
            self.tr("Are you sure you want to delete the template '{}'?").format(template.name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            template_id = template.id
            self.api.delete_template(template_id=template_id,
                                    callback=self.delete_template_callback,
                                    error_handler=self.delete_template_error_handler)
    
    def delete_template_callback(self, response: QNetworkReply):
        """Handle delete template response."""
        try:
            self.get_processings()  # Refresh to remove deleted template from table
            alert(self.tr("Template deleted successfully"), QMessageBox.Information)
        except Exception as e:
            alert(self.tr("Failed to delete template: {}").format(str(e)), QMessageBox.Critical)
    
    def delete_template_error_handler(self, error: str):
        """Handle delete template error."""
        alert(self.tr("Error deleting template: {}").format(error), QMessageBox.Critical)
    
    def open_template_details(self):
        """Open a dialog showing template details."""
        template = self.selected_template()
        if not template:
            return

        local_created_at = template.createdAt.astimezone()
        local_active_until = template.activeUntil.astimezone()
        
        # Show template details in a message box for now
        # TODO: Create a proper template details dialog
        details = (
            f"<b>{template.name}</b><br/>"
            f"<b>Status:</b> {template.status}<br/>"
            f"<b>Created:</b> {local_created_at.strftime('%Y-%m-%d %H:%M')}<br/>"
            f"<b>Active Until:</b> {local_active_until.strftime('%Y-%m-%d %H:%M')}<br/>"
            f"<b>Active:</b> {'Yes' if template.isActive else 'No'}<br/>"
            f"<b>Archived:</b> {'Yes' if template.isArchived else 'No'}<br/>"
            f"<b>New Images:</b> {template.newImagesCount or 0}<br/>"
            f"<b>AOI Intersection:</b> {template.maxAoiIntersectionPercent or 'N/A'}%"
        )
        
        alert(details, QMessageBox.Information)

    def stop(self):
        self.processing_fetch_timer.stop()
        self.processing_fetch_timer.deleteLater()

    def selected_processings(self, limit=None) -> List[ProcessingDTO]:
        pids = self.view.selected_processing_ids(limit=limit)
        # limit None will give full selection
        selected_processings = [self.processings[pid] for pid in filter(lambda pid: pid in pids, self.processings)]
        return selected_processings

    def selected_processing(self) -> Optional[ProcessingDTO]:
        first = self.selected_processings(limit=1)
        if not first:
            return None
        return first[0]
    
    def selected_templates(self, limit=None) -> List[ProcessingTemplateDTO]:
        """Get selected templates from the table."""
        pids = self.view.selected_processing_ids(limit=limit)
        # Filter to get only templates (not processings)
        selected_templates = [self.templates[pid] for pid in filter(lambda pid: pid in self.templates, pids)]
        return selected_templates
    
    def selected_template(self) -> Optional[ProcessingTemplateDTO]:
        """Get the first selected template, if any."""
        first = self.selected_templates(limit=1)
        if not first:
            return None
        return first[0]
    
    def is_processing_selected(self) -> bool:
        """Check if selected item is a processing (not a template)."""
        selected = self.selected_processing()
        return selected is not None
    
    def is_template_selected(self) -> bool:
        """Check if selected item is a template."""
        selected = self.selected_template()
        return selected is not None

    def is_only_templates_selected(self) -> bool:
        """True only when current table selection contains templates and no processings."""
        pids = self.view.selected_processing_ids()
        if not pids:
            return False
        return all(pid in self.templates for pid in pids)
    
    def restart_processing(self):
        processing = self.selected_processing()
        if not processing:
            return
        pid = processing.id
        if self.app_context.user_role.can_start_processing:
            self.api.restart_processing(processing_id=pid,
                                        callback=self.start_processing_callback,
                                        error_handler=self.start_processing_error_handler)
            
    def duplicate_processing(self):
        processing = self.selected_processing()
        if not processing:
            return
        self.dlg.disable_processing_start("")
        self.app_context.allow_enable_processing['aoi_loaded'] = False
        self.dlg.processingName.setText(processing.name)
        duplicate_provider_and_model(processing)
        self.result_loader.download_aoi_file(pid=processing.id, callback=self.duplicate_aoi_callback)

    def duplicate_aoi_callback(self, response: QNetworkReply, path: str) -> None:
        self.result_loader.download_aoi_file_callback(response, path)
        provider = self.selected_processing().params.sourceParams
        duplicate_aoi_based_on_provider(provider)

    def validate_all_processing_params(self, 
                                       allow_empty_name: bool = False) -> tuple[Optional[PostProcessingSchemaV2], 
                                                                                Optional[str]]:
        """
        Unified validation for processing prerequisites.
        Returns (processing_params, error_message) tuple.
        """
        # Context validation
        context_error = self.validate_context_params()
        if context_error:
            return None, context_error
        
        # UI parameters validation
        ui_start_params = self.view.read_processing_start_params()
        provider = self.app_context.data_provider
        processing_params = self.get_processing_schema(ui_start_params, provider)
        params_error, disable_start = self.validate_processing_params(processing_params, allow_empty_name)
        if params_error:
            if disable_start:
                return None, params_error
            else:
                return None, None
        
        # Provider validation
        provider_error = validate_provider_params(provider)
        if provider_error:
            return None, provider_error
        
        return processing_params, None
        
