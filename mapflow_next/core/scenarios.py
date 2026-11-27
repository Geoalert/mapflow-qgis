"""Scenario catalogue: ready-made setups (model + options + zoom) built on Mapflow models. Pure Python.

Model names come from the server per project, so a scenario finds its model by keywords
(`all` must appear, `not` must not). WARNING: a stable scenario → workflow-def id mapping on the
backend would make this exact; keyword matching is the bridge until then.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import DEFAULT_ZOOM, ZOOM_MAX, ZOOM_MIN, Model


def normalize(text: str) -> str:
    """Lowercase letters and digits only: '🏠 Buildings' and 'buildings' compare equal."""
    return re.sub(r"[^0-9a-z]+", " ", (text or "").lower()).strip()


@dataclass
class Scenario:
    id: str
    title: str
    categories: List[str]
    model_label: str
    short: str
    long: str = ""
    output: str = ""
    best: str = ""
    uses: List[str] = field(default_factory=list)
    tip: str = ""
    price_short: str = ""
    best_short: str = ""
    cost_main: str = ""
    cost_note: str = ""
    option: str = ""
    image: Optional[str] = None
    icon: Optional[str] = None
    custom: bool = False
    apply: Dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict) -> "Scenario":
        return cls(id=data["id"], title=data["title"], categories=list(data.get("categories") or []),
                   model_label=data.get("modelLabel") or data.get("model") or "", short=data.get("short", ""),
                   long=data.get("long", ""), output=data.get("output", ""), best=data.get("best", ""),
                   uses=list(data.get("uses") or []), tip=data.get("tip", ""),
                   price_short=data.get("priceShort", ""), best_short=data.get("bestShort", ""),
                   cost_main=data.get("costMain", ""), cost_note=data.get("costNote", ""),
                   option=data.get("option", ""), image=data.get("image"), icon=data.get("icon"),
                   custom=bool(data.get("custom")), apply=dict(data.get("apply") or {}))

    @property
    def zoom(self) -> Optional[int]:
        value = self.apply.get("zoom")
        return int(value) if value is not None else None

    @property
    def imagery_hint(self) -> Optional[str]:
        """'my_imagery' or 'search' for scenarios that are about the imagery, not a model preset."""
        return self.apply.get("imagery")

    def matches(self, query: str) -> bool:
        needle = normalize(query)
        return not needle or needle in normalize(f"{self.title} {self.short} {self.model_label}")


@dataclass
class Resolution:
    """What a scenario means in the current project."""
    model: Optional[Model]
    options: List[str]
    zoom: Optional[int]
    missing_options: List[str]


class Catalogue:
    def __init__(self, categories: List[dict], scenarios: List[Scenario], image_dir: Path):
        self.categories = categories
        self.scenarios = scenarios
        self.image_dir = image_dir
        self._by_id = {s.id: s for s in scenarios}

    @classmethod
    def load(cls, folder: Path) -> "Catalogue":
        data = json.loads((folder / "scenarios.json").read_text(encoding="utf-8"))
        return cls(data["categories"], [Scenario.from_json(s) for s in data["scenarios"]], folder)

    def get(self, scenario_id: Optional[str]) -> Optional[Scenario]:
        return self._by_id.get(scenario_id or "")

    def in_category(self, category: str) -> List[Scenario]:
        if category == "all":
            return list(self.scenarios)
        return [s for s in self.scenarios if category in s.categories]

    def search(self, query: str) -> List[Scenario]:
        return [s for s in self.scenarios if s.matches(query)]

    def popular(self, limit: int = 4) -> List[Scenario]:
        return [s for s in self.in_category("popular") if not s.custom][:limit]

    def image_path(self, scenario: Scenario) -> Optional[Path]:
        return self.image_dir / scenario.image if scenario.image else None


def match_model(models: List[Model], rule: Dict) -> Optional[Model]:
    """The model with every `all` keyword and no `not` keyword; the shortest name wins, so
    '🏠 Buildings' beats '🏠 Buildings (Aerial imagery)'."""
    need = [normalize(k) for k in rule.get("all", [])]
    avoid = [normalize(k) for k in rule.get("not", [])]
    fits = [m for m in models
            if all(k in normalize(m.name) for k in need) and not any(k in normalize(m.name) for k in avoid)]
    return min(fits, key=lambda m: len(normalize(m.name))) if fits else None


def resolve(scenario: Scenario, models: List[Model]) -> Resolution:
    rule = scenario.apply.get("model")
    model = match_model(models, rule) if rule else None
    wanted = [normalize(k) for k in scenario.apply.get("options", [])]
    chosen, matched = [], set()
    if model:
        for block in model.options:
            label = normalize(f"{block.display_name} {block.name}")
            hits = [k for k in wanted if k in label]
            if hits:
                chosen.append(block.name)
                matched.update(hits)
    missing = [k for k in scenario.apply.get("options", []) if normalize(k) not in matched]
    return Resolution(model=model, options=chosen, zoom=scenario.zoom, missing_options=missing if model else [])


def scenario_for_model(catalogue: Catalogue, model: Model, options: List[str]) -> Optional[Scenario]:
    """The scenario that best describes a model + options (used when duplicating a processing)."""
    best: Tuple[int, Optional[Scenario]] = (-1, None)
    for scenario in catalogue.scenarios:
        rule = scenario.apply.get("model")
        if not rule or match_model([model], rule) is None:
            continue
        res = resolve(scenario, [model])
        score = 10 - abs(len(set(res.options) ^ set(options)))
        if score > best[0]:
            best = (score, scenario)
    return best[1]


def recommended_zoom(scenario: Optional[Scenario]) -> int:
    """The zoom a scenario is tuned for, within the z17–z21 the plugin offers (z18 without a scenario)."""
    zoom = scenario.zoom if scenario else None
    return min(max(zoom or DEFAULT_ZOOM, ZOOM_MIN), ZOOM_MAX)
