from typing import List

from PyQt5.QtCore import QObject
from qgis.core import QgsMapLayer

from ...dialogs.main_dialog import MainDialog


class AoiView(QObject):
    """Every widget read and write for the AOI area of the start-processing panel.

    Deliberately holds no service: a view may import dialogs, model and schema, but not
    `service/` (`spec/007_architecture.md` § Layer rules). The controller reads state from here,
    passes it to the service, and pushes the answer back.
    """

    def __init__(self, dlg: MainDialog):
        super().__init__()
        self.dlg = dlg

    @property
    def use_all_vector_layers(self) -> bool:
        return self.dlg.useAllVectorLayers.isChecked()

    def set_excepted_layers(self, layers: List[QgsMapLayer]) -> None:
        self.dlg.polygonCombo.setExceptedLayerList(layers)

    def set_current_layer(self, layer: QgsMapLayer, notify: bool = True) -> None:
        """Point the AOI combo at ``layer``.

        ``notify=False`` blocks `layerChanged`, and with it the cost request that slot fires.
        Used when adding template AOI layers in bulk: no image is selected yet, and the user's
        click computes the cost once afterwards.
        """
        self.dlg.polygonCombo.blockSignals(not notify)
        self.dlg.polygonCombo.setLayer(layer)
        self.dlg.polygonCombo.blockSignals(False)

    def current_layer(self) -> QgsMapLayer:
        return self.dlg.polygonCombo.currentLayer()

    def report_no_imagery_selected(self, reason: str) -> None:
        self.dlg.disable_processing_start(reason=reason, clear_area=True)
