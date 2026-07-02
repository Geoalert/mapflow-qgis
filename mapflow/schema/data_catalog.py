from uuid import UUID
from enum import Enum
from datetime import datetime
from typing import Sequence, Union, Optional, List
from dataclasses import dataclass

from .base import Serializable, SkipDataClass, parse_api_datetime_utc
from .layer import RasterLayer


class PreviewSize(str, Enum):
    large = 'l'
    small = 's'


class PreprocessingStatus(str, Enum):
    """Preprocessing state of an uploaded image (see 002_C_myimagery_api.md).

    ``ready`` = image is usable (NONE = no preprocessing needed, or COMPLETED);
    ``pending``/``in_progress`` = still being preprocessed;
    ``failed`` = preprocessing failed (``preprocessing_error`` is set).
    """
    none = 'NONE'
    pending = 'PENDING'
    in_progress = 'IN_PROGRESS'
    completed = 'COMPLETED'
    failed = 'FAILED'

    @classmethod
    def _missing_(cls, value):
        # Be tolerant to unknown/none statuses coming from the API — treat as ready.
        return cls.none

    @property
    def is_ready(self) -> bool:
        return self in (PreprocessingStatus.none, PreprocessingStatus.completed)

    @property
    def is_pending(self) -> bool:
        return self in (PreprocessingStatus.pending, PreprocessingStatus.in_progress)

    @property
    def is_failed(self) -> bool:
        return self is PreprocessingStatus.failed


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
        self.created_at = parse_api_datetime_utc(self.created_at)

@dataclass
class MosaicStatusSummary(SkipDataClass):
    """Aggregate preprocessing counts attached to a mosaic (see 002_C_myimagery_api.md).

    ``ready = NONE + COMPLETED``, ``pending = PENDING``, ``in_progress = IN_PROGRESS``,
    ``failed = FAILED``; ``total = ready + pending + in_progress + failed``.
    """
    total: int = 0
    ready: int = 0
    pending: int = 0
    in_progress: int = 0
    failed: int = 0

    @property
    def preprocessing(self) -> int:
        """Images still being preprocessed (pending + in progress)."""
        return self.pending + self.in_progress

    @property
    def has_activity(self) -> bool:
        """True while any image is still being preprocessed."""
        return self.preprocessing > 0


@dataclass
class MosaicReturnSchema(SkipDataClass):
    id: UUID
    rasterLayer: RasterLayer
    name: str
    created_at: datetime
    footprint: str
    sizeInBytes: int
    tags: Union[Sequence[str], None] = ()
    status_summary: Optional[MosaicStatusSummary] = None

    def __post_init__(self):
        self.created_at = parse_api_datetime_utc(self.created_at)
        self.rasterLayer = RasterLayer.from_dict(self.rasterLayer)
        self.status_summary = MosaicStatusSummary.from_dict(self.status_summary)


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
    available_for_download: bool = True

    def __post_init__(self):
        self.uploaded_at = parse_api_datetime_utc(self.uploaded_at)
        self.meta_data = ImageMetadataSchema.from_dict(self.meta_data)


@dataclass
class ImageStatusSchema(SkipDataClass):
    """Per-image preprocessing status from ``GET /rasters/mosaic/{id}/status``.

    Carries only lightweight fields (no metadata/preview/size) — full metadata for
    ready images comes from ``GET /rasters/mosaic/{id}/image``. Non-ready images
    (pending/in_progress/failed) are only visible through this endpoint.
    """
    image_id: UUID
    filename: str
    uploaded_at: datetime
    preprocessing_status: PreprocessingStatus = PreprocessingStatus.none
    preprocessing_error: Optional[str] = None
    data_available: bool = False
    tiles_ready: bool = False

    def __post_init__(self):
        self.uploaded_at = parse_api_datetime_utc(self.uploaded_at)
        self.preprocessing_status = PreprocessingStatus(self.preprocessing_status)

    @property
    def id(self) -> UUID:
        """Alias so status rows and full-image rows share a ``.id`` for selection/delete."""
        return self.image_id

    @property
    def is_ready(self) -> bool:
        return self.preprocessing_status.is_ready

    @property
    def is_failed(self) -> bool:
        return self.preprocessing_status.is_failed


@dataclass
class MosaicStatusResponse(SkipDataClass):
    """Aggregate + per-image status for a mosaic (``GET /rasters/mosaic/{id}/status``)."""
    mosaic_id: UUID
    total_images: int = 0
    ready_images: int = 0
    pending_images: int = 0
    in_progress_images: int = 0
    failed_images: int = 0
    tiles_ready_images: int = 0
    images: List[ImageStatusSchema] = ()

    def __post_init__(self):
        self.images = [ImageStatusSchema.from_dict(i) for i in (self.images or [])]

    def non_ready_images(self) -> List[ImageStatusSchema]:
        """Images that would otherwise be invisible in the plain image list."""
        return [i for i in self.images if not i.is_ready]
