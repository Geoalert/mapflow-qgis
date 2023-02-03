from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import sys
from ..errors import ErrorMessage


class Processing:
    def __init__(self, id_, name, status,
                 workflow_def, aoi_area, created,
                 percent_completed, raster_layer, errors=None,  **kwargs):
        self.id_ = id_
        self.name = name
        self.status = status
        self.workflow_def = workflow_def
        self.aoi_area = aoi_area
        self.created = created.astimezone()
        self.percent_completed = int(percent_completed)
        self.errors = errors
        self.raster_layer = raster_layer

    @classmethod
    def from_response(cls, processing):
        id_ = processing['id']
        name = processing['name']
        status = processing['status']
        workflow_def = processing['workflowDef']['name']
        aoi_area = round(processing['aoiArea'] / 10 ** 6, 2)

        if sys.version_info.minor < 7:  # python 3.6 doesn't understand 'Z' as UTC
            created = processing['created'].replace('Z', '+0000')
        else:
            created = processing['created']
        created = datetime.strptime(
            created, '%Y-%m-%dT%H:%M:%S.%f%z'
        ).astimezone()
        percent_completed = processing['percentCompleted']
        messages = processing.get('messages', [])
        errors = [ErrorMessage.from_response(message) for message in messages]
        raster_layer = processing['rasterLayer']
        return cls(id_, name, status, workflow_def, aoi_area, created, percent_completed, raster_layer, errors)

    @property
    def is_new(self):
        now = datetime.now().astimezone()
        one_day = timedelta(1)
        return now - self.created < one_day

    def error_message(self, error_message_list):
        if not self.errors:
            return ""
        return "\n".join([error.to_str(error_message_list) for error in self.errors])

    def asdict(self):
        return {
            'id': self.id_,
            'name': self.name,
            'status': self.status,
            'workflowDef': self.workflow_def,
            'aoiArea': self.aoi_area,
            'percentCompleted': self.percent_completed,
            'errors': self.errors,
            # Serialize datetime and drop seconds for brevity
            'created': self.created.strftime('%Y-%m-%d %H:%M'),
            'rasterLayer': self.raster_layer
        }


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
        if processing.status == 'FAILED':
            failed_ids.append(processing.id_)
            if processing.id_ not in history.failed:
                failed.append(processing)
    # Find recently finished processings and alert the user
        elif processing.percent_completed == 100:
            finished_ids.append(processing.id_)
            if processing.id_ not in history.finished:
                finished.append(processing)

    return failed, finished, ProcessingHistory(failed_ids, finished_ids)
