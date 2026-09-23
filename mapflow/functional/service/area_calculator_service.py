from typing import Union, List, Optional
from PyQt5.QtCore import QObject, pyqtSignal
from qgis.core import QgsVectorLayer, QgsWkbTypes, QgsGeometry, QgsFeature, QgsCoordinateReferenceSystem
from ..app_context import AppContext
from .. import layer_utils
from .. import helpers
from ...model.provider import (ImagerySearchProvider,
                                MyImageryProvider)
from ...errors import (BadProcessingInput,
                       PluginError,
                       ImageIdRequired,
                       AoiNotIntersectsImage)
from ..geometry import clip_aoi_to_image_extent


class AreaCalculatorService(QObject):
    """Computes the processing AOI and its area, and prices it. It reads no widget: the AOI polygon
    layer, the chosen provider and the selected search images all arrive on `app_context` (pushed
    from the composition root), and what the panel must show leaves as a signal (`spec/007
    § Services`)."""

    #: (reason, clear the area label too) — a start is blocked.
    startDisabled = pyqtSignal(str, bool)
    #: The AOI area in sq.km, to show on the label.
    areaChanged = pyqtSignal(float)
    #: (enabled, label text) for the "Use imagery extent" action.
    imageryExtentChanged = pyqtSignal(bool, str)

    def __init__(self,
                 iface,
                 app_context: AppContext,
                 config,
                 data_catalog_service,
                 processing_service,
                 provider_service
                 ):
        super().__init__()
        self.iface = iface
        self.app_context = app_context
        self.config = config
        self.data_catalog_service = data_catalog_service
        self.processing_service = processing_service
        self.provider_service = provider_service
        #: The catalog AOI last priced, so a secondary multi-select that leaves the effective area
        #: unchanged does not fire a redundant cost request. Content-based rather than the old
        #: comparison of table cell indices, which a service can no longer read.
        self._last_catalog_aoi_wkt = None

    def get_aoi_area_polygon_layer(self, layer: Union[QgsVectorLayer, None]) -> None:
        if not layer or layer.featureCount() == 0:
            if not self.app_context.user_role.can_start_processing:
                reason = self.tr('Not enough rights to start processing in a shared project ({})').format(self.app_context.user_role.value)
            else:
                reason = self.tr('Set AOI to start processing')
            self.startDisabled.emit(reason, True)
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
            self.startDisabled.emit(reason, True)
            self.app_context.aoi = self.app_context.aoi_size = None

    def calculate_aoi_area_polygon_layer(self, layer: Union[QgsVectorLayer, None]) -> None:
        """Get the AOI size total when polygon another layer is chosen,
        current layer's selection is changed or the layer's features are modified.

        :param layer: The current polygon layer
        """
        self.get_aoi_area_polygon_layer(layer)
        if isinstance(self.app_context.data_provider, MyImageryProvider):
            self.calculate_aoi_area_catalog()

    def calculate_aoi_area_use_image_extent(self) -> None:
        """Get the AOI size when the Use image extent checkbox is toggled."""
        if isinstance(self.app_context.data_provider, MyImageryProvider):
            self.calculate_aoi_area_catalog()
        else:
            self.calculate_aoi_area_polygon_layer(self.app_context.aoi_layer)

    def calculate_aoi_area_catalog(self) -> None:
        """Get the AOI size when a new mosaic or image in 'My imagery' is selected.
        """
        # If different provider is chosen, set it to My imagery
        self.data_catalog_service.set_catalog_provider(self.provider_service.providers)
        image = self.data_catalog_service.selected_image()
        mosaic = self.data_catalog_service.selected_mosaic()
        if image or mosaic:
            if image:
                catalog_aoi = QgsGeometry().fromWkt(image.footprint)
                self.imageryExtentChanged.emit(True, self.tr("Use extent of '{name}'").format(name=image.filename))
            else:
                catalog_aoi = QgsGeometry().fromWkt(mosaic.footprint)
                self.imageryExtentChanged.emit(True, self.tr("Use extent of '{name}'").format(name=mosaic.name))
            aoi = layer_utils.get_catalog_aoi(catalog_aoi=catalog_aoi,
                                              selected_aoi=self.app_context.aoi)
        else:
            aoi = self.get_aoi_area_polygon_layer(self.app_context.aoi_layer)
            self.imageryExtentChanged.emit(False, self.tr("Use imagery extent"))
        if not self.app_context.aoi:  # other error message is already shown
            pass
        elif not aoi:  # error after intersection
            self.startDisabled.emit(self.tr("Selected AOI does not intersect the selected imagery"), True)
            return
        # Don't re-price the catalog AOI if the effective area did not change (e.g. a secondary
        # multi-select). Compared by geometry rather than by table cell, which is not the service's
        # to read.
        aoi_wkt = aoi.asWkt() if aoi else None
        if aoi_wkt is not None and aoi_wkt == self._last_catalog_aoi_wkt:
            return
        self._last_catalog_aoi_wkt = aoi_wkt
        self.calculate_aoi_area(aoi, helpers.WGS84)

    def calculate_aoi_area_selection(self, _: List[QgsFeature]) -> None:
        """Get the AOI size when the selection changed on a polygon layer.

        :param _: A list of currently selected features
        """
        layer = self.app_context.aoi_layer
        if layer == self.iface.activeLayer():
            self.calculate_aoi_area_polygon_layer(layer)

    def calculate_aoi_area_layer_edited(self) -> None:
        """Get the AOI size when a feature is added or remove from a layer."""
        layer = self.sender()
        if layer == self.app_context.aoi_layer:
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

        # The chosen provider and the selected search images are pushed to app_context, so the
        # service need not read the source combo or the metadata table.
        provider = self.app_context.data_provider
        local_image_indices = [int(index) for index in (self.app_context.selected_search_indices or [])]
        # This is AOI with respect to selected search images and raster image extent
        try:
            real_aoi = self.get_aoi(provider=provider,
                                    local_image_indices=local_image_indices,
                                    selected_aoi=self.app_context.aoi)
        except ImageIdRequired:
            # AOI is OK, but image ID is not selected,
            # in this case we should use selected AOI without cut by AOI
            real_aoi = self.app_context.aoi
        except PluginError:
            # The domain refusals get_aoi raises — bad AOI bounds, providers not initialized,
            # an AOI that misses the selected image. Anything else is a bug and must reach the
            # error guard rather than silently price an empty geometry.
            real_aoi = QgsGeometry()
        # The cropped AOI is what is actually processed — keep it so the request geometry
        # matches the displayed area instead of sending the whole (uncropped) AOI.
        self.app_context.processing_aoi = real_aoi
        try:
            self.app_context.aoi_size = layer_utils.calculate_aoi_area(real_aoi,
                                                                       self.app_context.project.transformContext())
        except (TypeError, ValueError):
            # measureArea rejects what it was handed; an unmeasurable AOI prices as zero.
            self.app_context.aoi_size = 0

        self.areaChanged.emit(self.app_context.aoi_size)
        if self.app_context.aoi_size > 0:
            self.processing_service.update_processing_cost()

    def get_aoi(self,
                provider,
                selected_aoi: QgsGeometry,
                local_image_indices: Optional[List[int]]) -> QgsGeometry:
        if not helpers.check_aoi(selected_aoi):
            raise BadProcessingInput(self.tr('Bad AOI. AOI must be inside boundaries:'
                                             ' \n[-180, 180] by longitude, [-90, 90] by latitude'))
        else:
            if not provider:
                raise PluginError(self.tr('Providers are not initialized'))
            if len(local_image_indices) != 0:
                if isinstance(provider, ImagerySearchProvider):
                    aoi = self.crop_aoi_with_image_footprint(selected_aoi, local_image_indices)
                    if not aoi:
                        raise AoiNotIntersectsImage()
                else:
                    aoi = selected_aoi
                    # We ignore image ID if the provider does not support it
            elif provider.requires_image_id:
                aoi = selected_aoi
                # raise PluginError(self.tr("Please select image in Search table for {}").format(provider.name))
            elif isinstance(provider, MyImageryProvider):
                image = self.data_catalog_service.selected_image()
                mosaic = self.data_catalog_service.selected_mosaic()
                if image:
                    catalog_aoi = QgsGeometry().fromWkt(image.footprint)
                elif mosaic:
                    catalog_aoi = QgsGeometry().fromWkt(mosaic.footprint)
                if image or mosaic:
                    aoi = layer_utils.get_catalog_aoi(catalog_aoi=catalog_aoi,
                                                      selected_aoi=selected_aoi)
                    if not aoi:
                        raise AoiNotIntersectsImage()
                    aoi = selected_aoi
                else:
                    aoi = selected_aoi
            else:
                aoi = selected_aoi
        return aoi

    def crop_aoi_with_image_footprint(self,
                                      aoi: QgsFeature,
                                      local_image_indices: List[int]):
        extents = [self.app_context.search_footprints[local_image_index] for local_image_index in local_image_indices]
        try:
            extents = [self.app_context.search_footprints[local_image_index] for local_image_index in local_image_indices]
            clipped_aoi_features = clip_aoi_to_image_extent(aoi, extents)
            aoi = QgsGeometry.fromWkt('GEOMETRYCOLLECTION()')
            for feature in clipped_aoi_features:
                geom = feature.geometry()
                aoi = aoi.combine(geom)
        except StopIteration:
            raise AoiNotIntersectsImage() from None
        return aoi
