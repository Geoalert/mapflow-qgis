from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from PyQt5.QtCore import QObject

from .base import Serializable, SkipDataClass


class ProcessingStatusDict(QObject):
    def __init__(self):
        super().__init__()
        self.value_map = {None: None,
                          'OK': self.tr("Ok"),
                          'IN_PROGRESS': self.tr("In progress"),
                          'FAILED': self.tr("Failed"),
                          'REFUNDED': self.tr("Refunded"),
                          'CANCELLED': self.tr("Cancelled"),
                          'AWAITING': self.tr("Awaiting")}


class ProcessingReviewStatusDict(QObject):
    def __init__(self):
        super().__init__()
        self.value_map = {None: None,
                          'IN_REVIEW': self.tr("Review required"),
                          'NOT_ACCEPTED': self.tr("In review"),
                          'REFUNDED': self.tr("Refunded"),
                          'ACCEPTED': self.tr("Ok")}


class NamedEnum(Enum):
    def __init__(self, value):
        super().__init__()
        self.value_map = {}

    @property
    def display_value(self):
        return self.value_map.get(self.value, self.value)


class ProcessingStatus(NamedEnum):
    none = None
    ok = 'OK'
    in_progress = 'IN_PROGRESS'
    failed = 'FAILED'
    refunded = 'REFUNDED'
    cancelled = 'CANCELLED'
    awaiting = 'AWAITING'

    def __init__(self, value):
        super().__init__(value)
        self.value_map = ProcessingStatusDict().value_map

    @property
    def is_ok(self):
        return self == ProcessingStatus.ok

    @property
    def is_in_progress(self):
        return self == ProcessingStatus.in_progress

    @property
    def is_failed(self):
        return self == ProcessingStatus.failed

    @property
    def is_refunded(self):
        return self == ProcessingStatus.refunded

    @property
    def is_cancelled(self):
        return self == ProcessingStatus.cancelled
    
    @property
    def is_awaiting(self):
        return self == ProcessingStatus.awaiting

    @property
    def is_terminal(self):
        return self.is_ok or self.is_failed or self.is_refunded or self.is_cancelled


class ProcessingReviewStatusEnum(NamedEnum):
    none = None
    in_review = 'IN_REVIEW'
    not_accepted = 'NOT_ACCEPTED'
    refunded = 'REFUNDED'
    accepted = 'ACCEPTED'

    def __init__(self, value):
        super().__init__(value)
        self.value_map = ProcessingReviewStatusDict().value_map


@dataclass
class ProcessingReviewStatus(Serializable, SkipDataClass):
    reviewStatus: Optional[ProcessingReviewStatusEnum] = None
    inReviewUntil: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]):
        """Handle None input by returning instance with defaults."""
        if data is None:
            return cls()
        return super().from_dict(data)

    def __post_init__(self):
        if self.inReviewUntil:
            self.inReviewUntil = datetime.strptime(self.inReviewUntil, '%Y-%m-%dT%H:%M:%S.%f%z').astimezone()
        self.reviewStatus = ProcessingReviewStatusEnum(self.reviewStatus)

    @property
    def is_in_review(self):
        return self.reviewStatus == ProcessingReviewStatusEnum.in_review

    @property
    def is_not_accepted(self):
        return self.reviewStatus == ProcessingReviewStatusEnum.not_accepted

    @property
    def is_none(self):
        return self.reviewStatus == ProcessingReviewStatusEnum.none

    @property
    def is_accepted(self):
        return self.reviewStatus == ProcessingReviewStatusEnum.accepted
