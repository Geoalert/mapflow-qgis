import json
from uuid import UUID
from typing import Dict, Optional, List
from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtNetwork import QNetworkReply
from PyQt5.QtWidgets import QMessageBox
from ...dialogs.main_dialog import MainDialog
from ...http import Http, api_message_parser
from ..view.processing_view import ProcessingView
from ..api.processing_api import ProcessingApi
from ...schema import ProcessingDTO, UpdateProcessingSchema, ProcessingStatus, BillingType, ProcessingHistory
from ..app_context import AppContext

class ProcessingService(QObject):
    """
    A service to store & query the mapflow processings.
    """

    def __init__(self,
                 http: Http,
                 dlg: MainDialog,
                 iface,
                 result_loader,
                 app_context: AppContext,
                 settings,
                 timer_interval):
        super().__init__()
        self.http = http
        self.iface = iface
        self.result_loader = result_loader
        self.app_context = app_context
        self.settings = settings
        self.view = ProcessingView(dlg=dlg)
        self.api = ProcessingApi(http=http,
                                 dlg=dlg,
                                 iface=iface,
                                 result_loader=self.result_loader)

        self.processings = set()
        self.processings_history = None # ProcessingHistory() - local storage for active processings list
        self.processing_fetch_timer = QTimer(dlg)
        self.processing_fetch_timer.setInterval(timer_interval)
        self.deleting_processings = None
        self.processing_cost = 0

    def load_processing_history(self):
        """
        Loads processing history to set up the notifications after the processings are fetched
        """
        # Update processing history context for the new project
        if self.app_context.current_project:
            try:
                self.processings_history = ProcessingHistory.from_settings(
                    self.settings, UUID(self.app_context.current_project.id)
                )
                print(f"Read processings history: {len(self.processings_history.processing_statuses)}")
            except (ValueError, KeyError):
                # If no history exists for this project, create new one
                self.processings_history = ProcessingHistory(project_id=UUID(self.app_context.current_project.id))
                print(f"Failed to read processings history: {len(self.processings_history.processing_statuses)}")

        # Optionally refresh processings for the new project
        # self.get_processings()  # Uncomment when this method is implemented

    # ================  CREATE  ====================== #
    def validate_params(self, ui_start_params):
        pass

    def start_processing(self):
        """
            if self.project_id != 'default':
            request_body.projectId = self.project_id

        """
        self.processing_fetch_timer.stop()
        ui_start_params = self.view.read_processing_start_params()
        # maybe some logic behind validation?
        self.validate_params(ui_start_params)
        provider = self.get_data_provider(ui_start_params)
        source_params = provider.source_params()
        # gather all the other logic
        self.api.create_processing()


    def start_processing_callback(self, response: QNetworkReply) -> None:
        """Display a success message and clear the processing name field."""
        self.alert(
            self.tr("Success! We'll notify you when the processing has finished."),
            QMessageBox.Information
        )
        new_processing = ProcessingDTO.from_dict(json.loads(response.readAll().data()))
        self.view.clear_processing_name(new_processing.name)
        self.processing_fetch_timer.start()  # start monitoring
        # Add to history
        self.processings[new_processing.id] = new_processing
        self.processings_history.add(new_processing.id, new_processing.status)
        # display
        self.view.add_new_processing(new_processing)
        self.dlg.startProcessing.setEnabled(True)

    def start_processing_error_handler(self):
        self.dlg.startProcessing.setEnabled(True)
        self.processing_fetch_timer.start()
        self.alert(self.tr("Failed to start processing"), QMessageBox.Warning)

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
        print(f"In update_local_processings: {len(self.processings_history.processing_statuses)}")
        terminal_changes = self.processings_history.update(processings_dict, self.settings)
        
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
            self.processings_history.to_settings(self.settings)

    def update_processing(self, processing_id: UUID, processing: UpdateProcessingSchema):
        self.api.update_processing(processing_id=processing_id, processing=processing, callback=self.update_processing_callback)

    def update_processing_callback(self, response: QNetworkReply):
        processing = ProcessingDTO.from_dict(json.loads(response.readAll().data()))
        self.save_processing(processing)
        self.view.update_processing_name(processing_id=processing.id, new_name=processing.name)

    # Processing cost
    def update_processing_cost(self):
        """Update the processing cost based on current AOI and workflow.
        
        Uses app_context for: aoi, workflow_defs, user_role, billing_type
        """
        aoi = self.app_context.aoi
        workflow_defs = self.app_context.workflow_defs
        user_role = self.app_context.user_role
        
        if not aoi:
            # Here the button must already be disabled, and the warning text set
            if self.view.dlg.startProcessing.isEnabled():
                if not user_role.can_start_processing:
                    reason = self.tr('Not enough rights to start processing in a shared project ({})').format(user_role.value)
                else:
                    reason = self.tr("Set AOI to start processing")
                self.view.disable_processing_start(reason, clear_area=False)
        elif not workflow_defs:
            self.view.disable_processing_start(reason=self.tr("Error! Models are not initialized.\n"
                                                             "Please, make sure you have selected a project"),
                                              clear_area=True)
        elif self.app_context.billing_type != BillingType.credits:
            self.view.dlg.startProcessing.setEnabled(True)
            self.view.dlg.processingProblemsLabel.clear()
        else:  # billing_type == BillingType.credits
            # TODO: This method needs access to providers and create_processing_request
            # which are currently in Mapflow class. Consider:
            # 1. Moving provider logic to a ProviderService
            # 2. Passing a callback for request creation
            # 3. Moving this entire cost calculation to Mapflow
            pass

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

    def delete_processings(self) -> None:
        """Delete one or more processings from the server.

        Asks for confirmation in a pop-up dialog. Multiple processings can be selected.
        Is called by clicking the deleteProcessings ('Delete') button.
        """
        # Pause refreshing processings table to avoid conflicts
        self.processing_fetch_timer.stop()
        selected_ids = self.selected_processing_ids()
        # Ask for confirmation if there are selected rows
        if selected_ids and self.alert(
                self.tr('Delete selected processings?'), QMessageBox.Question
        ):
            self.deleting_processings = {id_: None for id_ in selected_ids}
            for id_ in selected_ids:
                self.api.delete_processing(processing_id=id_,
                                           callback=self.delete_processings_callback,
                                           error_handler=self.delete_processings_error_handler,
                                           callback_kwargs={"processing_id": id_},
                                           error_handler_kwargs={"processing_id": id_})

    def _finalize_processing_delete(self):
        self.view.delete_processings_from_table([key for key, value in self.deleting_processings.items() if value])
        # todo: save and report error responses?
        self.report_http_error(self.tr(f"Failed to remove processings {[key for key, value in self.deleting_processings.items() if value is False]} "))
        self.processing_fetch_timer.start()
        self.deleting_processings = None

    def delete_processings_callback(self,
                                    _: QNetworkReply,
                                    processing_id: str) -> None:
        """Delete processings from the table after they've been deleted from the server.

        :param id_: ID of the deleted processing.
        """
        self.deleting_processings[processing_id] = True
        if any(status is None for status in self.deleting_processings.values()):
            pass
        else:
            self._finalize_processing_delete()

    def delete_processings_error_handler(self,
                                         _: QNetworkReply,
                                         processing_id: str) -> None:
        """Error handler for processing deletion request.

        :param response: The HTTP response.
        """
        self.deleting_processings[processing_id] = False
        if any(status is None for status in self.deleting_processings.values()):
            pass
        else:
            self._finalize_processing_delete()

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
