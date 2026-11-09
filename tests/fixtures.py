"""API payloads shaped like Mapflow's responses (fields the plugin reads, plus a few it must ignore)."""
import copy


def block(name, display, price, optional):
    return {"name": name, "displayName": display, "price": price, "optional": optional, "extra": "ignored"}


BUILDINGS = {"id": "wd-buildings", "name": "🏠 Buildings", "description": "Roofs of buildings",
             "blocks": [block("buildings", "Buildings", 10, False), block("classification", "Classification", 0, True),
                        block("heights", "Building heights", 10, True),
                        block("simplification", "Simplification", 0, True)]}
FOREST = {"id": "wd-forest", "name": "🌲 Forest and trees", "description": "",
          "blocks": [block("forest", "Forest", 8, False), block("heights", "Forest heights", 10, True),
                     block("crowns", "Tree crowns", 10, True)]}
ROADS = {"id": "wd-roads", "name": "🚗 Roads", "pricePerSqKm": 5, "blocks": []}
MULTI = {"id": "wd-multi", "name": "[multi] Buildings + Roads + Forest", "blocks": [block("all", "All", 23, False)]}
OPEN_DATA = {"id": "wd-open", "name": "Download Open Data", "blocks": [block("osm", "OSM", 1, False)]}

MAPBOX = {"id": "dp-1", "name": "mapbox", "displayName": "Mapbox Satellite",
          "price": [{"zoom": 17, "priceSqKm": 1}, {"zoom": 18, "priceSqKm": 3}, {"zoom": 19, "priceSqKm": 9}],
          "previewUrl": "https://api.mapbox.example/{z}/{x}/{y}.jpg", "previewUrlMaxZoom": 19}
ARCGIS = {"id": "dp-2", "name": "arcgis", "displayName": "ArcGIS World Imagery",
          "price": [{"zoom": 18, "priceSqKm": 3}, {"zoom": 19, "priceSqKm": 9}]}

STATUS = {"billingType": "CREDITS", "remainingCredits": 1240, "remainingArea": 0, "dataProviders": [MAPBOX, ARCGIS],
          "searchDataProviders": [{"name": "maxar"}], "reviewWorkflowEnabled": False, "maxAoisPerProcessing": 10}

USER = {"id": "u-1", "email": "me@example.com", "role": "USER", "aoiAreaLimit": 100e6}
PROJECT = {"id": "project-1", "name": "Downtown survey", "isDefault": True, "description": None,
           "workflowDefs": [BUILDINGS, FOREST, ROADS, MULTI, OPEN_DATA], "shareProject": None, "user": USER}
PROJECT_2 = dict(copy.deepcopy(PROJECT), id="project-2", name="Harbor", isDefault=False,
                 description="Port and storage yards, quarterly updates",
                 processingCounts={"succeeded": 12, "failed": 1}, updated="2026-11-05T09:00:00Z",
                 shareProject={"owners": [{"email": "me@example.com", "role": "owner"}],
                               "users": [{"email": "ana@example.com", "role": "contributor"},
                                         {"email": "li@example.com", "role": "readonly"}]})
# Many more, for search and "Show more" in the projects window: 2 + 43 = 45 projects
MORE_PROJECTS = [dict(copy.deepcopy(PROJECT), id=f"project-{n}", name=f"Field site {n:02d}", isDefault=False,
                      description=f"Survey area {n}", processingCounts={"succeeded": n % 7, "failed": n % 2},
                      updated=f"2026-10-{(n % 28) + 1:02d}T09:00:00Z")
                 for n in range(3, 46)]


def processing_json(pid, status="IN_PROGRESS", percent=0, name="Buildings · Old town", area=2.4e6, cost=70):
    return {"id": pid, "name": name, "projectId": "project-1", "status": status, "percentCompleted": percent,
            "description": None, "workflowDef": {"id": "wd-buildings", "name": "🏠 Buildings"},
            "aoiArea": area, "cost": cost, "created": "2026-11-07T10:00:00Z",
            "rasterLayer": {"tileUrl": "", "tileJsonUrl": ""},
            "vectorLayer": {"tileUrl": "https://tiles.example/{z}/{x}/{y}.pbf", "tileJsonUrl": ""},
            "messages": [], "params": {"sourceParams": {"dataProvider": {"providerName": "mapbox", "zoom": "18"}}},
            "blocks": [{"name": "classification", "enabled": True}, {"name": "heights", "enabled": False}],
            "reviewStatus": None}


