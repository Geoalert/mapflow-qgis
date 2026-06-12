"""Shared fixtures for the mapflow test suite.

Tier-specific bootstrap (PyQGIS startup, sys.modules stubs, Xvfb wiring)
lives in tests/functional/conftest.py, tests/qgis/conftest.py, and
tests/ui/conftest.py. Keep this file empty unless a fixture is genuinely
needed by every tier.
"""
