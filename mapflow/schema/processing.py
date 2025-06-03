from dataclasses import dataclass
from typing import Optional, Mapping, Any, Union, Iterable, List

from .base import SkipDataClass, Serializable
from ..entity.provider.provider import SourceType

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
class ProcessingParamsSchema(SkipDataClass):
    data_provider: Optional[str] = None
    url: Optional[str] = None
    projection: Optional[str] = None
    source_type: Optional[str] = None


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
class MyImageryParams(Serializable, SkipDataClass):
    imageIds: List[str]
    mosaicId: str


@dataclass
class ImagerySearchParams(Serializable, SkipDataClass):
    dataProvider: str
    imageIds: List[str]
    zoom: int


@dataclass
class DataProviderParams(Serializable, SkipDataClass):
    providerName: str
    zoom: str


@dataclass
class UserDefinedParams(Serializable, SkipDataClass):
    sourceType: SourceType
    url: str
    zoom: Optional[int]
    crs: str
    rasterLogin: Optional[str]
    rasterPassword: Optional[str]


@dataclass
class SourceParams(Serializable, SkipDataClass):
    dataProvider: Optional[DataProviderParams]
    myImagery: Optional[MyImageryParams]
    imagerySearch: Optional[ImagerySearchParams]
    userDefined: Optional[UserDefinedParams]


@dataclass
class PostProcessingParams(Serializable, SkipDataClass):
    sourceParams: SourceParams


@dataclass
class PostProcessingSchemaV2(Serializable):
    name: str
    description: Optional[str]
    projectId: str
    wdId: Optional[str]
    geometry: Mapping[str, Any]
    params: PostProcessingParams
    meta: Optional[Mapping[str, Any]]
    blocks: Optional[Iterable[BlockOption]]
