PLUGIN_NAME = 'Mapflow'
MAPFLOW_DEFAULT_TIMEOUT = 5  # in seconds
# PROCESSINGS
PROCESSING_TABLE_REFRESH_INTERVAL = 6  # in seconds
PROCESSING_ATTRIBUTES = 'name', 'workflowDef', 'status', 'percentCompleted', 'aoiArea', 'created', 'id'
PROCESSING_TABLE_ID_COLUMN_INDEX = PROCESSING_ATTRIBUTES.index('id')
PROCESSING_TABLE_SORT_COLUMN_INDEX = PROCESSING_ATTRIBUTES.index('created')
# MAXAR
MAXAR_METADATA_ATTRIBUTES = 'productType', 'colorBandOrder', 'cloudCover', 'offNadirAngle', 'acquisitionDate', 'featureId'
MAXAR_METADATA_ID_COLUMN_INDEX = MAXAR_METADATA_ATTRIBUTES.index('featureId')
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
MAX_TIF_SIZE = 2000  # MB
MAX_ZOOM = 21
DEFAULT_ZOOM = MAXAR_MAX_FREE_ZOOM
STYLES = {
    'Buildings Detection': 'buildings',
    'Buildings Detection With Heights': 'buildings',
    'Forest Detection': 'forest',
    'Forest Detection With Heights': 'forest_with_heights',
    'Roads Detection': 'roads'
}
