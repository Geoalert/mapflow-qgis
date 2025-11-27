import json
from uuid import UUID
from dataclasses import dataclass, field
from typing import Set, Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal, Qt, pyqtSlot, QTimer
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest
from PyQt5.QtWidgets import QMessageBox
from ...dialogs.main_dialog import MainDialog
from ...http import Http, api_message_parser
from ..view.processing_view import ProcessingView
from ..api.processing_api import ProcessingApi
from ...schema.processing import ProcessingDTO, UpdateProcessingSchema
from ...entity.status import ProcessingStatus
from ...entity.billing import BillingType
from ...entity.provider import MyImageryProvider, ImagerySearchProvider

@dataclass
class ProcessingHistory:
    """
    History of the processings for a specific project, including failed and finished processings,
    that are stored in settings
    """
    project_id: Optional[UUID]
    failed: Set[UUID] = field(default_factory=set)
    finished: Set[UUID] = field(default_factory=set)
    other: Dict[UUID, ProcessingStatus] = field(default_factory=dict)

    def to_settings(self, settings):
        settings.setValue(f"{self.project_id}", json.dumps({"failed": list(self.failed), "finished": list(self.finished)}))

    @classmethod
    def from_settings(cls, settings, project_id: UUID):
        data = json.loads(settings.value(f"{project_id}"))
        return cls(project_id, set(data["failed"]), set(data["finished"]))

    def is_finished(self, processing_id: UUID):
        return processing_id in self.finished

    def is_failed(self, processing_id: UUID):
        return processing_id in self.failed

    def add(self, processing_id: UUID, status: ProcessingStatus):
        if status.is_failed:
            self.failed.add(processing_id)
        elif status.is_ok:
            self.finished.add(processing_id)
        else:
            self.other[processing_id] = status

class ProcessingService(QObject):
    """
    A service to store & query the mapflow processings.
    """

    def __init__(self,
                 http: Http,
                 server: str,
                 dlg: MainDialog,
                 iface,
                 result_loader,
                 plugin_version,
                 temp_dir,
                 settings,
                 timer_interval):
        super().__init__()
        self.http = http
        self.server = server
        self.iface = iface
        self.result_loader = result_loader
        self.plugin_version = plugin_version
        self.temp_dir = temp_dir
        self.view = ProcessingView(dlg=dlg)
        self.api = ProcessingApi(http=http,
                                 server=server,
                                 dlg=dlg,
                                 iface=iface,
                                 result_loader=self.result_loader,
                                 plugin_version=self.plugin_version)
        self.settings = settings

        self.current_project_id: Optional[str] = None
        self.processings = set()
        self.processings_history = None # ProcessingHistory() - local storage for active processings list
        self.processing_fetch_timer = QTimer(dlg)
        self.processing_fetch_timer.setInterval(timer_interval)
        self.deleting_processings = None

    def set_current_project(self, project_id: str):
        """
        Set the current project ID and optionally refresh processings.
        This slot is connected to ProjectService.projectChanged signal.
        
        Args:
            project_id: The ID of the project to set as current
        """
        if not project_id:
            self.current_project_id = None
            return
            
        self.current_project_id = project_id
        # Update processing history context for the new project
        if self.current_project_id:
            try:
                self.processings_history = ProcessingHistory.from_settings(
                    self.settings, UUID(self.current_project_id)
                )
            except (ValueError, KeyError):
                # If no history exists for this project, create new one
                self.processings_history = ProcessingHistory(project_id=UUID(self.current_project_id))
        
        # Optionally refresh processings for the new project
        # self.get_processings()  # Uncomment when this method is implemented


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
        self.http.post()

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

    def get_processings(self):
        project_id = None
        # todo: get real project id.
        #  - signal from ProjectService?
        #  - initialize ProjcessingService with a ProjectService?
        self.api.get_processings(project_id=project_id,
                                 callback=self.get_processings_callback)

    def get_processings_callback(self, response: QNetworkReply):
        """Update the processing table and user limit.

        :param response: The HTTP response.
        """
        response_data = json.loads(response.readAll().data())
        processings = [ProcessingDTO.from_dict(entry) for entry in response_data]
        if all(not (p.status.is_in_progress or p.status.is_awaiting)
               and p.review_status.is_not_accepted
               for p in processings):
            # We do not re-fetch the processings, if nothing is going to change.
            # What can change from server-side: processing can finish if IN_PROGRESS or AWAITING
            # or review can be accepted if NOT_ACCEPTED.
            # Any other processings can change only from client-side
            self.processing_fetch_timer.stop()
        self.processings = {processing.id: processing for processing in processings}
        self.update_local_processings(processings)

    def save_processing(self, new_processing):
        # add new processing status to settings
        self.settings.setValue("", "")

    def update_processing(self, processing_id: UUID, processing: UpdateProcessingSchema):
        self.api.update_processing(processing_id=processing_id, processing=processing, callback=self.update_processing_callback)

    def update_processing_callback(self, response: QNetworkReply):
        processing = ProcessingDTO.from_dict(json.loads(response.readAll().data()))
        self.save_processing(processing)
        self.view.update_processing_name(processing_id=processing.id, new_name=processing.name)

    # Processing cost
    def update_processing_cost(self, aoi, workflow_defs):
        if not aoi:
            # Here the button must already be disabled, and the warning text set
            if self.dlg.startProcessing.isEnabled():
                if not self.user_role.can_start_processing:
                    reason = self.tr('Not enough rights to start processing in a shared project ({})').format(self.user_role.value)
                else:
                    reason = self.tr("Set AOI to start processing")
                self.view.disable_processing_start(reason, clear_area=False)
        elif not self.workflow_defs:
            self.dlg.disable_processing_start(reason=self.tr("Error! Models are not initialized.\n"
                                                             "Please, make sure you have selected a project"),
                                              clear_area=True)
        elif self.billing_type != BillingType.credits:
            self.dlg.startProcessing.setEnabled(True)
            self.dlg.processingProblemsLabel.clear()
            request_body, error = self.create_processing_request(allow_empty_name=True)
        else:  # self.billing_type == BillingType.credits: f
            provider = self.providers[self.dlg.providerIndex()]
            request_body, error = self.create_processing_request(allow_empty_name=True)
            if not request_body:
                self.dlg.disable_processing_start(self.tr("Processing cost is not available:\n"
                                                          "{error}").format(error=error))
            elif isinstance(provider, ImagerySearchProvider) and \
                not self.dlg.metadataTable.selectionModel().hasSelection():
                    self.dlg.disable_processing_start(self.tr("This provider requires image ID. "
                                                              "Use search tab to find imagery for you requirements, "
                                                              "and select image in the table."))
            elif isinstance(provider, MyImageryProvider) and\
                not self.dlg.mosaicTable.selectionModel().hasSelection():
                    self.dlg.disable_processing_start(reason=self.tr('Choose imagery to start processing'))
            else:
                if self.user_role.can_start_processing:
                    self.http.post(
                        url=f"{self.server}/processing/cost/v2",
                        callback=self.calculate_processing_cost_callback,
                        body=request_body.as_json().encode(),
                        use_default_error_handler=False,
                        error_handler=self.clear_processing_cost
                    )

    def disable_processing_start(self, response: QNetworkReply):
        """
        We do not display the result in case of error,
        the errors are also not displayed to not confuse the user.

        If the user tries to start the processing, he will see the errors
        """
        response_text = response.readAll().data().decode()
        if response_text is not None:
            message = api_message_parser(response_text)
            if not self.user_role.can_start_processing:
                reason = self.tr('Not enough rights to start processing in a shared project ({})').format(self.user_role.value)
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

