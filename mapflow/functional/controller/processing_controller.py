from PyQt5.QtCore import QObject
from qgis.core import QgsMapLayer

from .. import layer_utils
from ..service.aoi_service import AoiService
from ..view.aoi_view import AoiView
from ...schema import BillingType


class ProcessingController(QObject):
    """The start-processing panel: the model and its options, which AOI a processing will cover,
    the Start button's text and state, and the review/rating panel beside it.

    Owns the wiring only. It is the one place allowed to see both a service and a view, which is
    why the round trips below exist — the service cannot read a checkbox and the view cannot call
    a service (`spec/007_architecture.md` § Layer rules).

    Provider selection and cost join it as the later Phase C steps extract them.
    """

    def __init__(self,
                 iface,
                 aoi_service: AoiService,
                 aoi_view: AoiView,
                 add_layer_action,
                 remove_layer_action,
                 processing_service=None,
                 processing_view=None,
                 app_context=None,
                 review_dialog=None,
                 rating_submit_button=None,
                 rating_combo=None,
                 accept_button=None,
                 review_button=None,
                 processings_table=None,
                 provider_service=None,
                 model_combo=None,
                 model_options_changed=None,
                 metadata_table=None,
                 start_button=None):
        super().__init__()
        self.iface = iface
        self.aoi_service = aoi_service
        self.aoi_view = aoi_view
        # Owned by mapflow.py, which registers them with QGIS's layer context menu.
        self.add_layer_action = add_layer_action
        self.remove_layer_action = remove_layer_action
        self.processing_service = processing_service
        self.processing_view = processing_view
        self.app_context = app_context
        self.review_dialog = review_dialog
        self.provider_service = provider_service

        self.aoi_service.aoiLayerRegistered.connect(self._on_aoi_layer_registered)
        self.aoi_service.aoiLayersChanged.connect(self.refresh_excepted_layers)
        self.aoi_service.currentAoiLayerChanged.connect(self.aoi_view.set_current_layer)

        if model_combo is not None:
            model_combo.currentIndexChanged.connect(self.on_model_change)
        if model_options_changed is not None:
            model_options_changed.connect(self.on_options_change)
        if processing_service is not None:
            processing_service.ratingLoaded.connect(self.processing_view.set_rating_labels)
            processing_service.reviewSubmitted.connect(self._on_review_submitted)
            # The start panel: the service says what it must show, this renders it. The service
            # holds no view and reads no widget but the one enabled-state it still needs (C2.2c).
            processing_service.startPanelNeeded.connect(self._provide_start_panel)
            processing_service.startDisabled.connect(self.processing_view.disable_processing_start)
            processing_service.startUnblocked.connect(
                self.processing_view.clear_problem_and_enable_start)
            processing_service.submissionInFlight.connect(self._on_submission_in_flight)
            processing_service.costQuoted.connect(self.processing_view.set_processing_cost)
            processing_service.processingNameCleared.connect(
                self.processing_view.clear_processing_name)
            processing_service.processingNameSet.connect(self.processing_view.set_processing_name)
            processing_service.confirmationRequested.connect(self._confirm_processing_start)
        if start_button is not None:
            start_button.clicked.connect(self.start_processing)
        if rating_submit_button is not None:
            rating_submit_button.clicked.connect(self.submit_rating)
        if rating_combo is not None:
            rating_combo.activated.connect(self.refresh_feedback_controls)
        if accept_button is not None:
            accept_button.clicked.connect(self.accept_processing)
        if review_button is not None:
            review_button.clicked.connect(self.show_review_dialog)
        if review_dialog is not None:
            review_dialog.accepted.connect(self.submit_review)
        if processings_table is not None:
            processings_table.itemSelectionChanged.connect(self.refresh_feedback_controls)
            processings_table.cellClicked.connect(self.load_current_rating)
            # Which template a Start would run depends on the processings-table selection, so
            # the button follows it. `ProjectProcessingController` subscribes to the same signal
            # for the Delete button — two regions reading one widget signal is how they stay
            # independent (`spec/007_architecture.md`: controllers must not call each other).
            processings_table.itemSelectionChanged.connect(
                self.update_start_processing_button_state)
        if metadata_table is not None:
            # The planned-processing gate counts selected search images.
            metadata_table.itemSelectionChanged.connect(self.update_start_processing_button_state)

    # ---------- the model and its options ----------

    def on_model_change(self, *args) -> None:
        """A different model was picked: its options, its price, and which imagery sources it
        accepts all change together."""
        wd_name = self.processing_view.selected_model_name()
        wd = self.app_context.get_workflow_def(wd_name)
        # Unconditional, and before the early return: a model with no definition still narrows
        # the provider list, and leaving the previous model's sources offered is worse than
        # offering none.
        self.provider_service.set_available_imagery_sources(wd_name)
        if not wd:
            return
        self.show_wd_options(wd)
        self._show_price(wd)
        # The test is `blocks`, not `optional_blocks`: a model that declares any block waits,
        # because adding its option checkboxes fires `modelOptionsChanged` and `on_options_change`
        # quotes the cost then. Which leaves obligatory-only models quoted by neither path —
        # pinned in `test_a_model_whose_blocks_are_all_obligatory_is_not_quoted_on_selection`.
        if not wd.blocks:
            self._update_cost()

    def on_options_change(self, *args) -> None:
        wd = self.app_context.get_workflow_def(self.processing_view.selected_model_name())
        if not wd:
            return
        self._show_price(wd)
        self.processing_service.save_option_settings(wd, self.processing_view.enabled_blocks())
        self._update_cost()

    def show_wd_options(self, wd) -> None:
        """Rebuild the option checkboxes for `wd`, ticked as this user last left them."""
        can_start_processing = True
        if self.app_context.user_role:
            can_start_processing = self.app_context.user_role.can_start_processing
        self.processing_view.show_model_options(self.processing_service.saved_model_options(wd),
                                                enabled=can_start_processing)

    def _show_price(self, wd) -> None:
        self.processing_view.show_wd_price(
            wd_price=wd.get_price(enable_blocks=self.processing_view.enabled_blocks()),
            wd_description=wd.description,
            display_price=self.app_context.billing_type == BillingType.credits)

    def _update_cost(self) -> None:
        """A cost is quoted in credits, so only a credits account has one to ask for."""
        if self.app_context.billing_type == BillingType.credits:
            self.processing_service.update_processing_cost()

    # ---------- the start panel: what the service asks for, and starting ----------

    def _provide_start_panel(self) -> None:
        """Answer `startPanelNeeded`: hand the service the panel it is about to read. Synchronous,
        so the service has it by the time its `emit()` returns."""
        self.processing_service.set_start_panel(
            params=self.processing_view.read_processing_start_params(),
            enabled_blocks=self.processing_view.enabled_blocks(),
            has_option_widgets=self.processing_view.has_option_widgets(),
            aoi_layer_chosen=self.processing_view.aoi_layer_chosen())

    def start_processing(self, *args) -> None:
        """The Start button. The button is the start panel's, so its click is this controller's."""
        self.processing_service.start_processing()

    def _on_submission_in_flight(self, in_flight: bool) -> None:
        """Disable Start while a run request is out; re-enable when it returns."""
        self.processing_view.set_start_enabled(not in_flight)

    def _confirm_processing_start(self, processing_params) -> None:
        """The user asked to confirm each start: raise the dialog, and submit on OK. The dialog is
        the view's — a service may not build one — and the values it shows are half domain
        (from the service) and half panel (read by the view)."""
        self.processing_view.confirm_processing_start(
            name=processing_params.name,
            details=self.processing_service.confirmation_details(),
            on_accept=lambda: self.processing_service.submit_processing(processing_params))

    def update_start_processing_button_state(self, *args) -> None:
        """Render start button text and enforce planned-processing image selection gate."""
        self.update_start_processing_button_text()
        error = self.processing_service.planned_processing_selection_error()
        if error:
            self.processing_view.disable_processing_start(reason=error, clear_area=False)
            return
        # No gate error: re-enable the button and clear any planned-processing reason label.
        self.processing_view.enable_processing_start(
            clear_reason=self.tr("Select one or more images in search results "
                                 "to start planned processing"))

    def update_start_processing_button_text(self, *args) -> None:
        # Mirror what the start action actually does: "Start planned processing" only when a
        # template run would happen (template selected + imagery-search source + its results open).
        self.processing_view.set_start_button_text(
            self.tr("Start planned processing") if self.processing_service.template_to_run()
            else self.tr("Start processing"))

    # ---------- review and rating ----------

    def load_current_rating(self, *args) -> None:
        self.processing_service.load_current_rating()

    def submit_rating(self, *args) -> None:
        """Which star and what feedback are widget reads, so they are gathered here and handed
        over rather than looked up by the service."""
        self.processing_service.submit_rating(self.processing_view.selected_rating(),
                                              self.processing_view.rating_feedback())

    def accept_processing(self, *args) -> None:
        self.processing_service.accept_processing()

    def show_review_dialog(self, *args) -> None:
        """Open the review dialog, but only for a processing a review decision applies to. The
        service answers that (and says why when it does not), so the check is not repeated here."""
        processing = self.processing_service._reviewable_processing()
        if processing is None:
            return
        self.review_dialog.setup(processing)
        self.review_dialog.show()

    def submit_review(self, *args) -> None:
        """The comment and the reviewer's corrections live in the dialog, which a service may not
        touch — so they are read here and passed as plain values."""
        self.processing_service.reject_processing(
            processing_id=self.review_dialog.processing.id,
            comment=self.review_dialog.reviewComment.toPlainText(),
            features=layer_utils.export_as_geojson(self.review_dialog.reviewLayerCombo.currentLayer()))

    def _on_review_submitted(self) -> None:
        self.review_dialog.reviewComment.setText("")

    def refresh_feedback_controls(self, *args) -> None:
        """Enable the rating or the review controls for the current selection — whichever this
        account uses. 'Feedback' covers both: a 1-5 star rating for regular users, a review for
        accounts with the review workflow enabled."""
        processing = self.processing_service.selected_processing()
        if processing is None:
            self._set_feedback_enabled(status_ok=False, in_review=False)
            return
        self._set_feedback_enabled(status_ok=processing.status.is_ok,
                                   in_review=processing.reviewStatus.is_in_review)
        self.processing_view.enable_restart_action(
            self.app_context.user_role.can_start_processing
            and (processing.status.is_failed or processing.status.is_cancelled))

    def _set_feedback_enabled(self, status_ok: bool, in_review: bool) -> None:
        if self.app_context.review_workflow_enabled:
            self.processing_view.enable_review(
                status_ok and in_review,
                self.tr("Only correctly finished processings with 'Review required' status "
                        "can be reviewed"))
            return
        self.processing_view.enable_rating(
            can_interact=status_ok and self.app_context.user_role.can_delete_rename_review_processing,
            can_send=self.processing_view.rating_is_selected(),
            reason=self._rating_blocked_reason(status_ok))

    def _rating_blocked_reason(self, status_ok: bool) -> str:
        role = self.app_context.user_role
        if not role.can_delete_rename_review_processing:
            return self.tr('Not enough rights to rate processing in a shared project ({})').format(
                role.value)
        if not status_ok:
            if not self.processing_service.selected_processing():
                return self.tr('Please select processing')
            return self.tr("Only correctly finished processings (status OK) can be rated")
        if not self.processing_view.rating_is_selected():
            return self.tr("Please select rating to submit")
        return ""

    # ---------- registry ----------

    def refresh_excepted_layers(self) -> None:
        """Recompute what the AOI combo must not offer. The flag lives in a checkbox, so it
        travels controller -> service rather than being read by the service."""
        self.aoi_view.set_excepted_layers(
            self.aoi_service.excepted_layers(self.aoi_view.use_all_vector_layers))

    def _on_aoi_layer_registered(self, layer: QgsMapLayer) -> None:
        self.iface.addCustomActionForLayer(self.remove_layer_action, layer)

    def use_current_layer_as_aoi(self) -> None:
        """'Use as AOI in Mapflow' on a layer's context menu. Which layer that is comes from the
        layer tree — a widget, so the controller resolves it."""
        self.aoi_service.register_layer(self.iface.layerTreeView().currentLayer())

    def stop_using_current_layer_as_aoi(self) -> None:
        self.aoi_service.unregister_layer(self.iface.layerTreeView().currentLayer())

    # ---------- creating AOI layers ----------

    def create_aoi_from_map_extent(self, *args) -> None:
        layer = self.aoi_service.create_layer_from_rect(
            self.iface.mapCanvas().extent(), self.aoi_service.app_context.project.crs())
        self.iface.setActiveLayer(layer)

    def create_aoi_from_imagery(self, *args) -> None:
        layer = self.aoi_service.create_layer_from_imagery()
        if layer is None:
            self.aoi_view.report_no_imagery_selected(
                self.tr('Choose imagery collection or image to start processing'))
            return
        self.iface.setActiveLayer(layer)

    def draw_aoi(self, *args) -> None:
        """New empty AOI layer, active and in edit mode with the add-feature tool armed."""
        layer = self.aoi_service.create_editable_layer()
        self.iface.setActiveLayer(layer)
        self.iface.actionAddFeature().trigger()
