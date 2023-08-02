from dataclasses import dataclass, fields


@dataclass
class SkipDataClass:
    """
    Dataclass that skips all the unknown input arguments. Designed to withstand non-breaking API changes,
     so all the schemas for response parsing should inherit it

    This is abstract class and will do nothing, as it has no fields
    """
    @classmethod
    def from_dict(cls, params_dict: dict):
        clsf = [f.name for f in fields(cls)]
        return cls(**{k: v for k, v in params_dict.items() if k in clsf})
