"""Functional-tier tests: the `mapflow_ru` variable (spec/002_api.md, section "The `mapflow.ru` domain").

The variable changes only the domain of the Mapflow addresses. `Config` reads it once, at import, so
these tests check the pure functions that `Config` and its users call, with the real texts of `Config`.
"""
import json

import pytest

from mapflow.config import Config
from mapflow.domain import DEFAULT_DOMAIN, RU_DOMAIN, domain_from_setting, text_with_domain, url_with_domain
from mapflow.functional.auth import config_text_on_domain


# ---------- the variable ----------

@pytest.mark.parametrize("value", ["true", "True", "TRUE", "  true  ", True])
def test_true_in_any_case_turns_the_setting_on(value):
    assert domain_from_setting(value) == RU_DOMAIN


@pytest.mark.parametrize("value", ["", None, "false", "False", "1", "yes", "truee", "mapflow.ru", False])
def test_every_other_value_keeps_the_default_domain(value):
    assert domain_from_setting(value) == DEFAULT_DOMAIN


def test_without_the_variable_the_config_is_on_the_default_domain():
    assert Config.DOMAIN == DEFAULT_DOMAIN
    assert Config.SERVER.startswith("https://whitemaps-")
    assert Config.SERVER.endswith(".mapflow.ai/rest")
    assert Config.TOP_UP_URL == "https://app.mapflow.ai/account/balance"
    assert Config.AUTH_CONFIG_MAP == Config.AUTH_CONFIG_MAPS.get(Config.MAPFLOW_ENV, '')


# ---------- the server address ----------

@pytest.mark.parametrize("env", ["production", "staging", "internal", "duty"])
def test_the_server_address_keeps_everything_but_the_domain(env):
    address = "https://whitemaps-{env}.mapflow.ai/rest".format(env=env)

    assert text_with_domain(address, RU_DOMAIN) == "https://whitemaps-{env}.mapflow.ru/rest".format(env=env)
    assert text_with_domain(address, DEFAULT_DOMAIN) == address


# ---------- the sign-in configuration ----------

@pytest.mark.parametrize("env", sorted(Config.AUTH_CONFIG_MAPS))
def test_the_sign_in_configuration_changes_only_its_addresses(env):
    stored = Config.AUTH_CONFIG_MAPS[env]
    before = json.loads(stored)

    after = json.loads(config_text_on_domain(stored, RU_DOMAIN))

    address_keys = {"requestUrl", "tokenUrl", "refreshTokenUrl"}
    for key in address_keys:
        assert after[key] == before[key].replace("mapflow.ai", "mapflow.ru")
        assert "mapflow.ru/auth/realms/" in after[key]
    assert {k: v for k, v in after.items() if k not in address_keys} \
        == {k: v for k, v in before.items() if k not in address_keys}
    assert DEFAULT_DOMAIN not in config_text_on_domain(stored, RU_DOMAIN)


@pytest.mark.parametrize("env", sorted(Config.AUTH_CONFIG_MAPS))
def test_the_sign_in_configuration_goes_back_to_the_default_domain(env):
    """A user who removes the variable gets the stored configuration back as it was."""
    stored = Config.AUTH_CONFIG_MAPS[env]

    assert config_text_on_domain(stored, DEFAULT_DOMAIN) == stored
    assert config_text_on_domain(config_text_on_domain(stored, RU_DOMAIN), DEFAULT_DOMAIN) == stored
    assert config_text_on_domain(config_text_on_domain(stored, RU_DOMAIN), RU_DOMAIN) \
        == config_text_on_domain(stored, RU_DOMAIN)


# ---------- the links in a text ----------

def test_every_link_of_a_text_changes():
    text = ('<a href="https://app.mapflow.ai/account/api">Get token</a>'
            '<a href="https://mapflow.ai/terms-of-use-en.pdf">Terms of use</a>'
            'Register at <a href="https://mapflow.ai">mapflow.ai</a> to use the plugin. '
            'See https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup or mapflow.ai.')

    assert text_with_domain(text, RU_DOMAIN) == (
        '<a href="https://app.mapflow.ru/account/api">Get token</a>'
        '<a href="https://mapflow.ru/terms-of-use-en.pdf">Terms of use</a>'
        'Register at <a href="https://mapflow.ru">mapflow.ru</a> to use the plugin. '
        'See https://docs.mapflow.ru/api/qgis_mapflow.html#oauth2_setup or mapflow.ru.')
    assert text_with_domain(text, DEFAULT_DOMAIN) == text


@pytest.mark.parametrize("text", [
    "help@geoalert.io",
    "name@mapflow.ai",
    "https://notmapflow.ai/pricing",
    "https://mapflow.ai.example.com/pricing",
    "https://mapflow.aix/pricing",
    "https://github.com/Geoalert/mapflow-qgis/issues",
    "Mapflow",
    "",
])
def test_a_text_without_the_domain_stays(text):
    assert text_with_domain(text, RU_DOMAIN) == text


def test_a_value_that_is_not_text_stays():
    assert text_with_domain(None, RU_DOMAIN) is None
    assert url_with_domain(None, RU_DOMAIN) is None


# ---------- an address from a server answer ----------

@pytest.mark.parametrize("url, expected", [
    ("https://whitemaps-production.mapflow.ai/rest/rasters/image/x/preview/l",
     "https://whitemaps-production.mapflow.ru/rest/rasters/image/x/preview/l"),
    ("https://tiles.mapflow.ai/{z}/{x}/{y}.png?sig=a%2Fb&from=mapflow.ai",
     "https://tiles.mapflow.ru/{z}/{x}/{y}.png?sig=a%2Fb&from=mapflow.ai"),
    ("http://mapflow.ai:8080/a", "http://mapflow.ru:8080/a"),
    ("https://user@app.mapflow.ai/x", "https://user@app.mapflow.ru/x"),
    ("https://APP.MAPFLOW.AI/x", "https://APP.mapflow.ru/x"),
    ("https://mapflow.ai", "https://mapflow.ru"),
    ("https://mapflow.ai?x=1", "https://mapflow.ru?x=1"),
])
def test_only_the_host_of_a_server_address_changes(url, expected):
    assert url_with_domain(url, RU_DOMAIN) == expected
    assert url_with_domain(url, DEFAULT_DOMAIN) == url


@pytest.mark.parametrize("url", [
    "https://example.com/mapflow.ai/x",
    "https://s3.amazonaws.com/bucket/key?host=mapflow.ai",
    "https://notmapflow.ai/x",
    "https://mapflow.ai.example.com/x",
    "https://mapflow.ai@example.com/x",
    "ftp://mapflow.ai/x",
    "/rest/mapflow.ai",
    "https://[::1]/mapflow.ai",
    "",
])
def test_an_address_of_another_host_stays(url):
    assert url_with_domain(url, RU_DOMAIN) == url


def test_an_address_goes_back_to_the_default_domain():
    assert url_with_domain("https://app.mapflow.ru/x", DEFAULT_DOMAIN, RU_DOMAIN) == "https://app.mapflow.ai/x"
