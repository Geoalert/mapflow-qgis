import time
from dataclasses import dataclass
from qgis.core import QgsSettings

@dataclass
class Config:
    TIMEZONE = time.localtime().tm_zone
    PLUGIN_NAME = 'Mapflow'
    DEFAULT_MODEL = '🏠 Buildings'
    MAPFLOW_ENV = QgsSettings().value('variables/mapflow_env', "") or 'production'
    PROJECT_ID = QgsSettings().value("variables/mapflow_project_id", "") or "default"
    SERVER = "https://whitemaps-{env}.mapflow.ai/rest".format(env=MAPFLOW_ENV)
    BILLING_HISTORY_URL = "https://app.mapflow.ai/account/billing-history"
    TOP_UP_URL = "https://app.mapflow.ai/account/balance"
    MODEL_DOCS_URL = "https://docs.mapflow.ai/userguides/pipelines.html"

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
    METADATA_TABLE_ATTRIBUTES = {
        'Product Type': 'productType',
        'Sensor': 'source',
        'Band Order': 'colorBandOrder',
        'Cloud %': 'cloudCover',
        f'\N{DEGREE SIGN} Off Nadir': 'offNadirAngle',
        f'Date & Time ({TIMEZONE})': 'acquisitionDate',
        'Image ID': 'id'
    }
    MAXAR_ID_COLUMN_INDEX = tuple(METADATA_TABLE_ATTRIBUTES.values()).index('id')
    MAXAR_DATETIME_COLUMN_INDEX = tuple(METADATA_TABLE_ATTRIBUTES.keys()).index(f'Date & Time ({TIMEZONE})')
    MAXAR_CLOUD_COLUMN_INDEX = tuple(METADATA_TABLE_ATTRIBUTES.keys()).index(f'Cloud %')
    MAXAR_MAX_FREE_ZOOM = 12

    # MISC
    ENABLE_SENTINEL = (QgsSettings().value('variables/mapflow_enable_sentinel', "false").lower() == "true")
    SHOW_RAW_ERROR = (QgsSettings().value("variables/mapflow_raw_error", "false").lower() == "true")
    USE_OAUTH = (QgsSettings().value("variables/mapflow_use_oauth", "false").lower() == "true")
    SKYWATCH_METADATA_MAX_AREA = 1e11  # 100,000 sq.km
    SKYWATCH_METADATA_MAX_SIDE_LENGTH = 1e6  # 1,000 km
    INVALID_TOKEN_WARNING_OBJECT_NAME = 'invalidToken'
    METADATA_MORE_BUTTON_OBJECT_NAME = 'getMoreMetadata'
    SENTINEL_WD_NAME_PATTERN = 'Sentinel-2'
    SENTINEL_ATTRIBUTES = f'Date & Time ({TIMEZONE})', 'Cloud %', 'Image ID', 'Preview'
    SENTINEL_ID_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index('Image ID')
    SENTINEL_PREVIEW_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index('Preview')
    SENTINEL_DATETIME_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index(f'Date & Time ({TIMEZONE})')
    SENTINEL_CLOUD_COLUMN_INDEX = SENTINEL_ATTRIBUTES.index('Cloud %')
    SKYWATCH_POLL_INTERVAL = 2
    MAX_ZOOM = 21
    DEFAULT_ZOOM = MAXAR_MAX_FREE_ZOOM
    USER_STATUS_UPDATE_INTERVAL = 30  # seconds

    MAX_FILE_SIZE_PIXELS = 30_000
    MAX_FILE_SIZE_BYTES = 2*(1024**3)

    MAX_AOIS_PER_PROCESSING = int(QgsSettings().value("variables/mapflow_max_aois", "10"))

    # OAuth2
    OAUTH2_URL = "https://auth-duty.mapflow.ai/auth/realms/mapflow-duty/protocol/openid-connect"
    AUTH_CONFIG_NAME = f"mapflow_{MAPFLOW_ENV}"
    AUTH_CONFIG_MAP = '{"accessMethod":0,"apiKey":"","clientId":"qgis","clientSecret":"","configType":1,"customHeader":"","description":"","grantFlow":1,"id":"","name":"","objectName":"","password":"","persistToken":false,"queryPairs":{},"redirectPort":7070,"redirectUrl":"qgis","refreshTokenUrl":"https://auth-duty.mapflow.ai/auth/realms/mapflow-duty/protocol/openid-connect/token","requestTimeout":30,"requestUrl":"https://auth-duty.mapflow.ai/auth/realms/mapflow-duty/protocol/openid-connect/auth","scope":"","tokenUrl":"https://auth-duty.mapflow.ai/auth/realms/mapflow-duty/protocol/openid-connect/token","username":"","version":1}'


config = Config()
