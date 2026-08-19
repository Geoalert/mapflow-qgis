from typing import List, Optional, Tuple

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QInputDialog, QLabel, QPushButton, QWidget)
from qgis.core import Qgis, QgsMapLayer, QgsVectorLayer

from ...dialogs.main_dialog import MainDialog
from ...dialogs.select_aoi_layers_dialog import SelectAoiLayersDialog


class AoiView(QObject):
    """Every widget read and write for AOI selection and the on-map edit sessions.

    Deliberately holds no service: a view may import dialogs, model and schema, but not
    `service/` (`spec/007_architecture.md` § Layer rules). The controller reads state from here,
    passes it to the service, and pushes the answer back. That is also why the edit bar's
    buttons emit rather than calling anything — the view cannot reach the session.
    """

    #: The Save AOI / Cancel buttons on the map-canvas bar.
    saveRequested = pyqtSignal()
    cancelRequested = pyqtSignal()

    def __init__(self, dlg: MainDialog, iface):
        super().__init__()
        self.dlg = dlg
        self.iface = iface
        self._edit_bar_item = None

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

    # ---------- the on-map edit session ----------

    def enter_edit_session(self, message: str) -> None:
        """Hide the panel and raise a persistent Save AOI / Cancel bar over the map canvas.

        The panel goes away because the whole point of the session is that the user works on the
        map; the bar is how they get back.
        """
        self.dlg.hide()
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(message))
        layout.addStretch(1)
        save_button = QPushButton(self.tr("Save AOI"))
        cancel_button = QPushButton(self.tr("Cancel"))
        save_button.clicked.connect(self.saveRequested)
        cancel_button.clicked.connect(self.cancelRequested)
        layout.addWidget(save_button)
        layout.addWidget(cancel_button)
        self._edit_bar_item = self.iface.messageBar().pushWidget(widget, Qgis.Info)

    def leave_edit_session(self) -> None:
        """Drop the bar and bring the panel back."""
        if self._edit_bar_item is not None:
            try:
                self.iface.messageBar().popWidget(self._edit_bar_item)
            except (RuntimeError, AttributeError):
                # Already popped — the user can dismiss the bar itself.
                pass
            self._edit_bar_item = None
        self.dlg.show()

    def prompt_aoi_name(self) -> Tuple[str, bool]:
        """Ask for the drawn AOI's name. The bool is False when the user cancelled, which keeps
        the session open so the drawing is not lost."""
        return QInputDialog.getText(self.iface.mainWindow(),
                                    self.tr("Name the AOI"), self.tr("AOI name:"))

    def pick_aoi_layers(self, layers: List[QgsVectorLayer]) -> Optional[List[str]]:
        """Multi-select dialog over ``layers``. None when the user cancelled."""
        dialog = SelectAoiLayersDialog(self.dlg)
        dialog.setup(layers)
        if not dialog.exec():
            return None
        return dialog.selected_layer_ids()
