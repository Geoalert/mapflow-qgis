from uuid import UUID
from enum import Enum
from datetime import datetime
from typing import Sequence, Union, Optional, List, Dict
from dataclasses import dataclass

from .base import Serializable,  SkipDataClass

class PreviewSize(str, Enum):
    large = 'l'
    small = 's'

@dataclass
class RasterLayer(SkipDataClass):
    tileUrl: str
    tileJsonUrl: str

@dataclass
class UserLimitSchema(SkipDataClass):
    memoryLimit: Optional[int] = None
    memoryUsed: Optional[int] = None
    memoryFree: Optional[int] = None
    maxUploadFileSize: Optional[int] = None
    maxPixelCount: Optional[int] = None


# ========== MOSAIC ============== #

@dataclass
class MosaicCreateSchema(Serializable):
    name: str
    tags: Sequence[str] = ()

@dataclass
class MosaicUpdateSchema(MosaicCreateSchema):
    pass

@dataclass
class MosaicCreateReturnSchema(SkipDataClass):
    id: UUID
    name: str
    created_at: datetime
    tags: Union[Sequence[str], None] = ()

    def __post_init__(self):
        self.created_at = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))

@dataclass
class MosaicReturnSchema(SkipDataClass):
    id: UUID
    rasterLayer: RasterLayer
    name: str
    created_at: datetime
    footprint: str
    sizeInBytes: int
    tags: Union[Sequence[str], None] = ()

    def __post_init__(self):
        self.created_at = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        self.rasterLayer = RasterLayer.from_dict(self.rasterLayer)


# ============ IMAGE  =============== #

@dataclass
class ImageMetadataSchema(SkipDataClass):
    crs: str
    count: int
    width: int
    height: int
    dtypes: List[str]
    nodata: float
    pixel_size: List[float]

@dataclass
class ImageReturnSchema(SkipDataClass):
    id: UUID
    mosaic_id: UUID
    image_url: str
    preview_url_l: str
    preview_url_s: str
    uploaded_at: datetime
    file_size: int # Bytes
    footprint: dict
    filename: str
    checksum: str
    meta_data: ImageMetadataSchema
    cog_link: Optional[str]

    def __post_init__(self):
        self.uploaded_at = datetime.fromisoformat(self.uploaded_at.replace("Z", "+00:00"))
        self.meta_data = ImageMetadataSchema.from_dict(self.meta_data)
