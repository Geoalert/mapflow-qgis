import json
import dataclasses
from dataclasses import dataclass
from typing import Optional, Mapping, Any


class Serializable:
    def as_dict(self, skip_none=True):
        if skip_none:
            return dataclasses.asdict(self, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})
        else:
            return dataclasses.asdict(self)

    def as_json(self, skip_none=True):
        return json.dumps(self.as_dict(skip_none=skip_none))


@dataclass
class ProcessingParams(Serializable):
    url: str
    source_type: str
    crs: Optional[str] = None
    raster_login: Optional[str] = None
    raster_password: Optional[str] = None


@dataclass
class PostProcessingSchema(Serializable):
    name: str
    wdId: Optional[str]
    params: ProcessingParams
    geometry: Mapping[str, Any]
    meta: Optional[Mapping[str, Any]]
    projectId: Optional[str] = None
