from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Mapping, Any, Union, List

from .base import Serializable, SkipDataClass

from ..config import Config

class PreviewType(str, Enum):
    png = "png"
    jpg = "jpg"
    xyz = "xyz"
    tms = "tms"
    wms = "wms"

class ProductType(str, Enum):
    mosaic = "Mosaic"
    image = "Image"

@dataclass
class MultiPreview(Serializable, SkipDataClass):
    url: str
    geometry: dict

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
    limit: Optional[int] = Config.SEARCH_RESULTS_PAGE_LIMIT
    offset: Optional[int] = 0
    hideUnavailable: Optional[bool] = False
    productTypes: Optional[List[ProductType]] = None
    dataProviders: Optional[List[str]] = None

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
    satId: Optional[str] = None
    previewType: Optional[PreviewType] = None
    previewUrl: Optional[str] = None
    previews: Optional[List[MultiPreview]] = None
    providerName: Optional[str] = None
    zoom: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.acquisitionDate, str):
            self.acquisitionDate = datetime.fromisoformat(self.acquisitionDate.replace("Z", "+00:00"))
        elif not isinstance(self.acquisitionDate, datetime):
            raise TypeError("Acquisition date must be either datetime or ISO-formatted str")
        self.cloudCover = self.cloudCover
        try:
            self.previewType = PreviewType(self.previewType)
        except:
            self.previewType = None
        self.previews = [MultiPreview.from_dict(preview) for preview in self.previews]

    def as_geojson(self):
        properties = {k: v for k, v in self.as_dict().items() if k != "footprint"}
        res = {"type": "Feature",
                "geometry": self.footprint,
                "properties": properties}
        return res

@dataclass
class ImageCatalogResponseSchema(Serializable):
    images: List[ImageSchema]
    total: int = Config.SEARCH_RESULTS_PAGE_LIMIT
    limit: int = Config.SEARCH_RESULTS_PAGE_LIMIT
    offset: int = 0

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