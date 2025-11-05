from .error_message_list import ErrorMessageList


class ApiErrors(ErrorMessageList):
    def __init__(self):
        super().__init__()
        self.error_descriptions = {
            "MAXAR_PROVIDERS_UNAVAILABLE": self.tr("Upgrade your subscription to get access to Maxar imagery"),
            "ProviderMinAreaError": self.tr("Geometry area is {aoiArea} sq km, which "
                                            "is smaller than the minimum required area for {providerName} data provider "
                                            "({providerMinArea} sq km)")
        }