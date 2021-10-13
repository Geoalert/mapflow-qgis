PLUGIN_NAME = 'Mapflow'
MAPFLOW_DEFAULT_TIMEOUT = 5  # in seconds
# PROCESSINGS
PROCESSING_TABLE_REFRESH_INTERVAL = 6  # in seconds
PROCESSING_TABLE_ID_COLUMN_INDEX = 5
# MAXAR
MAXAR_PRODUCTS = 'Maxar SecureWatch', 'Maxar Vivid', 'Maxar Basemaps'
MAXAR_METADATA_ATTRIBUTES = 'sourceUnit', 'productType', 'colorBandOrder', 'cloudCover', 'acquisitionDate', 'featureId'
MAXAR_METADATA_ID_COLUMN_INDEX = MAXAR_METADATA_ATTRIBUTES.index('featureId')
# MISC
STYLES = {
    'Buildings Detection': 'buildings',
    'Buildings Detection With Heights': 'buildings',
    'Forest Detection': 'forest',
    'Forest Detection With Heights': 'forest_with_heights',
    'Roads Detection': 'roads'
}
