import time
from dataclasses import dataclass
from qgis.core import QgsSettings

@dataclass
class Config:
    TIMEZONE = time.localtime().tm_zone
    PLUGIN_NAME = 'Mapflow'
    DEFAULT_MODEL = '🏠 Buildings'
    MAPFLOW_ENV = QgsSettings().value('variables/mapflow_env', "") or'production'
    PROJECT_ID = QgsSettings().value("variables/mapflow_project_id", "") or "default"
    SERVER = "https://whitemaps-{env}.mapflow.ai/rest".format(env=MAPFLOW_ENV)
    BILLING_HISTORY_URL = "https://app.mapflow.ai/account/billing-history"
    TOP_UP_URL = "https://app.mapflow.ai/account/balance"
    MODEL_DOCS_URL = "https://docs.mapflow.ai/userguides/models_changelog/index.html"

    # PROCESSINGS
    PROCESSING_TABLE_REFRESH_INTERVAL = 6  # in seconds
    PROCESSING_TABLE_COLUMNS = ('name',
                                'workflowDef',
                                'status',
                                'percentCompleted',
                                'aoiArea',
                                'cost',
                                'created',
                                'reviewUntil',
                                'id')

    """
    todo: add tabs in code, not in designer ?
                                {'name' : self.tr("Name"),
                                'workflowDef': self.tr("Model"),
                                'status': self.tr("Status"),
                                'percentCompleted': self.tr("Progress %"),
                                'aoiArea': self.tr("Area, sq.km"),
                                'cost': self.tr("Cost"),
                                'created': self.tr("Created"),
                                'reviewUntil': self.tr("review until"),
                                'id': self.tr("ID")}
    """
    PROCESSING_TABLE_ID_COLUMN_INDEX = PROCESSING_TABLE_COLUMNS.index('id')
    PROCESSING_TABLE_SORT_COLUMN_INDEX = PROCESSING_TABLE_COLUMNS.index('created')
    DEFAULT_HIDDEN_COLUMNS = (PROCESSING_TABLE_COLUMNS.index(item) for item in ('id', 'reviewUntil', 'cost'))
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

    # MISC
    ENABLE_SENTINEL = (QgsSettings().value('variables/mapflow_enable_sentinel', "false").lower() == "true")
    SKYWATCH_METADATA_MAX_AREA = 1e11  # 100,000 sq.km
    SKYWATCH_METADATA_MAX_SIDE_LENGTH = 1e6  # 1,000 km
    INVALID_TOKEN_WARNING_OBJECT_NAME = 'invalidToken'
    METADATA_MORE_BUTTON_OBJECT_NAME = 'getMoreMetadata'
    SENTINEL_WD_NAMES = ['🚜 Fields (Sentinel-2)']
    SENTINEL_ATTRIBUTES = f'Date & Time ({TIMEZONE})', 'Cloud %', 'Image ID', 'Preview'
    SENTINEL_ID_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index('Image ID')
    SENTINEL_PREVIEW_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index('Preview')
    SENTINEL_DATETIME_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index(f'Date & Time ({TIMEZONE})')
    SENTINEL_CLOUD_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index('Cloud %')
    SKYWATCH_POLL_INTERVAL = 2
    MAX_ZOOM = 21
    DEFAULT_ZOOM = MAXAR_MAX_FREE_ZOOM
    USER_STATUS_UPDATE_INTERVAL = 30  # seconds

    STYLES = {
        '🏠 Buildings': 'buildings',
        'Buildings Detection With Heights': 'buildings',
        '🌲 Forest': 'forest',
        '🌲↕️ Forest with heights': 'forest_with_heights',
        '🚗 Roads': 'roads',
        '🏗️ Construction sites': 'construction'
    }

    MAX_FILE_SIZE_PIXELS = 30_000
    MAX_FILE_SIZE_BYTES = 1024**3

    MAX_AOIS_PER_PROCESSING = int(QgsSettings().value("variables/mapflow_max_aois", "10"))


config = Config()
