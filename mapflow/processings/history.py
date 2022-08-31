from typing import List, Dict, Optional, Tuple
from .saved_processing import Processing


class ProcessingHistory:
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
        elif processing['percentCompleted'] == 100:
            finished_ids.append(processing.id_)
            if processing.id_ not in history.finished:
                finished.append(processing)

    return failed, finished, ProcessingHistory(failed_ids, finished_ids)