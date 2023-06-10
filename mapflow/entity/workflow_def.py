from dataclasses import dataclass


@dataclass
class WorkflowDef:
    id: str
    name: str
    description: str = ""
    pricePerSqKm: float = 1.0
    created: str = ""
    updated: str = ""
