from dataclasses import dataclass
from typing import List, Dict


@dataclass
class ProviderReturnSchema:
    id: str
    name: str
    displayName: str
    price: List[Dict]

    def __post_init__(self):
        self.price_dict = {price["zoom"]: price["priceSqKm"] for price in self.price}
