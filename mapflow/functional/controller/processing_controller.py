from PyQt5.QtCore import QObject
from qgis.core import QgsMapLayer

from ..service.aoi_service import AoiService
from ..view.aoi_view import AoiView


class ProcessingController(QObject):
    """The start-processing panel: which AOI a processing will cover.

    Owns the wiring only. It is the one place allowed to see both `AoiService` and `AoiView`,
    which is why the round trips below exist — the service cannot read a checkbox and the view
    cannot call a service (`spec/007_architecture.md` § Layer rules).

    Scope today is AOI selection. Model and options, provider selection, cost and the
    start-button state join it as the later Phase C steps extract them.
    """

    def __init__(self,
                 iface,
                 aoi_service: AoiService,
                 aoi_view: AoiView,
                 add_layer_action,
                 remove_layer_action):
        super().__init__()
        self.iface = iface
        self.aoi_service = aoi_service
        self.aoi_view = aoi_view
        # Owned by mapflow.py, which registers them with QGIS's layer context menu.
        self.add_layer_action = add_layer_action
        self.remove_layer_action = remove_layer_action

        self.aoi_service.aoiLayerRegistered.connect(self._on_aoi_layer_registered)
        self.aoi_service.aoiLayersChanged.connect(self.refresh_excepted_layers)
        self.aoi_service.currentAoiLayerChanged.connect(self.aoi_view.set_current_layer)

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
