from dataclasses import dataclass

from .base import SkipDataClass


@dataclass
class RasterLayer(SkipDataClass):
    tileUrl: str
    tileJsonUrl: str

@dataclass
class VectorLayer(SkipDataClass):
    tileUrl: str
    tileJsonUrl: str

