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
    'Cloud %': 'cloudCover',
    f'\N{DEGREE SIGN} Off Nadir': 'offNadirAngle',
    f'Date & Time ({TIMEZONE})': 'acquisitionDate',
    'Image ID': 'featureId'
}
MAXAR_ID_COLUMN_INDEX = tuple(MAXAR_METADATA_ATTRIBUTES.values()).index('featureId')
MAXAR_DATETIME_COLUMN_INDEX = tuple(MAXAR_METADATA_ATTRIBUTES.keys()).index(f'Date & Time ({TIMEZONE})')
MAXAR_CLOUD_COLUMN_INDEX = tuple(MAXAR_METADATA_ATTRIBUTES.keys()).index(f'Cloud %')
MAXAR_MAX_FREE_ZOOM = 12
MAXAR_WMTS_URL = 'https://securewatch.digitalglobe.com/earthservice/wmtsaccess?SERVICE=WMTS&VERSION=1.0.0&STYLE=&REQUEST=GetTile&LAYER=DigitalGlobe:ImageryTileService&FORMAT=image/jpeg&TileRow={y}&TileCol={x}&TileMatrixSet=EPSG:3857&TileMatrix=EPSG:3857:{z}'
MAXAR_PRODUCTS = {
    f'Maxar {name}': {'url': MAXAR_WMTS_URL, 'type': 'xyz', 'connectId': ''} 
    for name in ('SecureWarch', 'Vivid', 'Basemaps')
}
# MISC
METADATA_MAX_AREA = 1e11  # 10000 sq. km
METADATA_MAX_SIDE_LENGTH = 1e5  # 100 km
INVALID_TOKEN_WARNING_OBJECT_NAME = 'invalidToken'
METADATA_MORE_BUTTON_OBJECT_NAME = 'getMoreMetadata'
SENTINEL_OPTION_NAME = 'Sentinel-2'
SENTINEL_ATTRIBUTES = f'Date & Time ({TIMEZONE})', 'Cloud %', 'Image ID', 'Preview'
SENTINEL_ID_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index('Image ID')
SENTINEL_PREVIEW_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index('Preview')
SENTINEL_DATETIME_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index(f'Date & Time ({TIMEZONE})')
SENTINEL_CLOUD_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index('Cloud %')
SKYWATCH_POLL_INTERVAL = 2
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
