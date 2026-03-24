import json
from uuid import UUID
from typing import Dict, Optional, List
from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtNetwork import QNetworkReply
from PyQt5.QtWidgets import QMessageBox, QApplication
from .provider_service import (get_provider_params, 
                               setup_provider_info, 
                               validate_provider_params, 
                               duplicate_aoi_based_on_provider,
                               duplicate_provider_and_model)
                               
from .. import helpers
from ...dialogs.main_dialog import MainDialog
from ...dialogs.confirm_processing_start_dialog import ConfirmProcessingStartDialog
from ...errors import (ProcessingInputDataMissing,
                       BadProcessingInput,
                       PluginError,
                       ImageIdRequired,
                       AoiNotIntersectsImage)
from ...http import Http, api_message_parser
from ..view.processing_view import ProcessingView
from ..api.processing_api import ProcessingApi
from ...schema import ProcessingDTO, UpdateProcessingSchema, ProcessingStatus, BillingType, ProcessingHistory, PostProcessingSchemaV2
from ...schema.processing import ProcessingUIParams
from ..service.alert_service import alert, AlertService
from ..app_context import AppContext
from ...functional.layer_utils import ResultsLoader
from ...http import Http, get_error_report_body
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
        self.processings_history = None # ProcessingHistory() - local storage for active processings list
        self.processing_fetch_timer = QTimer(dlg)
        self.processing_fetch_timer.setInterval(timer_interval)
        self.processing_cost = 0

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
        except AoiNotIntersectsImage:
            error = self.tr("Selected AOI does not intersect the selected imagery")
        except ImageIdRequired:
            error = self.tr("This provider requires image ID. Use search tab to find imagery for you requirements, "
                            "and select image in the table.")
        except PluginError as e:
            error = str(e)
        return error, disable_start
    
    def validate_context_params(self):
        error = None
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
            self.iface.messageBar().pushInfo(
                self.app_context.plugin_name, 
                self.tr('Starting the processing...')
            )
            try:
                self.dlg.startProcessing.setEnabled(False)
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
        new_processing = ProcessingDTO.from_dict(response_data)
        self.view.clear_processing_name(new_processing.name)
        self.processing_fetch_timer.start()  # start monitoring
        # Add to history
        self.processings[new_processing.id] = new_processing
        self.processings_history.add(new_processing.id, new_processing.status)
        # display
        self.view.add_new_processing(new_processing)
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
        self.view.set_table_loading()
        self.get_processings()
        self.processing_fetch_timer.start()

    def get_processings(self):
        # Fetch processings at startup and start the timer to keep fetching them afterwards
        self.api.get_processings(project_id=self.app_context.current_project.id,
                                 callback=self.get_processings_callback)

    def get_processings_callback(self, response: QNetworkReply):
        """Update the processing table and user limit.

        :param response: The HTTP response.
        """
        response_data = json.loads(response.readAll().data())
        processings = [ProcessingDTO.from_dict(entry) for entry in response_data]
        if all(p.is_final_state for p in processings):
            # We do not re-fetch the processings, if nothing is going to change.
            # What can change from server-side: processing can finish if IN_PROGRESS or AWAITING
            # or review can be accepted if NOT_ACCEPTED.
            # Any other processings can change only from client-side
            self.processing_fetch_timer.stop()
        self.processings = {processing.id: processing for processing in processings}
        self.update_local_processings(processings)

    def update_local_processings(self, processings: List[ProcessingDTO]):
        """
        Update local processing history and notify user of status changes.
        
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
        
        # Update the view
        self.view.update_processing_table(processings)

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
            message = api_message_parser(response_text)
            if not self.app_context.user_role.can_start_processing:
                reason = self.tr('Not enough rights to start processing in a shared project ({})').format(self.app_context.user_role.value)
            else:
                reason = self.tr('Processing cost is not available:\n{message}').format(message=message)
            self.view.disable_processing_start(reason, clear_area=False)

    def confirm_delete_processings(self) -> None:
        """Delete one or more processings from the server.

        Asks for confirmation in a pop-up dialog. Multiple processings can be selected.
        Is called by clicking the deleteProcessings ('Delete') button.
        """
        # Pause refreshing processings table to avoid conflicts
        self.processing_fetch_timer.stop()
        selected_ids = self.view.selected_processing_ids()
        # Ask for confirmation if there are selected rows
        if selected_ids and alert(
                self.tr('Delete selected processings?'), QMessageBox.Question
        ):
            self.delete_processings(response=None, processings=selected_ids, deleted=[], failed=[])
            
    def delete_processings(self, 
                           response: QNetworkReply, 
                           processings: List[UUID],
                           deleted: List[UUID], 
                           failed: List[UUID]):
        # todo: save and report error responses?
        if len(processings) == 0:
            self.view.delete_processings_from_table(deleted)
            if len(failed) > 0:
                failed_ids = ', <br>'.join(failed)
                alert(self.tr(f"Failed to remove processings with following ids: <center> {failed_ids}"))
            self.processing_fetch_timer.start()
        else:
            processing_to_delete = processings[0]
            non_deleted = processings[1:]
            self.api.delete_processing(processing_id=processing_to_delete,
                                       callback=self.delete_processings,
                                       error_handler=self.delete_processings,
                                       callback_kwargs={'processings': non_deleted,
                                                        'deleted': list(deleted) + [processing_to_delete],
                                                        'failed': failed},
                                       error_handler_kwargs={'processings': non_deleted,
                                                             'deleted': deleted,
                                                             'failed': list(failed) + [processing_to_delete]})

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
        
