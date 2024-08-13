from .error_message_list import ErrorMessageList


class ApiErrors(ErrorMessageList):
    def __init__(self):
        super().__init__()
        self.error_descriptions = {
            "MAXAR_PROVIDERS_UNAVAILABLE": self.tr("Upgrade your subscription to get access to Maxar imagery"),
            "NOT_FOUND": None
        }