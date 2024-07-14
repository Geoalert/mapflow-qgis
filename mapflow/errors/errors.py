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

    def to_str(self, raw=False):
        default = "Unknown error. Contact us to resolve the issue! help@geoalert.io"
        message = error_message_list.get(self.code, default=default)
        if message == default and raw:
            return f"Raw error: code = {self.code}, parameters={self.parameters}, message={self.message}"
        try:
            message = message.format(**self.parameters)
        except KeyError as e:
            message = message \
                      + self.tr("\n Warning: some error parameters were not loaded : {}!").format(str(e))
        except Exception as e:
            if self.message:
                # Default message which can be send by api
                message = self.tr("Error {code}: {message}").format(code=self.code, message=self.message)
            else:
                message = self.tr('Unknown error while fetching errors: {exception}'
                                  '\n Error code: {code}'
                                  '\n Contact us to resolve the issue! help@geoalert.io').format(exception=str(e),
                                                                                                 code=self.code)
        return message
