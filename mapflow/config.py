import time


TIMEZONE = time.localtime().tm_zone
PLUGIN_NAME = 'Mapflow'
MAPFLOW_DEFAULT_TIMEOUT = 5  # in seconds
# PROCESSINGS
PROCESSING_TABLE_REFRESH_INTERVAL = 6  # in seconds
PROCESSING_ATTRIBUTES = 'name', 'workflowDef', 'status', 'percentCompleted', 'aoiArea', 'created', 'id'
PROCESSING_TABLE_ID_COLUMN_INDEX = PROCESSING_ATTRIBUTES.index('id')
PROCESSING_TABLE_SORT_COLUMN_INDEX = PROCESSING_ATTRIBUTES.index('created')
# MAXAR
MAXAR_METADATA_ATTRIBUTES = {
    'Product Type': 'productType',
    'Band Order': 'colorBandOrder', 
    'Cloud Cover %': 'cloudCover', 
    'Off Nadir Angle': 'offNadirAngle', 
    f'Date & Time ({TIMEZONE})': 'acquisitionDate',
    'Image ID': 'featureId'
}
MAXAR_METADATA_ID_COLUMN_INDEX = list(MAXAR_METADATA_ATTRIBUTES.values()).index('featureId')
MAXAR_MAX_FREE_ZOOM = 12
MAXAR_PRODUCTS = {
    'Maxar SecureWatch': {
        'url': 'https://securewatch.digitalglobe.com/earthservice/wmtsaccess?SERVICE=WMTS&VERSION=1.0.0&STYLE=&REQUEST=GetTile&LAYER=DigitalGlobe:ImageryTileService&FORMAT=image/jpeg&TileRow={y}&TileCol={x}&TileMatrixSet=EPSG:3857&TileMatrix=EPSG:3857:{z}',
        'type': 'xyz',
        'connectId': ''
    },
    'Maxar Vivid': {
        'url': 'https://securewatch.digitalglobe.com/earthservice/wmtsaccess?SERVICE=WMTS&VERSION=1.0.0&STYLE=&REQUEST=GetTile&LAYER=DigitalGlobe:ImageryTileService&FORMAT=image/jpeg&TileRow={y}&TileCol={x}&TileMatrixSet=EPSG:3857&TileMatrix=EPSG:3857:{z}',
        'type': 'xyz',
        'connectId': ''
    },
    'Maxar Basemaps': {
        'url': 'https://securewatch.digitalglobe.com/earthservice/wmtsaccess?SERVICE=WMTS&VERSION=1.0.0&STYLE=&REQUEST=GetTile&LAYER=DigitalGlobe:ImageryTileService&FORMAT=image/jpeg&TileRow={y}&TileCol={x}&TileMatrixSet=EPSG:3857&TileMatrix=EPSG:3857:{z}',
        'type': 'xyz',
        'connectId': ''
    }
}
# MISC
SENTINEL_METADATA_ATTRIBUTES = 'Cloud Cover %', f'Date & Time ({TIMEZONE})', 'Image ID'
SENTINEL_OPTION_NAME = 'Sentinel-2'
MAX_TIF_SIZE = 2000  # MB
MAX_ZOOM = 21
DEFAULT_ZOOM = MAXAR_MAX_FREE_ZOOM
BUILTIN_PROVIDERS = {
    **MAXAR_PRODUCTS,
    SENTINEL_OPTION_NAME: {
        'url': 'http://',
        'type': 'sentinel_l2a',
        'token': ''
    }
}
STYLES = {
    'Buildings Detection': 'buildings',
    'Buildings Detection With Heights': 'buildings',
    'Forest Detection': 'forest',
    'Forest Detection With Heights': 'forest_with_heights',
    'Roads Detection': 'roads'
}