RESULT = {"type": "FeatureCollection", "features": [
    {"type": "Feature", "properties": {"id": i, "class_id": 101, "area": 120.5, "bbox": {"xmin": 0}},
     "geometry": {"type": "Polygon", "coordinates": [[
         [37.60 + i * 0.001, 55.75], [37.6005 + i * 0.001, 55.75], [37.6005 + i * 0.001, 55.7504],
         [37.60 + i * 0.001, 55.7504], [37.60 + i * 0.001, 55.75]]]}}
    for i in range(5)]}

CATALOG = {"images": [
    {"id": "img-1", "providerName": "maxar", "productType": "Image", "acquisitionDate": "2026-08-30T08:00:00Z",
     "cloudCover": 4, "offNadirAngle": 12, "pixelResolution": 0.5, "zoom": "18", "previewType": "png",
     "previewUrl": "", "aoiIntersectionPercent": 92,
     "footprint": {"type": "Polygon", "coordinates": [[
         [37.59, 55.74], [37.62, 55.74], [37.62, 55.76], [37.59, 55.76], [37.59, 55.74]]]}},
    {"id": "img-2", "providerName": "my_imagery_mosaics", "productType": "Mosaic", "acquisitionDate": None,
     "cloudCover": None, "pixelResolution": 0.3, "previewType": "xyz", "previewUrl": "",
     "footprint": {"type": "Polygon", "coordinates": [[
         [37.58, 55.73], [37.63, 55.73], [37.63, 55.77], [37.58, 55.77], [37.58, 55.73]]]}}],
    "total": 2, "limit": 50, "offset": 0}

MOSAICS = [{"id": "m-1", "name": "Drone survey March", "created_at": "2026-10-01T12:00:00Z", "sizeInBytes": 734003200,
            "footprint": "POLYGON((37.6 55.75, 37.61 55.75, 37.61 55.76, 37.6 55.76, 37.6 55.75))",
            "rasterLayer": {"tileUrl": "https://tiles.example/m-1/{z}/{x}/{y}.png", "tileJsonUrl": ""}, "tags": []},
           {"id": "m-2", "name": "Beirut", "created_at": "2026-11-02T18:37:28Z", "sizeInBytes": 18459276,
            "footprint": "POLYGON((35.5 33.89, 35.51 33.89, 35.51 33.9, 35.5 33.9, 35.5 33.89))",
            "rasterLayer": {"tileUrl": "https://tiles.example/m-2/{z}/{x}/{y}.png", "tileJsonUrl": ""}, "tags": [],
            "status_summary": {"total": 1, "ready": 1}}]


def _strip(south, north, west=37.6, east=37.61):
    return f"POLYGON(({west} {south}, {east} {south}, {east} {north}, {west} {north}, {west} {south}))"


# Each image's footprint: m-1 is three strips (north, centre, south) of its 37.60–37.61 × 55.75–55.76 extent
IMAGE_FOOTPRINTS = {"north.tif": _strip(55.7567, 55.76), "centre.tif": _strip(55.7533, 55.7567),
                    "south.tif": _strip(55.75, 55.7533), "beirut_0.5m.tif": _strip(33.89, 33.9, 35.5, 35.51)}


def mosaic_image(image_id, mosaic_id, filename, api_url=""):
    return {"id": image_id, "mosaic_id": mosaic_id, "image_url": f"s3://bucket/{filename}",
            "preview_url_s": f"{api_url}/rasters/image/{image_id}/preview/s",
            "preview_url_l": f"{api_url}/rasters/image/{image_id}/preview/l",
            "uploaded_at": "2026-10-01T12:00:00Z", "file_size": 244667733,
            "footprint": IMAGE_FOOTPRINTS[filename],
            "filename": filename, "meta_data": {"crs": "EPSG:3857", "pixel_size": [0.15, 0.15]}}


MOSAIC_IMAGES = {"m-1": ["north.tif", "centre.tif", "south.tif"], "m-2": ["beirut_0.5m.tif"]}
