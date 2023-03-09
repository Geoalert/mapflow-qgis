import time


TIMEZONE = time.localtime().tm_zone
PLUGIN_NAME = 'Mapflow'
MAPFLOW_DEFAULT_TIMEOUT = 5  # in seconds
DEFAULT_MODEL = '🏠 Buildings'
SERVER = "https://whitemaps-{env}.mapflow.ai/rest"

# PROCESSINGS
PROCESSING_TABLE_REFRESH_INTERVAL = 6  # in seconds
PROCESSING_ATTRIBUTES = 'name', 'workflowDef', 'status', 'percentCompleted', 'aoiArea', 'created', 'id'
PROCESSING_TABLE_ID_COLUMN_INDEX = PROCESSING_ATTRIBUTES.index('id')
PROCESSING_TABLE_SORT_COLUMN_INDEX = PROCESSING_ATTRIBUTES.index('created')
# MAXAR
MAXAR_METADATA_ATTRIBUTES = {
    'Product Type': 'productType',
    'Sensor': 'source',
    'Band Order': 'colorBandOrder',
    'Cloud %': 'cloudCover',
    f'\N{DEGREE SIGN} Off Nadir': 'offNadirAngle',
    f'Date & Time ({TIMEZONE})': 'acquisitionDate',
    'Image ID': 'id'
}
MAXAR_ID_COLUMN_INDEX = tuple(MAXAR_METADATA_ATTRIBUTES.values()).index('id')
MAXAR_DATETIME_COLUMN_INDEX = tuple(MAXAR_METADATA_ATTRIBUTES.keys()).index(f'Date & Time ({TIMEZONE})')
MAXAR_CLOUD_COLUMN_INDEX = tuple(MAXAR_METADATA_ATTRIBUTES.keys()).index(f'Cloud %')
MAXAR_MAX_FREE_ZOOM = 12
MAXAR_BASE_URL = 'https://securewatch.digitalglobe.com/earthservice/wmtsaccess?'

# MISC
SKYWATCH_METADATA_MAX_AREA = 1e11  # 100,000 sq.km
SKYWATCH_METADATA_MAX_SIDE_LENGTH = 1e6  # 1,000 km
INVALID_TOKEN_WARNING_OBJECT_NAME = 'invalidToken'
METADATA_MORE_BUTTON_OBJECT_NAME = 'getMoreMetadata'
SENTINEL_OPTION_NAME = 'Sentinel-2'
SENTINEL_WD_NAMES = ['🚜 Fields (Sentinel-2)']
SENTINEL_ATTRIBUTES = f'Date & Time ({TIMEZONE})', 'Cloud %', 'Image ID', 'Preview'
SENTINEL_ID_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index('Image ID')
SENTINEL_PREVIEW_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index('Preview')
SENTINEL_DATETIME_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index(f'Date & Time ({TIMEZONE})')
SENTINEL_CLOUD_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index('Cloud %')
SKYWATCH_POLL_INTERVAL = 2
MAX_ZOOM = 21
DEFAULT_ZOOM = MAXAR_MAX_FREE_ZOOM

PROVIDERS_KEY = 'mapflow_data_providers'
LEGACY_PROVIDERS_KEY = 'providers'
LEGACY_PROVIDER_LOGIN_KEY = 'providerUsername'
LEGACY_PROVIDER_PASSWORD_KEY = 'providerPassword'

STYLES = {
    'Buildings Detection': 'buildings',
    'Buildings Detection With Heights': 'buildings',
    'Forest Detection': 'forest',
    'Forest Detection With Heights': 'forest_with_heights',
    'Roads Detection': 'roads'
}

MAX_FILE_SIZE_PIXELS = 30_000
MAX_FILE_SIZE_BYTES = 1024**3
