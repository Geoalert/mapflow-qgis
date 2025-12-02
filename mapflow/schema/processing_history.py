import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Set
from uuid import UUID

from .status import ProcessingStatus
from .processing import ProcessingDTO


@dataclass
class ProcessingHistory:
    """
    History of the processings for a specific project, including failed and finished processings,
    that are stored in settings

    As project IDs are unique UUIDs, we can skip all other sections and just save/load by this key
    """
    project_id: Optional[UUID] = None
    processing_statuses: Dict[UUID, ProcessingStatus] = field(default_factory=dict)

    def to_settings(self, settings):
        settings.setValue(f"processing_history_{self.project_id}", json.dumps({
            str(id_): status.value
            for id_, status in self.processing_statuses.items()
            if status.is_terminal
        }))

    @classmethod
    def from_settings(cls, settings, project_id: UUID):
        data = settings.value(f"processing_history_{project_id}")
        if not data:
            return cls(project_id=project_id, processing_statuses={})
        parsed = json.loads(data)
        return cls(
            project_id=project_id,
            processing_statuses={id_: ProcessingStatus(status) for id_, status in parsed.items()}
        )

    def is_finished(self, processing_id: UUID) -> bool:
        return self.processing_statuses.get(processing_id) == ProcessingStatus.ok

    def is_failed(self, processing_id: UUID) -> bool:
        return self.processing_statuses.get(processing_id) == ProcessingStatus.failed

    def add(self, processing_id: UUID, status: ProcessingStatus):
        self.processing_statuses[processing_id] = status

    def update(self, processings: Dict[UUID, ProcessingDTO], settings) -> Dict[str, List[UUID]]:
        """
        Update processing statuses from current processings.

        - Updates current statuses in memory
        - Detects changes to terminal statuses (OK, FAILED, etc.)
        - Persists to settings if terminal status changes occurred
        - Returns report of newly terminal processings for notifications

        Args:
            processings: Dict mapping processing ID to ProcessingDTO
            settings: QgsSettings instance for persistence

        Returns:
            Dict with status names as keys and lists of processing IDs that
            newly entered that terminal status. Example:
            {"OK": [uuid1, uuid2], "FAILED": [uuid3]}
        """
        terminal_changes = defaultdict(list)
        for processing_id, processing in processings.items():
            # in case it's UUID
            processing_id = str(processing_id)
            old_status = self.processing_statuses.get(processing_id)
            new_status = processing.status

            # Skip if status unchanged
            if old_status == new_status:
                continue

            # Update in-memory status
            self.processing_statuses[processing_id] = new_status

            # Check if this is a NEW terminal status (wasn't terminal before)
            if new_status.is_terminal:
                # Only report if it wasn't already in a terminal state
                status_name = new_status.value
                terminal_changes[status_name].append(processing_id)

        # Persist to settings only if terminal statuses changed
        if terminal_changes:
            print(f"Saving to settings: {len(self.processing_statuses)}")
            self.to_settings(settings)

        return terminal_changes

    def cleanup_missing(self, current_ids: Set[UUID]) -> None:
        """Remove entries for processings that no longer exist in the project"""
        self.processing_statuses = {
            pid: status
            for pid, status in self.processing_statuses.items()
            if pid in current_ids
        }
