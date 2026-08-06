"""The duplicate_* recovery path must leave the dialog usable.

Duplicating a stored processing can fail for ordinary reasons — the model is no longer
enabled for the account, an option was removed, the source params reference something
gone. Every duplicate_* step therefore catches that, tells the user, and re-enables
processing so the dialog is not left stuck.

That recovery used to be copy-pasted into each handler, and one copy had a
transposed-letter typo (``self.aapp_context.llow_enable_processing``). There is no such
attribute, so the handler raised AttributeError on its first loop iteration and never
reached ``startProcessing.setEnabled(True)`` — leaving precisely the stuck dialog it
exists to prevent, only now with an alert already dismissed. It survived because these
paths had no test.

These tests pin the contract rather than the implementation: after a failed duplication,
every allow_enable_processing flag is True and the start button is re-enabled.
"""
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# Patch via the module object, not a dotted string: mapflow's import graph is circular
# (see tests/functional/conftest.py), so `mapflow.functional` is not yet set as an
# attribute of `mapflow` when patch() tries to walk the path, and it raises.
from mapflow.functional.service import provider_service as provider_service_module


def _service():
    """A ProviderService with just enough surface for the duplicate_* recovery path."""
    ProviderService = provider_service_module.ProviderService

    ProviderService._instance = None
    ProviderService._initialized = False

    service = ProviderService.__new__(ProviderService)
    service.dlg = MagicMock()
    # Iterating a bare MagicMock raises TypeError, which would muddy which exception the
    # handler actually saw; an empty list keeps the failure attributable to the DTO.
    service.dlg.modelOptions = []
    service.app_context = SimpleNamespace(
        allow_enable_processing={"aoi_loaded": False, "my_mosaic_loaded": False}
    )
    service.tr = lambda message: message
    return service


def _assert_dialog_recovered(service):
    assert all(service.app_context.allow_enable_processing.values()), (
        "every allow_enable_processing flag must be reset, or the dialog stays "
        "partially disabled"
    )
    service.dlg.startProcessing.setEnabled.assert_called_with(True)


def test_abort_duplication_resets_flags_and_reenables_start():
    service = _service()
    with patch.object(provider_service_module, "alert"):
        service._abort_duplication("something went wrong")
    _assert_dialog_recovered(service)


@pytest.mark.parametrize(
    "method_name",
    ["duplicate_provider", "duplicate_model", "duplicate_model_options"],
)
def test_duplicate_step_recovers_when_the_processing_is_unusable(method_name):
    """A DTO missing the attributes each step reads is the realistic stale-data case.

    The step must swallow it into the recovery path — not propagate, and not leave the
    dialog disabled.
    """
    service = _service()
    unusable = SimpleNamespace()  # no .params, no .workflowDef, no .blocks

    with patch.object(provider_service_module, "alert"):
        getattr(service, method_name)(unusable)

    _assert_dialog_recovered(service)


def test_unexpected_exception_is_logged_and_still_recovers(caplog):
    """The last-guard handler: something outside DUPLICATION_FAILURES must be surfaced
    in the log rather than silently folded into the generic alert — but the dialog
    must still be returned to a usable state.

    Uses caplog rather than patching a module attribute: the service logs through stdlib
    `logging`, so the assertion can check the record the handler would actually emit —
    including the traceback — instead of trusting that a stand-in was called.
    """
    service = _service()

    class Unexpected(Exception):
        pass

    broken = MagicMock()
    type(broken).params = property(lambda _self: (_ for _ in ()).throw(Unexpected("boom")))

    with patch.object(provider_service_module, "alert"), \
            caplog.at_level(logging.ERROR, logger="mapflow.functional.service.provider_service"):
        service.duplicate_provider(broken)

    assert caplog.records, "an unexpected exception must reach the log, not vanish"
    record = caplog.records[0]
    # exc_info is the point of logger.exception(): without it the traceback is lost and
    # an unexpected error is reduced to a message with no location.
    assert record.exc_info is not None, "the guard must record a traceback, not just a message"
    assert "boom" in caplog.text
    _assert_dialog_recovered(service)
