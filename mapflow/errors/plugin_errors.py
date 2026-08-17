class PluginError(ValueError):
    """Base class for exceptions in this module."""
    pass


class BadProcessingInput(PluginError):
    """Raised when there is an error in UI input for processing."""
    pass


class ProcessingInputDataMissing(PluginError):
    """Raised when some of necessary data fields for processing are not filled."""
    pass


class ProcessingLimitExceeded(PluginError):
    """Raised when the user has exceeded the processing limit."""
    pass


class ImageIdRequired(PluginError):
    pass


class AoiNotIntersectsImage(PluginError):
    pass


class AoiMergeDeclined(Exception):
    """Raised when the user refuses to merge intersecting AOIs (which would drop their names).

    Deliberately NOT a ``PluginError``: the user has already answered the question, so the
    callers must abort silently instead of showing an error on top of the prompt.
    """
    pass


class ProxyIsAlreadySet(RuntimeError):
    pass
