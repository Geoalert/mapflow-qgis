from typing import Dict, Optional

from PyQt5.QtCore import QObject

from .api_errors import ApiErrors
from .data_errors import DataErrors
from .error_message_list import ErrorMessageList
from .processing_errors import ProcessingErrors

"""
["messages":[{"code":"source-validator.PixelSizeTooHigh","parameters":{"max_res":"1.2","level":"error","actual_res":"5.620983603290215"}}]}]
"""


error_message_list = ErrorMessageList()
error_message_list.update(ProcessingErrors())
error_message_list.update(DataErrors())
error_message_list.update(ApiErrors())


class ErrorMessage(QObject):
    def __init__(self,
                 code: str,
                 parameters: Optional[Dict[str, str]] = None,
                 message: Optional[str] = None):
        super().__init__()
        self.code = code
        self.parameters = parameters or {}
        self.message = message

    @classmethod
    def from_response(cls, response: Dict):
        return cls(response["code"], response["parameters"])

    @property
    def formatted_message(self):
        """
        returns formatted translated error message; if the translation is missing from the plugin code, returns None
        """
        message = error_message_list.get(self.code)
        if not message:
            # no message description
            return None
        try:
            message = message.format(**self.parameters)
        except Exception as e:
            # problem during formatting. Probably wrong parameters
            message = None
        return message

    @property
    def raw_message(self):
        return f"Raw error: code = {self.code}, parameters={self.parameters}, message={self.message}"

    def to_str(self, raw=False):
        default = "Unknown error. Contact us to resolve the issue! help@geoalert.io"
        formated_message=self.formatted_message
        if formated_message:
            return formated_message
        elif raw:
            return self.raw_message
        else:
            print(self.message, self.parameters, self.code)
            return self.message or default
