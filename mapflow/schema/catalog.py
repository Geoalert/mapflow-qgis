from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Mapping, Any, Union, List

from .base import Serializable, SkipDataClass


class PreviewType(str, Enum):
    png = "png"
    xyz = "xyz"
    tms = "tms"
    wms = "wms"


@dataclass
class ImageCatalogRequestSchema(Serializable):
    aoi: Mapping[str, Any]
    acquisitionDateFrom: Union[datetime, str, None] = None
    acquisitionDateTo: Union[datetime, str, None] = None
    minResolution: Optional[float] = None
    maxResolution: Optional[float] = None
    maxCloudCover: Optional[float] = None
    minOffNadirAngle: Optional[float] = None
    maxOffNadirAngle: Optional[float] = None
    minAoiIntersectionPercent: Optional[float] = None

@dataclass
class ImageSchema(Serializable, SkipDataClass):
    id: str
    footprint: Optional[dict]
    pixelResolution: Optional[float]
    acquisitionDate: Union[datetime, str]
    productType: Optional[str]
    sensor: Optional[str]
    colorBandOrder: Optional[str]
    cloudCover: Optional[float]
    offNadirAngle: Optional[float]
    source: Optional[str] = None  # Duplicate of sensor for the table (like in Maxar)
    previewType: Optional[PreviewType] = None
    previewUrl: Optional[str] = None
    providerName: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.acquisitionDate, str):
            self.acquisitionDate = datetime.fromisoformat(self.acquisitionDate.replace("Z", "+00:00"))
        elif not isinstance(self.acquisitionDate, datetime):
            raise TypeError("Acquisition date must be either datetime or ISO-formatted str")
        # To percent
        self.cloudCover = self.cloudCover*100
        self.source = self.sensor
        self.previewType = PreviewType(self.previewType)

    def as_geojson(self):
        properties = {k: v for k, v in self.as_dict().items() if k != "footprint"}
        return {"type": "Feature",
                "geometry": self.footprint,
                "properties": properties}

@dataclass
class ImageCatalogResponseSchema(Serializable):
    images: List[ImageSchema]

    def __post_init__(self):
        self.images = [ImageSchema.from_dict(image) for image in self.images]

    def as_geojson(self):
        return {"type": "FeatureCollection", "features": [image.as_geojson() for image in self.images]}

@dataclass
class Aoi:
    id: str
    status: str
    percentCompleted: int
    area: int
    messages: list
    geometry: dict

    def aoi_as_feature(self):
        feature = {"type": "Feature",
                   "geometry" : self.geometry,
                   "properties" : { "id": self.id, 
                                    "status": self.status,
                                    "percentCompleted": self.percentCompleted,
                                    "area": self.area,
                                    "messages": self.messages }
                  }
        return feature

@dataclass
class AoiResponseSchema:
    aois: List[Aoi]

    def __post_init__(self):
        self.aois = [Aoi(**data) for data in self.aois]

    def aoi_as_geojson(self):
        geojson = { "type": "FeatureCollection",
                    "features": [aoi.aoi_as_feature() for aoi in self.aois]}
        return geojson