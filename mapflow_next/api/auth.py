"""Credentials live in the QGIS authentication database, never in plain settings.

- API token: a Basic auth config, applied to requests by QGIS.
- Browser sign-in: the refresh token, kept as an encrypted auth setting so the sign-in survives a
  QGIS restart. Access tokens stay in memory.
"""
from __future__ import annotations

import base64
import binascii
from typing import Optional, Tuple

from qgis.core import QgsApplication, QgsAuthMethodConfig

from ..config import Config


class AuthSetupError(Exception):
    pass


def _manager():
    return QgsApplication.authManager()


def _ok(result) -> bool:
    """PyQGIS returns (bool, config) for in/out arguments; tolerate a bare bool too."""
    return bool(result[0] if isinstance(result, tuple) else result)


def find_config(name: str) -> Optional[str]:
    manager = _manager()
    for config_id in manager.configIds():
        config = QgsAuthMethodConfig()
        manager.loadAuthenticationConfig(config_id, config)
        if config.name() == name:
            return config_id
    return None


def _ensure_master_password() -> None:
    manager = _manager()
    if manager.isDisabled():
        raise AuthSetupError("The QGIS authentication system is disabled: " + manager.disabledMessage())
    if not manager.setMasterPassword(True):
        raise AuthSetupError("QGIS needs its master password to keep your Mapflow sign-in secure.")


def decode_token(token: str) -> Tuple[str, str]:
    """A Mapflow API token is base64("login:password"); padding is optional."""
    token = (token or "").strip()
    if token.lower().startswith("basic "):
        token = token[6:].strip()
    padded = token + "=" * (-len(token) % 4)
    try:
        login, password = base64.b64decode(padded, validate=True).decode("utf-8").split(":", 1)
    except (binascii.Error, UnicodeDecodeError, ValueError) as error:
        raise ValueError("This doesn't look like a Mapflow API token.") from error
    if not login or not password:
        raise ValueError("This doesn't look like a Mapflow API token.")
    return login, password


def store_token(config: Config, token: str) -> str:
    """Save the token as a Basic auth config (replacing an older one). Returns its id."""
    login, password = decode_token(token)
    _ensure_master_password()
    manager = _manager()
    existing = find_config(config.token_config_name)
    method = QgsAuthMethodConfig()
    if existing:
        manager.loadAuthenticationConfig(existing, method, True)
    method.setName(config.token_config_name)
    method.setMethod("Basic")
    method.setConfig("username", login)
    method.setConfig("password", password)
    method.setConfig("realm", "")
    if existing:
        ok = manager.updateAuthenticationConfig(method)
    else:
        ok = _ok(manager.storeAuthenticationConfig(method))
    if not ok:
        raise AuthSetupError("Could not save the token in the QGIS authentication database.")
    return method.id()


def token_login(config_id: str) -> str:
    method = QgsAuthMethodConfig()
    _manager().loadAuthenticationConfig(config_id, method, True)
    return method.config("username", "")


def forget_token(config_id: Optional[str]) -> None:
    """Sign out of a token sign-in: delete the stored API token."""
    if config_id:
        _manager().removeAuthenticationConfig(config_id)


def store_refresh_token(config: Config, token: str) -> bool:
    """Keep the browser sign-in for next time (encrypted). Best effort: without the master password
    the sign-in still works, it just doesn't survive a restart."""
    manager = _manager()
    try:
        _ensure_master_password()
    except AuthSetupError:
        return False
    return bool(manager.storeAuthSetting(config.refresh_token_key, token, True))


def load_refresh_token(config: Config) -> str:
    manager = _manager()
    if manager.isDisabled() or not manager.existsAuthSetting(config.refresh_token_key):
        return ""
    return manager.authSetting(config.refresh_token_key, "", True) or ""


def forget_refresh_token(config: Config) -> None:
    manager = _manager()
    if not manager.isDisabled() and manager.existsAuthSetting(config.refresh_token_key):
        manager.removeAuthSetting(config.refresh_token_key)
