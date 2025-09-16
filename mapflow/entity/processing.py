import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

from .status import ProcessingStatus, ProcessingReviewStatus
from ..errors import ErrorMessage
from ..schema.processing import BlockOption, ProcessingParams


class Processing:
    def __init__(self,
                 id_,
                 name,
                 status,
                 workflow_def,
                 aoi_area,
                 cost,
                 created,
                 percent_completed,
                 raster_layer,
                 vector_layer,
                 errors=None,
                 review_status=None,
                 in_review_until=None,
                 params: Optional[ProcessingParams] = None,
                 blocks: Optional[List[BlockOption]] = None,
                 description: Optional[str] = None,
                 meta: Optional[Dict] = None,
                 **kwargs):
        self.id_ = id_
        self.name = name
        self.status = ProcessingStatus(status)
        self.workflow_def = workflow_def
        self.aoi_area = aoi_area
        self.cost = int(cost)
        self.created = created.astimezone()
        self.percent_completed = int(percent_completed)
        self.errors = errors
        self.raster_layer = raster_layer
        self.vector_layer = vector_layer
        self.review_status = ProcessingReviewStatus(review_status)
        self.in_review_until = in_review_until
        self.params = params
        self.blocks = blocks
        self.description = description
        self.meta = meta

    @classmethod
    def from_response(cls, processing):
        id_ = processing['id']
        name = processing['name']
        status = processing['status']
        description = processing.get("description") or None
        workflow_def = processing['workflowDef']['name']
        aoi_area = round(processing['aoiArea'] / 10 ** 6, 2)
        meta = processing.get("meta") or None

        if sys.version_info.minor < 7:  # python 3.6 doesn't understand 'Z' as UTC
            created = processing['created'].replace('Z', '+0000')
        else:
            created = processing['created']
        created = datetime.strptime(created, '%Y-%m-%dT%H:%M:%S.%f%z').astimezone()
        percent_completed = processing['percentCompleted']
        messages = processing.get('messages', [])
        errors = [ErrorMessage.from_response(message) for message in messages]
        raster_layer = processing['rasterLayer']
        vector_layer = processing['vectorLayer']
        if processing.get('reviewStatus'):
            review_status = processing.get('reviewStatus', {}).get('reviewStatus')
            in_review_until_str = processing.get('reviewStatus', {}).get('inReviewUntil')
            if in_review_until_str:
                in_review_until = datetime.strptime(in_review_until_str, '%Y-%m-%dT%H:%M:%S.%f%z').astimezone()
            else:
                in_review_until = None
        else:
            review_status = in_review_until = None
        cost = processing.get('cost', 0)
        params = ProcessingParams.from_dict(processing.get("params"))
        blocks = [BlockOption.from_dict(block) for block in processing.get("blocks", [])]
        return cls(id_,
                   name,
                   status,
                   workflow_def,
                   aoi_area,
                   cost,
                   created,
                   percent_completed,
                   raster_layer,
                   vector_layer,
                   errors,
                   review_status,
                   in_review_until,
                   params,
                   blocks,
                   description,
                   meta)

    @property
    def is_new(self):
        now = datetime.now().astimezone()
        one_day = timedelta(1)
        return now - self.created < one_day

    @property
    def review_expires(self):
        if not isinstance(self.in_review_until, datetime)\
                or not self.review_status.is_in_review:
            return False
        now = datetime.now().astimezone()
        one_day = timedelta(1)
        return self.in_review_until - now < one_day

    def error_message(self, raw=False):
        if not self.errors:
            return ""
        return "\n".join([error.to_str(raw=raw) for error in self.errors])

    def asdict(self):
        return {
            'id': self.id_,
            'name': self.name,
            'status': self.status_with_review,
            'workflowDef': self.workflow_def,
            'aoiArea': self.aoi_area,
            'cost': self.cost,
            'percentCompleted': self.percent_completed,
            'errors': self.errors,
            # Serialize datetime and drop seconds for brevity
            'created': self.created.strftime('%Y-%m-%d %H:%M'),
            'rasterLayer': self.raster_layer,
            'reviewUntil':  self.in_review_until.strftime('%Y-%m-%d %H:%M') if self.in_review_until else "",
            'description': self.description,
            'meta': self.meta
        }

    @property
    def status_with_review(self):
        """
        Review status is set instead of status if applicable, that is
        when the status is OK and review_status is set (not None)
        """
        if self.status.is_ok and not self.review_status.is_none:
            return self.review_status.display_value
        else:
            return self.status.display_value


def parse_processings_request_dict(response: list) -> Dict[str, Processing]:
    res = {}
    for processing in response:
        new_processing = Processing.from_response(processing)
        res[new_processing.id_] = new_processing
    return res


def parse_processings_request(response: list) -> List[Processing]:
    return [Processing.from_response(resp) for resp in response]


class ProcessingHistory:
    """
    History of the processings, including failed and finished processings, that are stored in settings
    """
    def __init__(self,
                 failed: Optional[List[str]] = None,
                 finished: Optional[List[str]] = None):
        self.failed = failed or []
        self.finished = finished or []

    def asdict(self):
        return {
            'failed': [id_ for id_ in self.failed],
            'finished': [id_ for id_ in self.finished]
        }

    def update(self,
               failed: Optional[List[Processing]] = None,
               finished: Optional[List[Processing]] = None):
        self.failed = [processing.id_ for processing in failed]
        self.failed = [processing.id_ for processing in finished]

    @classmethod
    def from_settings(cls, settings: Dict[str, List[str]]):
        return cls(failed=settings.get('failed', []), finished=settings.get('finished', []))


def updated_processings(processings: List[Processing],
                        history: ProcessingHistory) -> Tuple[List[Processing], List[Processing], ProcessingHistory]:
    failed = []
    finished = []
    failed_ids = []
    finished_ids = []
    for processing in processings:
        if processing.status.is_failed:
            failed_ids.append(processing.id_)
            if processing.id_ not in history.failed:
                failed.append(processing)
    # Find recently finished processings and alert the user
        elif processing.percent_completed == 100:
            finished_ids.append(processing.id_)
            if processing.id_ not in history.finished:
                finished.append(processing)

    return failed, finished, ProcessingHistory(failed_ids, finished_ids)
