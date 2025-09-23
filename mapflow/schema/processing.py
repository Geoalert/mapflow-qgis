from dataclasses import dataclass, fields
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
        if not params_dict:
            return None
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
