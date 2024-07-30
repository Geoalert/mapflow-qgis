from uuid import UUID
from enum import Enum
from datetime import datetime
from typing import Sequence, Union, Optional
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
    memoryLimit: int
    memoryUsed: int
    memoryFree: int


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
    tags: Union[Sequence[str], None] = ()

    def __post_init__(self):
        self.created_at = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        self.rasterLayer = RasterLayer.from_dict(self.rasterLayer)


# ============ IMAGE  =============== #
@dataclass
class ImageReturnSchema(SkipDataClass):
    id: UUID
    image_url: str
    preview_url_l: str
    preview_url_s: str
    uploaded_at: datetime
    file_size: int # Bytes
    footprint: dict
    filename: str
    checksum: str
    meta_data: dict
    cog_link: Optional[str]

    def __post_init__(self):
        self.uploaded_at = datetime.fromisoformat(self.uploaded_at.replace("Z", "+00:00"))