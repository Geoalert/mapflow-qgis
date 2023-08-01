import json
import dataclasses
from dataclasses import dataclass
from typing import Optional, Mapping, Any, Union, Iterable


class Serializable:
    def as_dict(self, skip_none=True):
        if skip_none:
            return dataclasses.asdict(self, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})
        else:
            return dataclasses.asdict(self)

    def as_json(self, skip_none=True):
        return json.dumps(self.as_dict(skip_none=skip_none))


@dataclass
class PostSourceSchema(Serializable):
    url: str
    source_type: str
    projection: Optional[str] = None
    raster_login: Optional[str] = None
    raster_password: Optional[str] = None


@dataclass
class BlockOption(Serializable):
    name: str
    enabled: bool


@dataclass
class PostProviderSchema(Serializable):
    # Data provider name
    data_provider: str
    year: Optional[str] = None


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

