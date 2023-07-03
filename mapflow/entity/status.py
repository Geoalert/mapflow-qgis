from enum import Enum
from PyQt5.QtCore import QObject


class ProcessingStatusDict(QObject):
    def __init__(self):
        super().__init__()
        self.value_map = {None: None,
                          'OK': self.tr("Ok"),
                          'IN_PROGRESS': self.tr("In progress"),
                          'FAILED': self.tr("Failed")}


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


class ProcessingReviewStatus(NamedEnum):
    none = None
    in_review = 'IN_REVIEW'
    not_accepted = 'NOT_ACCEPTED'
    refunded = 'REFUNDED'
    accepted = 'ACCEPTED'

    def __init__(self, value):
        super().__init__(value)
        self.value_map = ProcessingReviewStatusDict().value_map

    @property
    def is_in_review(self):
        return self == ProcessingReviewStatus.in_review

    @property
    def is_not_accepted(self):
        return self == ProcessingReviewStatus.not_accepted

    @property
    def is_none(self):
        return self == ProcessingReviewStatus.none