"""The duplicate-a-processing cluster announces what the form must become, rather than writing it.

ProviderService used to rebuild the start form directly — set the model combo, tick option
checkboxes, pick the source, fill the metadata table. It touches no widget now (spec/007 §
Services): each step emits a signal that `mapflow.py` wires to the view that owns the widget
(ProcessingView, ProviderView, SearchView). These pin the payloads those signals carry, so a
mis-wire in the composition root is the only way the form can go wrong — not the service.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PyQt5.QtCore import QObject

from mapflow.functional.service import provider_service as provider_service_module
from mapflow.functional.service.provider_service import ProviderService
from mapflow.schema.processing import (DataProviderParams, DataProviderSchema,
                                       MyImageryParams, MyImagerySchema)


def _service(workflow_defs=None, providers=None):
    ProviderService._instance = None
    ProviderService._initialized = False
    service = ProviderService.__new__(ProviderService)
    QObject.__init__(service)
    service.tr = lambda message: message
    service.providers = providers if providers is not None else []
    service.data_catalog_service = MagicMock()
    defs = workflow_defs or {}
    service.app_context = SimpleNamespace(
        allow_enable_processing={"aoi_loaded": False, "my_mosaic_loaded": False, "my_image_loaded": False},
        get_workflow_def=lambda name: defs.get(name))
    return service


def _record(signal):
    seen = []
    signal.connect(lambda *args: seen.append(args if len(args) != 1 else args[0]))
    return seen


# ---------- the model ----------

def test_an_available_model_is_announced_not_written():
    service = _service(workflow_defs={"Buildings": SimpleNamespace(optional_blocks=[])})
    picked = _record(service.modelSelected)

    service.duplicate_model(SimpleNamespace(workflowDef=SimpleNamespace(name="Buildings")))

    assert picked == ["Buildings"]


def test_a_missing_model_aborts_and_re_enables_start():
    service = _service(workflow_defs={})  # "Roads" not enabled for the account
    picked = _record(service.modelSelected)
    reenabled = _record(service.startEnabled)

    with patch.object(provider_service_module, "alert"):
        service.duplicate_model(SimpleNamespace(workflowDef=SimpleNamespace(name="Roads")))

    assert picked == []
    assert reenabled == [()]


def test_the_options_to_tick_are_the_processings_enabled_blocks_present_in_the_model():
    model = SimpleNamespace(optional_blocks=[SimpleNamespace(displayName="Trees"),
                                             SimpleNamespace(displayName="Cars")])
    service = _service(workflow_defs={"Buildings": model})
    ticked = _record(service.modelOptionsSet)

    processing = SimpleNamespace(
        workflowDef=SimpleNamespace(name="Buildings"),
        blocks=[SimpleNamespace(displayName="Trees", enabled=True),
                SimpleNamespace(displayName="Cars", enabled=False)])
    with patch.object(provider_service_module, "alert"):
        service.duplicate_model_options(processing)

    # Only the enabled block that still exists in the model is ticked.
    assert ticked == [["Trees"]]


# ---------- the data provider ----------

def test_an_available_data_provider_is_announced_with_its_index_and_zoom():
    providers = [SimpleNamespace(name="Mapbox", api_name="mapbox"),
                 SimpleNamespace(name="Sentinel", api_name="sentinel")]
    service = _service(providers=providers)
    chosen = _record(service.dataProviderSelected)

    provider = DataProviderParams(DataProviderSchema(providerName="sentinel", zoom="15"))
    service.duplicate_data_provider(provider)

    assert chosen == [(1, "15")]


def test_a_data_provider_not_on_the_account_aborts():
    service = _service(providers=[SimpleNamespace(name="Mapbox", api_name="mapbox")])
    chosen = _record(service.dataProviderSelected)
    reenabled = _record(service.startEnabled)

    provider = DataProviderParams(DataProviderSchema(providerName="gone", zoom="15"))
    with patch.object(provider_service_module, "alert"):
        service.duplicate_data_provider(provider)

    assert chosen == []
    assert reenabled == [()]


# ---------- my imagery ----------

def test_duplicating_a_my_imagery_mosaic_drives_the_catalog_through_its_service():
    service = _service(providers=[])
    shown = _record(service.myImageryDuplicated)

    provider = MyImageryParams(MyImagerySchema(imageIds=None, mosaicId="m-1"))
    service.duplicate_my_imagery(provider)

    # The catalog is another region: reached through its service, never its view.
    service.data_catalog_service.clear_mosaic_selection.assert_called_once()
    service.data_catalog_service.select_mosaic_cell.assert_called_once_with("m-1")
    service.data_catalog_service.set_catalog_provider.assert_called_once()
    assert shown == [()]  # bring the catalog tab forward
