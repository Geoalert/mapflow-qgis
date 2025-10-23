from .error_message_list import ErrorMessageList


class ApiErrors(ErrorMessageList):
    def __init__(self):
        super().__init__()
        self.error_descriptions = {
            "MAXAR_PROVIDERS_UNAVAILABLE": self.tr("Upgrade your subscription to get access to Maxar imagery"),
            "ProviderMinAreaError": self.tr("Geometry area ({aoi_area} sq km) "
                                            "is smaller than the minimum required area for data provider {provider_name} "
                                            "({provider_min_area} sq km)")
        }