import dataclasses
import json
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from typing import Optional


@dataclass
class SkipDataClass:
    """
    Dataclass that skips all the unknown input arguments. Designed to withstand non-breaking API changes,
     so all the schemas for response parsing should inherit it

    This is abstract class and will do nothing, as it has no fields
    """

    @classmethod
    def from_dict(cls, params_dict: Optional[dict]):
        if not params_dict:
            return None
        clsf = [f.name for f in fields(cls)]
        return cls(**{k: v for k, v in params_dict.items() if k in clsf})


@dataclass
class Serializable:
    @staticmethod
    def decorate_value(value):
        """
        Common serialization dacorations
        """
        if isinstance(value, datetime):
            return value.isoformat()
        else:
            return value

    def as_dict(self, skip_none=True):
        if skip_none:
            return dataclasses.asdict(self,
                                      dict_factory=lambda x: {k: self.decorate_value(v) for (k, v) in x if v is not None})
        else:
            return dataclasses.asdict(self,
                                      dict_factory=lambda x: {k: self.decorate_value(v) for (k, v) in x})

    def as_json(self, skip_none=True):
        return json.dumps(self.as_dict(skip_none=skip_none))


def parse_api_datetime_utc(value: Optional[object]) -> Optional[datetime]:
    """Parse API datetime preserving UTC semantics for internal state."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    raise TypeError(f"Unsupported datetime value type: {type(value)}")
