PLUGIN_NAME = 'Mapflow'
PROCESSING_LIST_REFRESH_INTERVAL = 5  # in seconds
PROCESSING_TABLE_ID_COLUMN_INDEX = 5
MAXAR_PRODUCTS = ('Maxar SecureWatch', 'Maxar Vivid', 'Maxar Basemaps')
MAXAR_METADATA_ATTRIBUTES = ('featureId', 'sourceUnit', 'productType', 'colorBandOrder', 'cloudCover', 'formattedDate')
MAXAR_METADATA_URL = 'https://securewatch.digitalglobe.com/catalogservice/wfsaccess'
MAXAR_METADATA_REQUEST_PARAMS = {
    'REQUEST': 'GetFeature',
    'TYPENAME': 'DigitalGlobe:FinishedFeature',
    'SERVICE': 'WFS',
    'VERSION': '2.0.0',
    'SRSNAME': 'EPSG:4326',
    'FEATUREPROFILE': 'Default_Profile',
    'WIDTH': 3000,
    'HEIGHT': 3000
}
STYLES = {
    'Buildings Detection': 'buildings',
    'Buildings Detection With Heights': 'buildings',
    'Forest Detection': 'forest',
    'Forest Detection With Heights': 'forest_with_heights',
    'Roads Detection': 'roads'
}
