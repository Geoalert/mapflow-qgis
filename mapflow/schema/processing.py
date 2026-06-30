from enum import Enum

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Mapping, Any, Union, Iterable, List
from uuid import UUID

from .base import SkipDataClass, Serializable, parse_api_datetime_utc
from .status import ProcessingStatus, ProcessingReviewStatus
from .layer import RasterLayer, VectorLayer
from .workflow_def import WorkflowDef
from ..entity.provider.provider import SourceType
from ..errors import ErrorMessage


def _parse_iso_datetime(dt_str: str) -> datetime:
    """Parse ISO 8601 datetime strings with or without microseconds."""
    return parse_api_datetime_utc(dt_str)


@dataclass
class PostSourceSchema(Serializable, SkipDataClass):
    url: str
    source_type: str
    projection: Optional[str] = None
    raster_login: Optional[str] = None
    raster_password: Optional[str] = None
    zoom: Optional[str] = None


@dataclass
class BlockOption(Serializable, SkipDataClass):
    name: str
    displayName: str
    enabled: bool


@dataclass
class PostProviderSchema(Serializable, SkipDataClass):
    # Data provider name
    data_provider: str
    url: Optional[str] = None
    zoom: Optional[str] = None


@dataclass
class PostProcessingSchema(Serializable):
    name: str
    wdId: Optional[str]
    params: Union[PostSourceSchema, PostProviderSchema]
    blocks: Optional[Iterable[BlockOption]]
    geometry: Mapping[str, Any]
    meta: Optional[Mapping[str, Any]]
    projectId: Optional[str] = None

    def __post_init__(self):
        if self.blocks:
            self.blocks = [BlockOption(**item) for item in self.blocks]
        else:
            self.blocks = []


@dataclass
class UpdateProcessingSchema(Serializable):
    name: str
    description: str


@dataclass
class DataProviderSchema(Serializable):
    providerName: str
    zoom: str


@dataclass
class DataProviderParams(Serializable):
    dataProvider: DataProviderSchema


@dataclass
class MyImagerySchema(Serializable):
    imageIds: List[str]
    mosaicId: str


@dataclass
class MyImageryParams(Serializable):
    myImagery: MyImagerySchema


@dataclass
class ImagerySearchSchema(Serializable):
    dataProvider: str
    imageIds: List[str]
    zoom: int
    searchId: Optional[str] = None


@dataclass
class ImagerySearchParams(Serializable):
    imagerySearch: ImagerySearchSchema


@dataclass
class UserDefinedSchema(Serializable):
    sourceType: SourceType
    url: str
    zoom: Optional[int]
    crs: Optional[str]
    rasterLogin: Optional[str]
    rasterPassword: Optional[str]


@dataclass
class UserDefinedParams(Serializable):
    userDefined: UserDefinedSchema


@dataclass
class ProcessingParams(Serializable, SkipDataClass):
    sourceParams: Union[DataProviderParams,
                        MyImageryParams,
                        ImagerySearchParams,
                        UserDefinedParams]

    @classmethod
    def from_dict(cls, params_dict: Optional[dict]):
        if not params_dict:
            return None
        # The template `/processings` endpoint returns legacy flat params
        # (e.g. {"url", "zoom", "data_provider"}) instead of the v2 {"sourceParams": {...}}
        # shape. Without sourceParams there is nothing to resolve — return None rather
        # than raise (a raise here would drop the whole processing from the list).
        source_params = params_dict.get("sourceParams")
        if not isinstance(source_params, dict):
            return None

        if source_params.get("dataProvider"):
            source_params = DataProviderParams(DataProviderSchema(**source_params.get("dataProvider")))
        elif source_params.get("myImagery"):
            source_params = MyImageryParams(MyImagerySchema(**source_params.get("myImagery")))
        elif source_params.get("imagerySearch"):
            #! print (str(source_params))
            source_params = ImagerySearchParams(ImagerySearchSchema(**source_params.get("imagerySearch")))
        elif source_params.get("userDefined"):
            source_params = UserDefinedParams(UserDefinedSchema(**source_params.get("userDefined")))
        else:
            source_params = "Unidentified"
        return ProcessingParams(sourceParams=source_params)


