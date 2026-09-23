from PyQt5.QtCore import QObject


class ErrorMessageList(QObject):
    def __init__(self):
        super().__init__()
        self.error_descriptions = {}
        # Maps a verbatim backend `message` to a translatable description, for cases where the
        # backend reports a generic `code` (e.g. "BAD_REQUEST") and the message is the only discriminator.
        self.message_descriptions = {}

    def update(self, other):
        # Overwrites on key collision. The registries merged in errors.py are
        # statically defined, so "no collisions" is a property of the source and
        # is enforced by tests/functional/test_error_message_list.py rather than
        # by a runtime assert — asserts are stripped under `python -O`, which is
        # precisely where a silent shadowed error message would be hardest to spot.
        self.error_descriptions.update(other.error_descriptions)
        self.message_descriptions.update(other.message_descriptions)

    def get(self, key, default=False):
        if default:
            default = self.tr("Unknown error. Contact us to resolve the issue! help@geoalert.io")
        return self.error_descriptions.get(key, default)

    def get_by_message(self, message, default=False):
        if default:
            default = self.tr("Unknown error. Contact us to resolve the issue! help@geoalert.io")
        return self.message_descriptions.get(message, default)
