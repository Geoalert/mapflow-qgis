from qgis.core import QgsVectorLayer
from dataclasses import dataclass, fields
from datetime import datetime, timedelta
from typing import Optional, Mapping, Any, Union, Iterable, List
from uuid import UUID
from .base import SkipDataClass, Serializable
from ..entity.provider.provider import SourceType
from ..entity.status import ProcessingStatus, ProcessingReviewStatus
from ..errors import ErrorMessage
from ..schema.layer import RasterLayer, VectorLayer
from .workflow_def import WorkflowDef

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
    datapPovider: DataProviderSchema


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


@dataclass
class ImagerySearchParams(Serializable):
    imagerySearch: ImagerySearchSchema


@dataclass
class UserDefinedSchema(Serializable):
    sourceType: SourceType
    url: str
    zoom: Optional[int]
    crs: str
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
    def from_dict(cls, params_dict: dict):
        clsf = [f.name for f in fields(cls)]
        processing_params = cls(**{k: v for k, v in params_dict.items() if k in clsf})
        source_params = processing_params.sourceParams
        if source_params.get("dataProvider"):
            source_params = DataProviderParams(DataProviderSchema(**source_params.get("dataProvider")))
        elif source_params.get("myImagery"):
            source_params = MyImageryParams(MyImagerySchema(**source_params.get("myImagery")))
        elif source_params.get("imagerySearch"):
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
    area: Optional[QgsVectorLayer]
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

    percent_completed: int
    review_status: ProcessingReviewStatus
    in_review_until: datetime
    params: ProcessingParams
    blocks: List[BlockOption]

    def __post_init__(self):
        self.review_status = ProcessingReviewStatus(self.review_status)
        self.status = ProcessingStatus(self.status)
        self.created = datetime.strptime(self.created, '%Y-%m-%dT%H:%M:%S.%f%z').astimezone()
        self.params = ProcessingParams.from_dict(self.params)
        self.blocks = [BlockOption.from_dict(block) for block in self.blocks]
        self.workflowDef = WorkflowDef.from_dict(self.workflowDef)
        self.messages = [ErrorMessage.from_response(message) for message in self.messages]

    @property
    def review_expires(self):
        if not isinstance(self.in_review_until, datetime)\
                or not self.review_status.is_in_review:
            return False
        now = datetime.now().astimezone()
        one_day = timedelta(1)
        return self.in_review_until - now < one_day

    def error_message(self, raw=False):
        if not self.errors:
            return ""
        return "\n".join([error.to_str(raw=raw) for error in self.errors])
