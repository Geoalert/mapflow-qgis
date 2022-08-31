from datetime import datetime, timedelta
from typing import List, Dict
import sys
from ..errors import ErrorMessage


class Processing:
    def __init__(self, id_, name, status, workflow_def, aoi_area, created, errors=None, **kwargs):
        self.id_ = id_
        self.name = name
        self.status = status
        self.workflow_def = workflow_def
        self.aoi_area = aoi_area
        self.created = created.astimezone()
        self.errors = errors

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
            created = processing.created
        created = datetime.strptime(
            created, '%Y-%m-%dT%H:%M:%S.%f%z'
        ).astimezone()

        messages = processing.get('messages', [])
        errors = [ErrorMessage.from_response(message) for message in messages]
        return cls(id_, name, status, workflow_def, aoi_area, created, errors)

    @property
    def is_new(self):
        now = datetime.now().astimezone()
        one_day = timedelta(1)
        return now - self.created < one_day

    @property
    def error_message(self):
        if not self.errors:
            # todo: write sample error message
            return "Empty message"
        return "\n".join([str(error) for error in self.errors])

    def asdict(self):
        return {
            'id': self.id_,
            'name': self.name,
            'status': self.status,
            'workflowDef': self.workflow_def,
            'aoiArea': self.aoi_area,
            'errors': self.errors,
            # Serialize datetime and drop seconds for brevity
            'created': self.created.strftime('%Y-%m-%d %H:%M')
        }


def parse_processings_request_dict(response: list) -> Dict[str, Processing]:
    res = {}
    for processing in response:
        new_processing = Processing.from_response(processing)
        res[new_processing.id_] = new_processing
    return res


def parse_processings_request(response: list) -> List[Processing]:
    return [Processing.from_response(resp) for resp in response]