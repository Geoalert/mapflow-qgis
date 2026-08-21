import os
from typing import List, Optional, Tuple

from PyQt5.QtCore import QObject
from PyQt5.QtNetwork import QNetworkReply
from osgeo import gdal, ogr
from qgis.core import (QgsCoordinateReferenceSystem, QgsFeature, QgsGeometry, QgsLayerTreeLayer,
                       QgsRasterLayer, QgsRectangle, QgsVectorLayer)

from .. import helpers
from .. import layer_utils
from ..app_context import AppContext
from .alert_service import alert, alert_info, alert_warning, report_http_error
from ...config import OSM
from ...errors import ImageIdRequired
from ...schema.catalog import MultiPreviewList, PreviewType


class PreviewService(QObject):
    """Preview *layers on the map*: XYZ tiles, PNG/JPG stills, mosaic tiles, catalog images.

    The boundary is the layer. The My Imagery thumbnail (`get_image_preview_s`) paints a QImage
    into a panel widget and stays with the catalog; anything that puts a raster on the map is
    here, together with the two guards that keep a second copy off it.

    Holds no widget and no dialog (`spec/007_architecture.md` § Layer rules). The search-table
    reads that decide *which* image to preview stay with the caller until
    `view/search_view.py` exists; what arrives here is an image id or a feature.
    """

    def __init__(self,
                 iface,
                 app_context: AppContext,
                 http,
                 plugin_dir: str,
                 config,
                 result_loader,
                 processing_service):
        super().__init__()
        self.iface = iface
        self.app_context = app_context
        self.http = http
        self.plugin_dir = plugin_dir
        self.config = config
        self.result_loader = result_loader
        #: Consulted for the in-template placement rules only. Becomes `TemplateService` when the
        #: templates step splits it out.
        self.processing_service = processing_service
        #: Image ids whose preview is being downloaded. The layer is only added in the HTTP
        #: callback, so the on-map duplicate check cannot see an in-flight one — a rapid second
        #: click would start a second download without this.
        self._pending_preview_ids = set()
        #: The mosaic-preview boundary layer currently shown. Its name varies by acquisition
        #: date, so a name match alone leaves the previous boundary on the map.
        self._mosaic_preview_footprint_id = None

    # ---------- reading the search-metadata layer ----------

    def metadata_feature(self, image_id):
        if not image_id:
            return None
        try:  # Get the image extent to set the correct extent on the raster layer
            return next(self.app_context.metadata_layer.getFeatures(f"id = '{image_id}'"))
        except (RuntimeError, AttributeError, StopIteration):  # layer gone, deleted, or empty
            return None

    def metadata_footprint(self,
                           image_id=None,
                           feature=None,
                           crs: QgsCoordinateReferenceSystem = helpers.WEB_MERCATOR):
        if not feature:
            feature = self.metadata_feature(image_id)
        if not feature:
            return None
        return helpers.from_wgs84(feature.geometry(), crs)

    @staticmethod
    def _feature_attribute(feature, name):
        """``feature.attribute(name)``, or ``None`` when that field does not exist on the layer.

        The OGR GeoJSON reader omits a property that is null in every feature, so My Imagery
        results (all-null ``acquisitionDate`` etc.) lack those columns and a plain
        ``feature.attribute(name)`` would raise ``KeyError``. A NULL value on an existing field
        already comes back as Python ``None``."""
        try:
            return feature.attribute(name)
        except KeyError:
            return None

    # ---------- placement ----------

    def _add_aoi_to_preview_if_needed(self) -> None:
        """Overlay the search AOI on a preview — but not inside a template, where the AOI is
        already drawn as its own layer, so the clone would just duplicate it (feedback 1)."""
        if self.processing_service.in_template_mode:
            return
        self.result_loader.add_aoi_to_preview()

    def _relocate_to_template_group(self, layer) -> None:
        """In the in-template view, move a freshly added preview layer into the template's
        map group, above the search-results footprints and below the AOI subgroups, so the
        precedence is AOIs (top) > previews > search results (bottom)."""
        service = self.processing_service
        if not layer or not service.in_template_mode or not service.active_template:
            return
        settings = self.app_context.settings
        mapflow_group_name = settings.value('layerGroup') or self.app_context.plugin_name
        try:
            template_group = layer_utils.find_template_group(
                self.app_context.project, mapflow_group_name, str(service.active_template.name))
            root = self.app_context.project.layerTreeRoot()
            node = root.findLayer(layer.id())
            if node is None or template_group is None:
                return
            footprints_layer = getattr(self.app_context, 'metadata_layer', None)
            footprints_id = footprints_layer.id() if footprints_layer else None
            children = template_group.children()
            # Default to the bottom; otherwise insert directly above the footprints layer
            # (which itself sits below the AOI/processing subgroups).
            insert_index = len(children)
            for i, child in enumerate(children):
                if isinstance(child, QgsLayerTreeLayer) and child.layerId() == footprints_id:
                    insert_index = i
                    break
            template_group.insertChildNode(insert_index, node.clone())
            (node.parent() or root).removeChildNode(node)
        except (AttributeError, RuntimeError):
            return

    def _move_layer_to_top(self, layer_id: str) -> bool:
        """Move an existing layer's tree node to the top of its parent group."""
        root = self.app_context.project.layerTreeRoot()
        node = root.findLayer(layer_id)
        if not node:
            return False
        parent = node.parent() or root
        parent.insertChildNode(0, node.clone())
        parent.removeChildNode(node)
        return True

    # ---------- entry points ----------

    def preview_catalog(self, image_id):
        feature = self.metadata_feature(image_id)
        if not feature:
            alert(self.tr("Preview is unavailable when metadata layer is removed"))
            return
        # If this image's preview is already on the map (layers are named "<image_id> preview"),
        # just bring it to the top instead of downloading and adding a duplicate.
        existing_preview = self.app_context.project.mapLayersByName(f"{image_id} preview")
        if existing_preview:
            self._move_layer_to_top(existing_preview[0].id())
            self.iface.setActiveLayer(existing_preview[0])
            self.iface.mapCanvas().refresh()
            return
        # A preview for this image is already being downloaded (async): a rapid second click /
        # double-click must not start another download. The preview layer is only added in the
        # HTTP callback, so the on-map guard above cannot catch these — hence this in-flight set.
        if image_id in self._pending_preview_ids:
            return
        footprint = self.metadata_footprint(feature=feature)
        self.iface.mapCanvas().zoomToSelected(self.app_context.metadata_layer)
        self.iface.mapCanvas().refresh()
        # Get multi-image preview (e.g. Roscosmos)
        try:
            previews_list = MultiPreviewList.from_dict_or_string(feature['previews'])
        except KeyError:  # duplicated processings don't have this field
            previews_list = MultiPreviewList([])
        if len(previews_list.previews) != 0:
            previews = []
            for p in previews_list.previews:
                # Create QgsGeometry from GeoJSON through ogr and wkt
                ogr_geom = ogr.CreateGeometryFromJson(str(p.geometry))
                wkt_geom = ogr_geom.ExportToWkt()
                geom = QgsGeometry.fromWkt(wkt_geom)
                previews.append((p.url, geom))
            self._pending_preview_ids.add(image_id)  # in-flight until the VRT is added / errors
            self.preview_multiple_png(response=None,
                                      previews=previews,
                                      footprint=previews[0][1],
                                      image_id=image_id,
                                      georeferenced_previews_list=[])
            return
        # Get single image preview. Read each attribute independently: a My Imagery result may
        # lack whole metadata columns — an all-null acquisitionDate is dropped by the OGR GeoJSON
        # reader, so feature.attribute('acquisitionDate') raises KeyError. A single missing field
        # must not blank out the others (a shared try/except previously reset preview_type to '',
        # so even mosaics with a valid xyz preview reported "no preview"). Duplicated processings
        # likewise lack these fields, and get '' the same way.
        url = self._feature_attribute(feature, 'previewUrl') or ''
        preview_type = self._feature_attribute(feature, 'previewType') or ''
        provider_name = self._feature_attribute(feature, 'providerName') or ''
        raw_date = self._feature_attribute(feature, 'acquisitionDate')
        image_date = raw_date.toString("dd.MM.yyyy") if raw_date else ''
        if not preview_type:
            alert(self.tr("Selected imagery has no preview"))
            return
        # Display image preview
        if preview_type in (PreviewType.png, PreviewType.jpg):
            if not url:
                alert(self.tr("Preview with such URL is unavailable"))
                return
            self._pending_preview_ids.add(image_id)  # in-flight until added / errors
            self.preview_png(url, footprint, image_id)
        # Display mosaic preview
        elif preview_type in (PreviewType.xyz, PreviewType.tms, PreviewType.wms):
            self.preview_mosaic(feature, url, preview_type, provider_name, image_date)
        else:
            alert(self.tr("Preview for '{iid}' is unavailable").format(iid=image_id))
            return

    def preview_xyz(self, provider, image_id):
        max_zoom = self.config.MAX_ZOOM
        layer_name = provider.name
        try:
            url = provider.preview_url(image_id=image_id)
            preview_max_zoom = provider.preview_max_zoom
        except ImageIdRequired:
            alert_warning(self.tr("Provider {name} requires image id for preview!")
                          .format(name=provider.name))
            return
        except NotImplementedError:
            alert_info(self.tr("Preview is unavailable for the provider {}. \n"
                               "OSM layer will be added instead.").format(provider.name))
            # Add OSM instead of preview, if it is unavailable (for Mapbox)
            layer = QgsRasterLayer(OSM, 'OpenStreetMap', 'wms')
            self.result_loader.add_preview_layer(preview_layer=layer)
            return
        except Exception as e:
            # provider.preview_url is provider-supplied and may fail in ways only it knows;
            # the message is the only thing the user can act on, so it is shown rather than
            # narrowed away.
            alert_warning(str(e))
            return
        uri = layer_utils.generate_xyz_layer_definition(url,
                                                        provider.source_type,
                                                        preview_max_zoom or max_zoom,
                                                        provider.credentials.login,
                                                        provider.credentials.password)
        layer = QgsRasterLayer(uri, layer_name, 'wms')
        layer.setCrs(QgsCoordinateReferenceSystem(provider.crs))
        if layer.isValid():
            self.result_loader.add_preview_layer(preview_layer=layer)
        else:
            alert(self.tr("We couldn't load a preview for this image"))

    # ---------- PNG / JPG ----------

    def preview_png(self,
                    url: str,
                    footprint: QgsGeometry,
                    image_id: str = ""):
        # previewUrl is always a self-authenticating (pre-signed) URL — for every provider,
        # including My Imagery — so we send a dummy Authorization header and never leak the
        # Mapflow credentials to the (often third-party) preview host.
        self.http.get(url=url,
                      timeout=30,
                      auth='null'.encode(),
                      callback=self.display_png_preview_gcp,
                      use_default_error_handler=False,
                      error_handler=self.preview_png_error_handler,
                      error_handler_kwargs={"image_id": image_id},
                      callback_kwargs={"footprint": footprint,
                                       "image_id": image_id})

    def display_png_preview(self,
                            response: QNetworkReply,
                            extent: QgsRectangle,
                            crs: QgsCoordinateReferenceSystem = QgsCoordinateReferenceSystem("EPSG:3857"),
                            image_id: str = ""):
        """
        We assume that png preview is not internally georeferenced,
        but the footprint specified in the metadata has the same extent, so we generate georef
        for the image
        """
        with open(self.app_context.temp_dir/os.urandom(32).hex(), mode='wb') as f:
            f.write(response.readAll().data())
        preview = gdal.Open(f.name)
        pixel_xsize = extent.width() / preview.RasterXSize
        pixel_ysize = extent.height() / preview.RasterYSize
        preview.SetProjection(crs.toWkt())
        preview.SetGeoTransform([
            extent.xMinimum(),  # north-west corner x
            pixel_xsize,  # pixel horizontal resolution (m)
            0,  # x-axis rotation
            extent.yMaximum(),  # north-west corner y
            0,  # y-axis rotation
            -pixel_ysize  # pixel vertical resolution (m)
        ])
        preview.FlushCache()
        layer = QgsRasterLayer(f.name, f"{image_id} preview", 'gdal')
        layer.setExtent(extent)
        self.app_context.project.addMapLayer(layer)

    def display_png_preview_gcp(self,
                                response: QNetworkReply,
                                footprint: QgsGeometry,
                                crs: QgsCoordinateReferenceSystem = QgsCoordinateReferenceSystem("EPSG:3857"),
                                image_id: str = ""):
        """
        Display image preview using Ground Control Points from footprint corners.
        Delegates to ResultsLoader.display_preview_with_gcp().
        """
        layer = self.result_loader.display_preview_with_gcp(
            response=response,
            footprint=footprint,
            crs=crs,
            image_name=image_id,
            # Don't clone the AOI over the preview inside a template: the AOI is already drawn
            # as its own layer there, so the "Search area" clone just duplicates it (feedback 1).
            add_aoi=not self.processing_service.in_template_mode,
        )
        self._pending_preview_ids.discard(image_id)  # download finished
        self._relocate_to_template_group(layer)

    def preview_multiple_png(self,
                             response: QNetworkReply,
                             previews: List[Tuple[str, QgsGeometry]],
                             footprint: QgsGeometry,
                             image_id: str = "",
                             georeferenced_previews_list: Optional[List[str]] = None):
        " Add preview for multi-part images (e.g. Roscosmos). "
        if georeferenced_previews_list is None:
            georeferenced_previews_list = []
        # Callback part: collect response images into a list
        if response:
            georeferenced_preview = self.result_loader.georeference_preview_part(
                response=response, footprint=footprint, crs=helpers.WGS84)
            georeferenced_previews_list.append(georeferenced_preview)
        # Final part: merge all collected images into one VRT
        if len(previews) == 0:
            vrt_path = os.path.join(self.app_context.temp_dir, os.urandom(32).hex())
            vrt = gdal.BuildVRT(vrt_path, georeferenced_previews_list)
            vrt.FlushCache()
            vrt = None
            vrt_layer = QgsRasterLayer(vrt_path, f"{image_id} preview", 'gdal')
            self._pending_preview_ids.discard(image_id)  # multi-part download finished
            self.result_loader.add_layer(vrt_layer)
            self._add_aoi_to_preview_if_needed()
            self._relocate_to_template_group(vrt_layer)
            return
        # Request part: remove first image from the list and get its preview
        image_to_preview = previews.pop(0)
        self.http.get(url=image_to_preview[0],
                      timeout=30,
                      auth='null'.encode(),
                      callback=self.preview_multiple_png,
                      use_default_error_handler=False,
                      error_handler=self.preview_png_error_handler,
                      error_handler_kwargs={"image_id": image_id},
                      callback_kwargs={"previews": previews,
                                       "footprint": image_to_preview[1],
                                       "image_id": image_id,
                                       "georeferenced_previews_list": georeferenced_previews_list})

    def preview_png_error_handler(self, response: QNetworkReply, image_id: str = ""):
        # Clear the in-flight flag so the user can retry this image's preview after a failure.
        self._pending_preview_ids.discard(image_id)
        report_http_error(response,
                          plugin_version=self.app_context.plugin_version,
                          title=self.tr("Could not display preview"))

    # ---------- mosaic tiles ----------

    def preview_mosaic(self,
                       feature: QgsFeature,
                       url: str,
                       preview_type: str,
                       provider_name: str,
                       image_date: str):
        uri = layer_utils.generate_xyz_layer_definition(url=url, source_type=preview_type)
        tile_layer = QgsRasterLayer(uri, provider_name, "wms")
        tiles_to_delete = [
            layer.id() for layer in self.app_context.project.mapLayers().values()
            if layer.dataProvider().dataSourceUri() == tile_layer.dataProvider().dataSourceUri()]
        self.app_context.project.removeMapLayers(tiles_to_delete)
        self.result_loader.add_layer(layer=tile_layer, order=0)
        self._relocate_to_template_group(tile_layer)
        # Add footprint layer
        if feature:
            footprint_layer = QgsVectorLayer("Polygon?crs=EPSG:4326",
                                             f"{provider_name}_{image_date}",
                                             "memory")
            footprint_layer.dataProvider().addFeatures([feature])
            footprint_layer.updateExtents()
            footprint_layer.loadNamedStyle(
                os.path.join(self.plugin_dir, 'static', 'styles', 'metadata_footprint.qml'))
            # Remove same-named boundaries AND the previously shown one (its name varies by
            # acquisition date, so a name match alone leaves the old boundary on the map).
            footprints_to_delete = [
                layer.id() for layer in self.app_context.project.mapLayers().values()
                if layer.name() == footprint_layer.name()]
            if self._mosaic_preview_footprint_id:
                footprints_to_delete.append(self._mosaic_preview_footprint_id)
            self.app_context.project.removeMapLayers(footprints_to_delete)
            self.result_loader.add_layer(layer=footprint_layer, order=0)
            self._mosaic_preview_footprint_id = footprint_layer.id()
            self._relocate_to_template_group(footprint_layer)
        self._add_aoi_to_preview_if_needed()
