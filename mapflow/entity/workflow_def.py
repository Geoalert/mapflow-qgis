from dataclasses import dataclass
from typing import Optional, Iterable


@dataclass
class BlockConfig:
    name: str
    displayName: str
    price: int
    optional: bool
    # defaultEnable: bool


@dataclass
class WorkflowDef:
    id: str
    name: str
    description: str = ""
    pricePerSqKm: float = 1.0
    created: str = ""
    updated: str = ""
    blocks: Optional[Iterable[BlockConfig]] = None

    def __post_init__(self):
        if self.blocks:
            self.blocks = [BlockConfig(**item) for item in self.blocks]
        else:
            self.blocks = []