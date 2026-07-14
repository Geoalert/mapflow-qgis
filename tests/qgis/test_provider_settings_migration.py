"""QGIS-tier tests for loading user providers from settings after the legacy Maxar/Sentinel
removal. Maxar providers are stored in the user's QgsSettings (not built in); loading a
removed provider type must NOT error — it is silently discarded and purged on the next save,
so the plugin still starts. Genuinely broken providers of a supported type are still reported."""
import json
from unittest.mock import MagicMock

from mapflow.entity.provider.collection import ProvidersList


def _settings(providers_dict):
    settings = MagicMock()
    settings.value.return_value = json.dumps(providers_dict)
    return settings


def _xyz(name="My XYZ"):
    return {
        "name": name,
        "source_type": "xyz",
        "option_name": "xyz",
        "url": "https://tiles.example.com/{z}/{x}/{y}.png",
        "credentials": ["", ""],
        "save_credentials": False,
        "crs": "EPSG:3857",
    }


def _legacy_maxar(name="Maxar SecureWatch"):
    return {
        "name": name,
        "source_type": "xyz",
        "option_name": "Maxar WMTS",  # removed provider type
        "url": "https://securewatch.digitalglobe.com/earthservice/wmtsaccess?connectid=x",
        "credentials": ["u", "p"],
        "save_credentials": True,
        "crs": "EPSG:3857",
    }


def test_legacy_maxar_provider_is_discarded_without_error():
    settings = _settings({"Maxar SecureWatch": _legacy_maxar(), "My XYZ": _xyz()})

    providers, errors = ProvidersList.from_settings(settings)

    names = [p.name for p in providers]
    assert names == ["My XYZ"]  # Maxar dropped
    assert errors == []  # discarding a removed type is not an error


def test_only_legacy_providers_yields_empty_list_no_error():
    settings = _settings({"Maxar SecureWatch": _legacy_maxar()})

    providers, errors = ProvidersList.from_settings(settings)

    assert list(providers) == []
    assert errors == []


def test_discarded_providers_are_purged_on_save():
    settings = _settings({"Maxar SecureWatch": _legacy_maxar(), "My XYZ": _xyz()})
    providers, _ = ProvidersList.from_settings(settings)

    providers.to_settings(settings)

    saved = json.loads(settings.setValue.call_args.args[1])
    assert "Maxar SecureWatch" not in saved
    assert "My XYZ" in saved


def test_broken_supported_provider_is_still_reported():
    broken = _xyz("Broken")
    broken.pop("url")  # missing required arg -> create_provider raises
    settings = _settings({"Broken": broken, "My XYZ": _xyz()})

    providers, errors = ProvidersList.from_settings(settings)

    assert errors == ["Broken"]
    assert [p.name for p in providers] == ["My XYZ"]


def test_no_providers_key_is_noop():
    settings = MagicMock()
    settings.value.return_value = "{}"

    providers, errors = ProvidersList.from_settings(settings)

    assert list(providers) == []
    assert errors == []
