import json
import logging
from typing import List

from osgeo import ogr
from qgis import processing as qgis_processing  # to avoid collisions
from qgis.core import (
    QgsCoordinateReferenceSystem, QgsDistanceArea,
    QgsFeature, QgsFeatureIterator, QgsGeometry, QgsProcessingException,
    QgsProject, QgsVectorLayer,
)

# What a failing qgis_processing.run() raises: QgsProcessingException when the algorithm
# itself rejects the input (the invalid-geometry case these fallbacks exist for), KeyError
# if it returns without the 'OUTPUT' key. Anything else is unexpected and gets logged
# rather than silently treated as "geometry needs repair".
PROCESSING_FAILURES = (QgsProcessingException, KeyError)

logger = logging.getLogger(__name__)


def make_distance_calculator() -> QgsDistanceArea:
    """Return a QgsDistanceArea configured for WGS84 ellipsoidal measurements."""
    calculator = QgsDistanceArea()
    wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
    calculator.setEllipsoid("WGS84")
    calculator.setSourceCrs(wgs84, QgsProject.instance().transformContext())
    return calculator


def geojson_feature_area_sqkm(feature: dict, calculator: QgsDistanceArea) -> float:
    """Return the area of a GeoJSON feature dict in sq km, or 0.0 on failure."""
    geom_dict = feature.get("geometry")
    if not geom_dict:
        return 0.0
    ogr_geom = ogr.CreateGeometryFromJson(json.dumps(geom_dict))
    if ogr_geom is None:
        return 0.0
    geom = QgsGeometry.fromWkt(ogr_geom.ExportToWkt())
    if not geom or geom.isEmpty():
        return 0.0
    return calculator.measureArea(geom) / 1e6

def clip_aoi_to_image_extent(aoi_geometry: QgsGeometry,
                             extents: List[QgsFeature]) -> QgsFeatureIterator:
    """Clip user AOI to image extent if the image doesn't cover the entire AOI.
    args:
        aoi_geometry: AOI geometry - selected by user area of interest (input)
        extents: list of QgsFeature objects from image extent(s) (overlay)
    """
    aoi_layer = QgsVectorLayer('Polygon?crs=epsg:4326', '', 'memory')
    aoi = QgsFeature()
    aoi.setGeometry(aoi_geometry)
    aoi_layer.dataProvider().addFeatures([aoi])
    aoi_layer.updateExtents()
    # Create a temp layer for the image extent
    image_extent_layer = QgsVectorLayer('MultiPolygon?crs=epsg:4326', '', 'memory')
    image_extent_layer.dataProvider().addFeatures(extents)
    image_extent_layer.updateExtents()
    try:
        # Find the intersection
        intersection = intersect_geoms(aoi_layer, image_extent_layer)
    except PROCESSING_FAILURES:
        intersection = None
    except Exception:
        logger.exception("Unexpected error intersecting AOI with image extents; "
                         "retrying with repaired geometries")
        intersection = None
    if intersection is None:
        # If intersection function fails, fix mosaic geometries beforehand
        fixed_image_layer = fix_geoms(image_extent_layer)
        fixed_aoi_layer = fix_geoms(aoi_layer)
        # And then use fixed layers for intersection
        intersection = intersect_geoms(fixed_aoi_layer, fixed_image_layer)
    return intersection.getFeatures()

def clip_aoi_to_catalog_extent(catalog_aoi: QgsGeometry,
                               selected_aoi: QgsGeometry) -> QgsFeatureIterator:
    # Create AOI layer from WGS84 geometry
    aoi_layer = QgsVectorLayer('Polygon?crs=epsg:4326', '', 'memory')
    aoi_feature = QgsFeature()
    aoi_feature.setGeometry(selected_aoi)
    aoi_layer.dataProvider().addFeatures([aoi_feature])
    aoi_layer.updateExtents()
    # Create a layer from chosen mosaic or image footprint
    catalog_layer = QgsVectorLayer('Polygon?crs=epsg:4326', '', 'memory')
    catalog_feature = QgsFeature()
    catalog_feature.setGeometry(catalog_aoi)
    catalog_layer.dataProvider().addFeatures([catalog_feature])
    catalog_layer.updateExtents()
    try:
        # Find the intersection
        intersection = intersect_geoms(aoi_layer, catalog_layer)
    except PROCESSING_FAILURES:
        intersection = None
    except Exception:
        logger.exception("Unexpected error intersecting AOI with the catalog extent; "
                         "retrying with repaired geometries")
        intersection = None
    if intersection is None:
        # If intersection function fails, fix geometries beforehand
        fixed_aoi_layer = fix_geoms(aoi_layer)
        fixed_catalog_layer = fix_geoms(catalog_layer)
        # And then use fixed layers for intersection
        intersection = intersect_geoms(fixed_aoi_layer, fixed_catalog_layer)
    return intersection.getFeatures()

def fix_geoms(layer: QgsVectorLayer) -> QgsVectorLayer:
    """Repair a layer's geometries, falling back through progressively weaker methods.

    METHOD 1 is structure repair (union); METHOD 0 is linework repair, which keeps areas
    that don't overlap. Try the stronger repair first, fall back to the weaker one, and
    hand back the original if neither works — a caller holding the unrepaired layer is no
    worse off than before it asked.
    """
    for method, description in ((1, "structure repair"), (0, "linework repair")):
        try:
            return qgis_processing.run(
                'native:fixgeometries',
                {'INPUT': layer, 'METHOD': method, 'OUTPUT': 'memory:'}
            )['OUTPUT']
        except PROCESSING_FAILURES:
            continue
        except Exception:
            logger.exception("Unexpected error during %s of geometries", description)
            continue
    return layer

def intersect_geoms(input_layer: QgsVectorLayer, 
                    overlay_layer: QgsVectorLayer) -> QgsVectorLayer:
    intersection = qgis_processing.run('qgis:intersection',
                                       {'INPUT': input_layer, 'OVERLAY': overlay_layer, 'OUTPUT': 'memory:'}
                                      )['OUTPUT']
    return intersection