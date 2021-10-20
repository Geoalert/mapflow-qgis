PLUGIN_NAME = 'Mapflow'
MAPFLOW_DEFAULT_TIMEOUT = 5  # in seconds
# PROCESSINGS
PROCESSING_TABLE_REFRESH_INTERVAL = 6  # in seconds
PROCESSING_TABLE_ID_COLUMN_INDEX = 5
# MAXAR
MAXAR_METADATA_ATTRIBUTES = 'productType', 'colorBandOrder', 'cloudCover', 'offNadirAngle', 'acquisitionDate', 'featureId'
MAXAR_METADATA_ID_COLUMN_INDEX = MAXAR_METADATA_ATTRIBUTES.index('featureId')
# MISC
MAXAR_PRODUCTS = {
    'Maxar SecureWatch': {
        'url': 'https://securewatch.digitalglobe.com/earthservice/wmtsaccess?SERVICE=WMTS&VERSION=1.0.0&STYLE=&REQUEST=GetTile&LAYER=DigitalGlobe:ImageryTileService&FORMAT=image/jpeg&TileRow={y}&TileCol={x}&TileMatrixSet=EPSG:3857&TileMatrix=EPSG:3857:{z}',
        'type': 'xyz',
        'connectId': '55f8367d-52dd-4905-82a5-b9f21aff9462'
    },
    'Maxar Vivid': {
        'url': 'https://securewatch.digitalglobe.com/earthservice/wmtsaccess?SERVICE=WMTS&VERSION=1.0.0&STYLE=&REQUEST=GetTile&LAYER=DigitalGlobe:ImageryTileService&FORMAT=image/jpeg&TileRow={y}&TileCol={x}&TileMatrixSet=EPSG:3857&TileMatrix=EPSG:3857:{z}',
        'type': 'xyz',
        'connectId': 'cae3cbda-715b-4614-a4fa-a9f58a7bb87a'
    },
    'Maxar Basemaps': {
        'url': 'https://securewatch.digitalglobe.com/earthservice/wmtsaccess?SERVICE=WMTS&VERSION=1.0.0&STYLE=&REQUEST=GetTile&LAYER=DigitalGlobe:ImageryTileService&FORMAT=image/jpeg&TileRow={y}&TileCol={x}&TileMatrixSet=EPSG:3857&TileMatrix=EPSG:3857:{z}',
        'type': 'xyz',
        'connectId': '18b01fb7-dcf1-410f-b550-619b9a4ff4e8'
    }
}
STYLES = {
    'Buildings Detection': 'buildings',
    'Buildings Detection With Heights': 'buildings',
    'Forest Detection': 'forest',
    'Forest Detection With Heights': 'forest_with_heights',
    'Roads Detection': 'roads'
}
