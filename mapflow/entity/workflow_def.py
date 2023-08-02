from dataclasses import dataclass
from ..schema import SkipDataClass


@dataclass
class WorkflowDef(SkipDataClass):
    id: str
    name: str
    description: str = ""
    pricePerSqKm: float = 1.0
    created: str = ""
    updated: str = ""
