"""The account's role gates what the start panel offers.

`show_wd_options` moved from `Mapflow` to `ProcessingController`; the guard it tests did not
move — `user_role` is None until /user/status answers, and reading `can_start_processing` off
None raises. The role cases live with the rest of the model-options behaviour in
`test_model_options.py`; this file keeps the guard on its own because it is a crash, not a
preference.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from PyQt5.QtCore import QObject

from mapflow.functional.controller.processing_controller import ProcessingController


def test_show_wd_options_handles_missing_user_role():
    controller = ProcessingController.__new__(ProcessingController)
    QObject.__init__(controller)
    controller.app_context = SimpleNamespace(user_role=None)
    controller.processing_service = MagicMock()
    controller.processing_service.saved_model_options.return_value = [("Block 1", False)]
    controller.processing_view = MagicMock()

    wd = SimpleNamespace(
        id="wd-id",
        optional_blocks=[SimpleNamespace(displayName="Block 1", name="block_1")],
    )

    controller.show_wd_options(wd)

    controller.processing_view.show_model_options.assert_called_once_with(
        [("Block 1", False)], enabled=True)
