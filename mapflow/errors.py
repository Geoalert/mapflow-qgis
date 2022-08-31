from typing import Dict
from translate import tr
"""
["messages":[{"code":"source-validator.PixelSizeTooHigh","parameters":{"max_res":"1.2","level":"error","actual_res":"5.620983603290215"}}]}]
"""


class ErrorMessage():
    def __init__(self, code: str, parameters: Dict[str,str]):
        self.code = code
        self.parameters = parameters
        self.message = "error"
        # todo: get the real message from local file

    @classmethod
    def from_response(cls, response: Dict):
        return cls(response['code'], response['parameters'])

    def __str__(self):
        return tr(self.message).format(**self.parameters)