"""A second ProviderService is a new service bound to its own arguments.

QGIS rebuilds the plugin on an in-place upgrade (and under Plugin Reloader), and the new `Mapflow`
constructs a new ProviderService with a new `app_context`. While the class cached its first
instance, that construction handed back the previous plugin's service, still bound to the previous
`app_context` — so the live UI and the service read and wrote different state, with no error.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.config import Config
from mapflow.functional.service.provider_service import ProviderService
from mapflow.model.provider import ProvidersList


def _build(app_context):
    return ProviderService(providers=ProvidersList([]), app_context=app_context,
                           config=Config(), data_catalog_service=MagicMock())


def test_a_second_construction_is_bound_to_its_own_app_context():
    first_context, second_context = SimpleNamespace(), SimpleNamespace()

    first = _build(first_context)
    second = _build(second_context)

    assert second is not first
    assert second.app_context is second_context
    assert first.app_context is first_context  # the earlier plugin's service is left as it was
