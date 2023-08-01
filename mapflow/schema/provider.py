from dataclasses import dataclass
from typing import List, Dict


@dataclass
class ProviderReturnSchema:
    id: str
    name: str
    displayName: str
    price: List[Dict]
