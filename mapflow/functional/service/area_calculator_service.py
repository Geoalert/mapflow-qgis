from typing import Union, List
from PyQt5.QtCore import QObject
from qgis.core import QgsVectorLayer, QgsWkbTypes, QgsGeometry, QgsProject, QgsFeature, QgsCoordinateReferenceSystem
from ..app_context import AppContext
from .. import layer_utils
from ...dialogs import MainDialog
from ...entity.provider import MyImageryProvider

class AreaCalculatorService(QObject):
    def __init__(self,
                 app_context: AppContext,
                 qgs_project: QgsProject,
                 dlg: MainDialog):
        self.app_context = app_context
        self.qgs_project = qgs_project
        self.dlg = dlg

    def get_aoi_area_polygon_layer(self, layer: Union[QgsVectorLayer, None]) -> None:
        if not layer or layer.featureCount() == 0:
            if not self.app_context.user_role.can_start_processing:
                reason = self.tr('Not enough rights to start processing in a shared project ({})').format(self.app_context.user_role.value)
            else:
                reason = self.tr('Set AOI to start processing')
            self.dlg.disable_processing_start(reason, clear_area=True)
            self.app_context.aoi = self.app_context.aoi_size = None
            return

        features = list(layer.getSelectedFeatures()) or list(layer.getFeatures())
        if QgsWkbTypes.flatType(layer.wkbType()) == QgsWkbTypes.Polygon:
            geoms_count = len(features)
        elif QgsWkbTypes.flatType(layer.wkbType()) == QgsWkbTypes.MultiPolygon:
            geoms_count = layer_utils.count_polygons_in_layer(features)
        else: # type of layer is not supported
            # (but it shouldn't be the case, because point and line layers will not appear in AOI-combo,
            # and collections are devided by QGIS into separate layers with different types)
            raise ValueError("Only polygon and multipolyon layers supported for this operation")
        if self.app_context.max_aois_per_processing >= geoms_count:
            if len(features) == 1:
                aoi = features[0].geometry()
            else:
                aoi = QgsGeometry.collectGeometry([feature.geometry() for feature in features])
            self.calculate_aoi_area(aoi, layer.crs())
            return aoi
        else:  # self.app_context.max_aois_per_processing < number of polygons (as features and as parts of multipolygons):
            if not self.app_context.user_role.can_start_processing:
                reason = self.tr('Not enough rights to start processing in a shared project ({})').format(self.app_context.user_role.value)
            else:
                reason = self.tr('AOI must contain not more than {} polygons').format(self.app_context.max_aois_per_processing)
            self.dlg.disable_processing_start(reason, clear_area=True)
            self.app_context.aoi = self.app_context.aoi_size = None

    def calculate_aoi_area_polygon_layer(self, layer: Union[QgsVectorLayer, None]) -> None:
        """Get the AOI size total when polygon another layer is chosen,
        current layer's selection is changed or the layer's features are modified.

        :param layer: The current polygon layer
        """
        self.get_aoi_area_polygon_layer(layer)
        provider = self.app_context.provider
        if isinstance(provider, MyImageryProvider):
            self.calculate_aoi_area_catalog()

    def calculate_aoi_area_use_image_extent(self) -> None:
        """Get the AOI size when the Use image extent checkbox is toggled.

        :param use_image_extent: The current state of the checkbox
        """
        provider = self.providers[self.dlg.providerIndex()]
        if isinstance(provider, MyImageryProvider):
            self.calculate_aoi_area_catalog()
        else:
            self.calculate_aoi_area_polygon_layer(self.dlg.polygonCombo.currentLayer())

    def calculate_aoi_area_catalog(self) -> None:
        """Get the AOI size when a new mosaic or image in 'My imagery' is selected.
        """
        # If different provider is chosen, set it to My imagery
        self.data_catalog_service.set_catalog_provider(self.providers)
        image = self.data_catalog_service.selected_image()
        mosaic = self.data_catalog_service.selected_mosaic()
        if image or mosaic:
            self.use_imagery_extent.setEnabled(True)
            if image:
                catalog_aoi = QgsGeometry().fromWkt(image.footprint)
                self.use_imagery_extent.setText(self.tr("Use extent of '{name}'").format(name=image.filename))
            else:
                catalog_aoi = QgsGeometry().fromWkt(mosaic.footprint)
                self.use_imagery_extent.setText(self.tr("Use extent of '{name}'").format(name=mosaic.name))
            aoi = layer_utils.get_catalog_aoi(catalog_aoi=catalog_aoi,
                                              selected_aoi=self.app_context.aoi)
        else:
            aoi = self.get_aoi_area_polygon_layer(self.dlg.polygonCombo.currentLayer())
            self.use_imagery_extent.setText(self.tr("Use imagery extent"))
            self.use_imagery_extent.setEnabled(False)
        if not self.app_context.aoi:  # other error message is already shown
            pass
        elif not aoi:  # error after intersection
            self.dlg.disable_processing_start(reason=self.tr("Selected AOI does not intersect the selected imagery"),
                                              clear_area=True)
            return
        # Don't recalculate AOI if first selected mosaic/image didn't change
        selected_mosaics = self.dlg.mosaicTable.selectedIndexes()
        selected_images = self.dlg.imageTable.selectedIndexes()
        if len(selected_mosaics) > 1 and self.dlg.selected_mosaic_cell == selected_mosaics[0] \
                or len(selected_images) > 1 and self.dlg.selected_image_cell == selected_images[0]:
            return
        self.calculate_aoi_area(aoi, helpers.WGS84)

    def calculate_aoi_area_selection(self, _: List[QgsFeature]) -> None:
        """Get the AOI size when the selection changed on a polygon layer.

        :param _: A list of currently selected features
        """
        layer = self.dlg.polygonCombo.currentLayer()
        if layer == self.iface.activeLayer():
            self.calculate_aoi_area_polygon_layer(layer)

    def calculate_aoi_area_layer_edited(self) -> None:
        """Get the AOI size when a feature is added or remove from a layer."""
        layer = self.sender()
        if layer == self.dlg.polygonCombo.currentLayer():
            self.calculate_aoi_area_polygon_layer(layer)

    def calculate_aoi_area(self, aoi: QgsGeometry, crs: QgsCoordinateReferenceSystem) -> None:
        """Display the AOI size in sq.km.
            This is the only place where app_context.aoi is changed! This is important because it is the place where we
            send request to update processing cost!
        :param aoi: the processing area.
        :param crs: the CRS of the processing area.
        """
        if crs != helpers.WGS84:
            aoi = helpers.to_wgs84(aoi, crs)

        self.app_context.aoi = aoi  # save for reuse in processing creation or metadata requests
        # fetch UI data
        provider_index = self.dlg.providerIndex()
        selected_images = self.dlg.metadataTable.selectedItems()
        if selected_images:
            rows = list(set(image.row() for image in selected_images))
            local_image_indices = [int(self.dlg.metadataTable.item(row, self.config.LOCAL_INDEX_COLUMN).text())
                                   for row in rows]
        else:
            local_image_indices = []
        # This is AOI with respect to selected Maxar images and raster image extent
        try:
            real_aoi = self.get_aoi(provider_index=provider_index,
                                    local_image_indices=local_image_indices,
                                    selected_aoi=self.app_context.aoi)
        except ImageIdRequired:
            # AOI is OK, but image ID is not selected,
            # in this case we should use selected AOI without cut by AOI
            real_aoi = self.app_context.aoi
        except Exception as e:
            # Could not calculate AOI size
            real_aoi = QgsGeometry()
        try:
            self.app_context.aoi_size = layer_utils.calculate_aoi_area(real_aoi,
                                                                       self.app_context.project.transformContext())
        except Exception as e:
            self.app_context.aoi_size = 0

        self.dlg.labelAoiArea.setText(self.tr('Area: {:.2f} sq.km').format(self.app_context.aoi_size))
        self.processing_service.update_processing_cost()
