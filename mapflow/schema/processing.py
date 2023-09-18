from dataclasses import dataclass
from typing import Optional, Mapping, Any, Union, Iterable
from .base import SkipDataClass, Serializable


@dataclass
class PostSourceSchema(Serializable, SkipDataClass):
    url: str
    source_type: str
    projection: Optional[str] = None
    raster_login: Optional[str] = None
    raster_password: Optional[str] = None


@dataclass
class BlockOption(Serializable, SkipDataClass):
    name: str
    enabled: bool


@dataclass
class PostProviderSchema(Serializable, SkipDataClass):
    # Data provider name
    data_provider: str
    url: Optional[str] = None


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

