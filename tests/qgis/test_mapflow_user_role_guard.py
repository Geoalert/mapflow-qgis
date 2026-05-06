from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.mapflow import Mapflow


def test_show_wd_options_handles_missing_user_role():
    plugin = Mapflow.__new__(Mapflow)
    plugin.dlg = MagicMock()
    plugin.app_context = SimpleNamespace(settings=MagicMock(), user_role=None)
    plugin.app_context.settings.value.return_value = False

    wd = SimpleNamespace(
        id="wd-id",
        optional_blocks=[SimpleNamespace(displayName="Block 1", name="block_1")],
    )

    plugin.show_wd_options(wd)

    plugin.dlg.enable_model_options.assert_called_once_with(True)
