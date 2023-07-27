from dataclasses import dataclass
from typing import Optional, List, Mapping


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
    blocks: Optional[List[BlockConfig]] = None

    def __post_init__(self):
        if self.blocks:
            self.blocks = [BlockConfig(**item) for item in self.blocks]
            # Store obligatory price in pricePerSqKm
            self.pricePerSqKm = sum(block.price for block in self.non_optional_blocks)
        else:
            self.blocks = []

    @property
    def optional_blocks(self):
        return [block for block in self.blocks if block.optional]

    @property
    def non_optional_blocks(self):
        return [block for block in self.blocks if not block.optional]

    def get_price(self, enable_blocks: Optional[List[bool]]):
        price = self.pricePerSqKm
        if len(enable_blocks) != len(self.optional_blocks):
            raise ValueError(f"enable_blocks param {enable_blocks }must correspond WD`s optional blocks {self.optional_blocks}!")
        for block, enabled in zip(self.optional_blocks, enable_blocks):
            if enabled:
                price += block.price
        return price

    def get_enabled_blocks(self, enable_blocks: List[bool]):
        """
        Form a dict to send it to API instead of list of toggles that we get from UIs
        """
        if len(enable_blocks) != len(self.optional_blocks):
            raise ValueError(f"enable_blocks param {enable_blocks }must correspond WD`s optional blocks {self.optional_blocks}!")
        return [{"name": block.name, "enabled": enabled} for block, enabled in zip(self.optional_blocks, enable_blocks)]