"""QGIS-tier tests for picking a model and its optional blocks.

The split under test: `ProcessingService` owns only the settings round trip for the option
checkboxes (`wd/{workflow_id}/{block_name}`, `spec/003_local_storage.md`), `ProcessingView` owns
the widgets, and `ProcessingController` decides — which is what makes the branches below reachable
without a dialog.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PyQt5.QtCore import QObject

from mapflow.functional.controller.processing_controller import ProcessingController
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.schema import BillingType
from mapflow.schema.workflow_def import WorkflowDef


def _wd(optional_prices=(), base_price=10):
    """A workflow def with `len(optional_prices)` optional blocks after one obligatory one."""
    blocks = [{"name": "base", "displayName": "Base", "price": base_price, "optional": False}]
    blocks += [{"name": f"opt_{i}", "displayName": f"Option {i}", "price": price, "optional": True}
               for i, price in enumerate(optional_prices)]
    return WorkflowDef(id="wd-1", name="Buildings", description="Finds buildings", blocks=blocks)


def _wd_without_blocks():
    """A workflow def that declares no blocks — a flat price per sq km and no checkboxes."""
    return WorkflowDef(id="wd-1", name="Buildings", description="Finds buildings", blocks=None)


def _service(settings=None):
    service = ProcessingService.__new__(ProcessingService)
    service.app_context = SimpleNamespace(settings=settings or MagicMock())
    return service


def _controller(wd=None, billing=BillingType.credits, user_role=None):
    controller = ProcessingController.__new__(ProcessingController)
    QObject.__init__(controller)
    controller.app_context = SimpleNamespace(
        billing_type=billing,
        user_role=user_role,
        get_workflow_def=MagicMock(return_value=wd))
    controller.processing_service = MagicMock()
    controller.processing_service.saved_model_options.return_value = []
    controller.processing_view = MagicMock()
    controller.processing_view.selected_model_name.return_value = "Buildings"
    controller.processing_view.enabled_blocks.return_value = []
    controller.provider_service = MagicMock()
    return controller


# ---------- the settings round trip ----------

def test_the_options_a_model_was_last_run_with_are_remembered_per_block():
    settings = MagicMock()
    # The read asks for the value as a bool; see test_model_options_persistence for why.
    settings.value.side_effect = lambda key, default, **kwargs: key == "wd/wd-1/opt_1"
    service = _service(settings)

    assert service.saved_model_options(_wd(optional_prices=(5, 7))) == [
        ("Option 0", False), ("Option 1", True)]


def test_saved_options_keep_the_workflow_defs_order():
    """The checkbox order is what maps a tick back to a block, so it must follow the definition."""
    service = _service()
    service.app_context.settings.value.return_value = False

    names = [name for name, _checked in service.saved_model_options(_wd(optional_prices=(1, 2, 3)))]

    assert names == ["Option 0", "Option 1", "Option 2"]


def test_ticking_an_option_is_written_under_its_workflow_and_block():
    settings = MagicMock()
    service = _service(settings)

    service.save_option_settings(_wd(optional_prices=(5, 7)), [False, True])

    assert settings.setValue.call_args_list[0].args == ("wd/wd-1/opt_0", False)
    assert settings.setValue.call_args_list[1].args == ("wd/wd-1/opt_1", True)


def test_a_model_without_options_writes_nothing():
    settings = MagicMock()
    service = _service(settings)

    service.save_option_settings(_wd(), [])

    settings.setValue.assert_not_called()


# ---------- picking a model ----------

def test_choosing_a_model_narrows_the_imagery_sources_even_when_it_has_no_definition():
    """The definition is missing (a model the project offers but /user/status did not describe),
    yet leaving the previous model's providers on offer would be worse than offering none."""
    controller = _controller(wd=None)

    controller.on_model_change()

    controller.provider_service.set_available_imagery_sources.assert_called_once_with("Buildings")
    controller.processing_view.show_model_options.assert_not_called()
    controller.processing_view.show_wd_price.assert_not_called()


def test_choosing_a_model_shows_its_options_and_its_price():
    wd = _wd(optional_prices=(5,))
    controller = _controller(wd=wd)
    controller.processing_view.enabled_blocks.return_value = [False]
    controller.processing_service.saved_model_options.return_value = [("Option 0", False)]

    controller.on_model_change()

    controller.processing_view.show_model_options.assert_called_once_with(
        [("Option 0", False)], enabled=True)
    kwargs = controller.processing_view.show_wd_price.call_args.kwargs
    assert kwargs["wd_price"] == 10
    assert kwargs["wd_description"] == "Finds buildings"
    assert kwargs["display_price"] is True


@pytest.mark.parametrize("wd", [
    pytest.param(_wd_without_blocks(), id="no blocks at all"),
    pytest.param(_wd(), id="only obligatory blocks"),
    pytest.param(_wd(optional_prices=(5,)), id="an optional block"),
])
def test_choosing_a_model_asks_for_its_cost(wd):
    """Rebuilding the checkboxes is silent — each is created with its saved state before `toggled`
    is connected — so picking a model is the only thing that can quote it, whatever blocks it
    declares."""
    controller = _controller(wd=wd)
    controller.processing_view.enabled_blocks.return_value = [False] * len(wd.optional_blocks)

    controller.on_model_change()

    controller.processing_service.update_processing_cost.assert_called_once()


def test_an_area_account_is_never_quoted_a_cost():
    controller = _controller(wd=_wd_without_blocks(), billing=BillingType.area)

    controller.on_model_change()

    controller.processing_service.update_processing_cost.assert_not_called()
    assert controller.processing_view.show_wd_price.call_args.kwargs["display_price"] is False


# ---------- ticking an option ----------

def test_ticking_an_option_saves_it_reprices_and_re_asks_the_cost():
    wd = _wd(optional_prices=(5, 7))
    controller = _controller(wd=wd)
    controller.processing_view.enabled_blocks.return_value = [True, False]

    controller.on_options_change()

    controller.processing_service.save_option_settings.assert_called_once_with(wd, [True, False])
    # 10 obligatory + 5 for the ticked option; the untouched one is not counted.
    assert controller.processing_view.show_wd_price.call_args.kwargs["wd_price"] == 15
    controller.processing_service.update_processing_cost.assert_called_once()


def test_ticking_an_option_with_no_model_selected_saves_nothing():
    controller = _controller(wd=None)

    controller.on_options_change()

    controller.processing_service.save_option_settings.assert_not_called()
    controller.processing_service.update_processing_cost.assert_not_called()


# ---------- who may touch the options ----------

def test_options_are_enabled_when_the_account_has_no_role_yet():
    """`user_role` is None until /user/status answers, and `None.can_start_processing` raises."""
    controller = _controller(user_role=None)

    controller.show_wd_options(_wd(optional_prices=(5,)))

    assert controller.processing_view.show_model_options.call_args.kwargs["enabled"] is True


def test_a_role_that_may_not_start_a_processing_gets_the_options_disabled():
    controller = _controller(user_role=SimpleNamespace(can_start_processing=False))

    controller.show_wd_options(_wd(optional_prices=(5,)))

    assert controller.processing_view.show_model_options.call_args.kwargs["enabled"] is False

