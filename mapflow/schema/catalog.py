from dataclasses import dataclass
from typing import Optional, Mapping, Any, Union, List
from datetime import datetime
from .base import Serializable, SkipDataClass


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
    footprint: dict
    pixelResolution: float
    acquisitionDate: Union[datetime, str]
    productType: str
    sensor: str
    colorBandOrder: str
    cloudCover: float
    offNadirAngle: float

    def __post_init__(self):
        if isinstance(self.acquisitionDate, str):
            self.acquisitionDate = datetime.fromisoformat(self.acquisitionDate.replace("Z", "+00:00"))
        elif not isinstance(self.acquisitionDate, datetime):
            raise TypeError("Acquisition date must be either datetime or ISO-formatted str")
        # To percent
        self.cloudCover = self.cloudCover*100

    def as_geojson(self):
        properties = {k: v for k, v in self.as_dict().items() if k != "footprint"}
        return {"type": "Feature",
                "geometry": self.footprint,
                "properties": properties}

@dataclass
class ImageCatalogResponseSchema(Serializable, SkipDataClass):
    images: List[ImageSchema]

    def __post_init__(self):
        self.images = [ImageSchema.from_dict(image) for image in self.images]

    def as_geojson(self):
        return {"type": "FeatureCollection", "features": [image.as_geojson() for image in self.images]}