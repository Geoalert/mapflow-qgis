from .error_message_list import ErrorMessageList


class ApiErrors(ErrorMessageList):
    def __init__(self):
        super().__init__()
        self.error_descriptions = {
            "MAXAR_PROVIDERS_UNAVAILABLE": self.tr("Upgrade your subscription to get access to Maxar imagery"),
            "ProviderMinAreaError": self.tr("Geometry area is {aoiArea} sq km, which "
                                            "is smaller than the minimum required area for {providerName} data provider "
                                            "({providerMinArea} sq km)"),
            # Synthesized client-side before sending the request (see Mapflow.create_search_template)
            "TEMPLATE_AREA_LIMIT_EXCEEDED": self.tr("Up to {templateAreaLimit} sq km can be used for a planned "
                                                    "processing. Try reducing your area of interest."),
        }
        self.message_descriptions = {
            # Backend rejects template creation with a generic "BAD_REQUEST" code and this exact message.
            "You don't have enough limit, please contact admin!":
                self.tr("You don't have enough limit to create this planned processing. "
                        "Please contact your administrator to increase the limit."),
        }