@dataclass
class PostProcessingSchemaV2(Serializable):
    name: str
    description: Optional[str]
    projectId: str
    wdId: Optional[str]
    geometry: Mapping[str, Any]
    params: ProcessingParams
    meta: Optional[Mapping[str, Any]]
    blocks: Optional[Iterable[BlockOption]]


@dataclass
class ProcessingUIParams(Serializable, SkipDataClass):
    name: Optional[str]
    data_source_index: int
    zoom: Optional[int]
    wd_name: str
    model_options: list[BlockOption]


@dataclass
class ProcessingDTO(Serializable, SkipDataClass):
    id: UUID
    name: str
    projectId: UUID
    status: ProcessingStatus
    description: Optional[str]
    workflowDef: WorkflowDef
    aoiArea: int
    cost: int
    created: datetime
    rasterLayer: RasterLayer
    vectorLayer: VectorLayer
    messages: list[ErrorMessage]
    params: ProcessingParams
    blocks: List[BlockOption]

    percentCompleted: Optional[int] = None
    reviewStatus: Optional[ProcessingReviewStatus] = None

    def __post_init__(self):
        self.status = ProcessingStatus(self.status)
        self.created = _parse_iso_datetime(self.created)
        self.params = ProcessingParams.from_dict(self.params)
        self.blocks = [BlockOption.from_dict(block) for block in self.blocks]
        self.workflowDef = WorkflowDef.from_dict(self.workflowDef)
        self.messages = [ErrorMessage.from_response(message) for message in self.messages]
        self.rasterLayer = RasterLayer.from_dict(self.rasterLayer)
        self.vectorLayer = VectorLayer.from_dict(self.vectorLayer)
        if self.reviewStatus is None:
            self.reviewStatus = ProcessingReviewStatus()
        else:
            self.reviewStatus = ProcessingReviewStatus.from_dict(self.reviewStatus)

    @property
    def review_expires(self):
        if not isinstance(self.reviewStatus.inReviewUntil, datetime)\
                or not self.reviewStatus.is_in_review:
            return False
        now = datetime.now(timezone.utc)
        one_day = timedelta(1)
        return self.reviewStatus.inReviewUntil - now < one_day

    @property
    def reviewUntil(self):
        """
        backwards compatibility
        """
        return self.reviewStatus.inReviewUntil

    @property
    def is_final_state(self):
        """
        means that the processing is reached final state and can't change it without user interaction
        """
        return  self.status.is_terminal and not self.reviewStatus.is_not_accepted

    def error_message(self, raw=False):
        if not self.messages:
            return ""
        return "\n".join([error.to_str(raw=raw) for error in self.messages])

    def as_processing_table_dict(self):
        return {
            "name": self.name,
            "workflowDef": self.workflowDef.name,
            "status": self.reviewStatus.reviewStatus.display_value
                      if (self.reviewStatus and not self.reviewStatus.is_none)
                      else self.status.display_value,
            "percentCompleted": self.percentCompleted,
            "aoiArea": self.aoiArea/1000000,
            "cost": self.cost,
            "created": self.created.astimezone().strftime('%Y-%m-%d %H:%M'),
            "reviewUntil": self.reviewUntil,
            "id": self.id
        }


class ProcessingSortBy(str, Enum):
    scenario = "SCENARIO"
    name = "NAME"
    project = "PROJECT"
    email = "EMAIL"
    created = "CREATED"
    status = "STATUS"
    progress = "PROGRESS"
    completed = "COMPLETED"
    cost = "COST"
    area = "AREA"
    provider = "PROVIDER"


class ProcessingSortOrder(str, Enum):
    ascending = "ASC"
    descending = "DESC"


@dataclass
class ProcessingsRequest(Serializable):
    limit: int = 30
    offset: int = 0
    terms: Optional[str] = None
    sortBy: Optional[str] = None
    sortOrder: Optional[str] = None


@dataclass
class ProcessingsResult(SkipDataClass):
    results: Optional[List] = None
    total: int = 0
    count: int = 0

    def __post_init__(self):
        if self.results:
            self.results = [ProcessingDTO.from_dict(p) for p in self.results]
        else:
            self.results = []
