import os
from typing import List, Optional

from PyQt5.QtCore import QObject, pyqtSignal
from qgis.core import QgsFeature, QgsGeometry, QgsMapLayer, QgsVectorLayer

from .. import helpers
from ..app_context import AppContext


class AoiService(QObject):
    """AOI geometry and the AOI layers the user can process.

    Holds no widget and no dialog (`spec/007_architecture.md` § Layer rules), which shapes two
    things that would otherwise look roundabout:

    * anything the UI must do in response leaves as a signal, and a controller subscribes —
      the service never calls a view;
    * inputs that live in a widget arrive as arguments. `excepted_layers` takes the
      "use all vector layers" flag rather than reading the checkbox, and the layer-creation
      methods return the layer instead of activating it, because making a layer active is an
      `iface` call on the map canvas.
    """

    #: A layer joined the AOI registry. Carries the layer so the controller can attach the
    #: per-layer "Remove AOI from Mapflow" context action.
    aoiLayerRegistered = pyqtSignal(object)
    #: The registry changed; whatever filters the AOI combo is stale.
    aoiLayersChanged = pyqtSignal()
    #: The AOI combo should point at this layer. The bool is whether the change may trigger a
    #: cost request — False while adding layers in bulk, where no image is selected yet.
    currentAoiLayerChanged = pyqtSignal(object, bool)

    def __init__(self,
                 iface,
                 app_context: AppContext,
                 plugin_dir: str,
                 result_loader,
                 data_catalog_service):
        super().__init__()
        self.iface = iface
        self.app_context = app_context
        self.plugin_dir = plugin_dir
        self.result_loader = result_loader
        self.data_catalog_service = data_catalog_service
        #: Layers the user has marked as usable AOIs. Owned here rather than on AppContext:
        #: nothing outside the AOI code reads it, and one concept has one home (invariant 4).
        self.aoi_layers: List[QgsVectorLayer] = []
        self.aoi_layer_counter = 0

    # ---------- the registry ----------

    def register_layer(self,
                       layer: QgsMapLayer,
                       recompute_cost: bool = True,
                       set_current: bool = True) -> None:
        """Mark ``layer`` as usable as an AOI.

        ``set_current=False`` for template AOI *display* layers added in bulk: they must not
        hijack the processing Area (the last one used to stick as the Area — feedback 8.1); the
        Area is driven by the AOI table selection instead.
        """
        if layer is None:
            return
        if layer not in self.aoi_layers:
            self.aoi_layers.append(layer)
            self.aoiLayerRegistered.emit(layer)
        self.aoiLayersChanged.emit()
        if not set_current:
            return
        self.currentAoiLayerChanged.emit(layer, recompute_cost)

    def unregister_layer(self, layer: QgsMapLayer) -> None:
        try:
            self.aoi_layers.remove(layer)
        except ValueError:
            # Can easily be gone already: the per-layer context action cannot be removed from a
            # single layer's menu, so "Remove AOI" stays clickable after the first click.
            pass
        self.aoiLayersChanged.emit()

    def excepted_layers(self, use_all_vector_layers: bool) -> List[QgsMapLayer]:
        """Layers the AOI combo must *not* offer.

        With "use all vector layers" on, only the search-metadata layers are excluded — they are
        big, crowded, and lead to topology errors. With it off, everything that is not a
        registered AOI layer is excluded.
        """
        layers = self.app_context.project.mapLayers().values()
        if use_all_vector_layers:
            provider = self.app_context.search_provider
            if not provider:
                return []
            return [layer for layer in layers if provider.name + ' metadata' == layer.name()]
        return [layer for layer in layers if layer not in self.aoi_layers]

    # ---------- creating AOI layers ----------

    def _new_aoi_layer(self, geometry: Optional[QgsGeometry], editable: bool = False):
        """A styled, numbered in-memory polygon layer, added to the map and the registry."""
        layer = QgsVectorLayer('Polygon?crs=epsg:4326', f'AOI_{self.aoi_layer_counter}', 'memory')
        if geometry is not None:
            feature = QgsFeature()
            feature.setGeometry(geometry)
            layer.dataProvider().addFeatures([feature])
            layer.updateExtents()
        if editable:
            layer.startEditing()
        layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'aoi.qml'))
        self.aoi_layer_counter += 1
        self.result_loader.add_layer(layer)
        self.register_layer(layer)
        return layer

    def create_layer_from_rect(self, rect, crs) -> QgsVectorLayer:
        """An AOI covering ``rect`` (the current map view), reprojected to WGS84."""
        return self._new_aoi_layer(helpers.to_wgs84(QgsGeometry.fromRect(rect), crs))

    def create_layer_from_imagery(self) -> Optional[QgsVectorLayer]:
        """An AOI covering the footprint of the selected My Imagery image or mosaic.

        Returns None when nothing is selected, so the caller can explain why instead of adding
        an empty layer.
        """
        image = self.data_catalog_service.selected_image()
        mosaic = self.data_catalog_service.selected_mosaic()
        if image:
            geometry = QgsGeometry().fromWkt(image.footprint)
        elif mosaic:
            geometry = QgsGeometry().fromWkt(mosaic.footprint)
        else:
            return None
        return self._new_aoi_layer(geometry)

    def create_editable_layer(self) -> QgsVectorLayer:
        """An empty AOI layer left in edit mode for the user to draw into."""
        return self._new_aoi_layer(None, editable=True)
