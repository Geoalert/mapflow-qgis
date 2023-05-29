class PluginError(ValueError):
    """Base class for exceptions in this module."""
    pass


class BadProcessingInput(PluginError):
    """Raised when there is an error in UI input for processing."""
    pass


class ProcessingInputDataMissing(PluginError):
    """Raised when some of necessary data fields for processing are not filled."""
    pass