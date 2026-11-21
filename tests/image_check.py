"""Tells the test images (the containers `make` runs) from a developer's host. Pure Python, no qgis import."""
from pathlib import Path
from typing import Iterable

IMAGE_ROOT = Path("/app")                                  # the Makefile bind-mounts the repo here
CONTAINER_MARKERS = ("/.dockerenv", "/run/.containerenv")  # Docker and Podman


def in_test_image(root: Path, markers: Iterable[str] = CONTAINER_MARKERS) -> bool:
    """True inside a container with the repo mounted at /app, as `make test-*` runs it."""
    return Path(root).resolve() == IMAGE_ROOT and any(Path(marker).exists() for marker in markers)


def missing_qgis_outcome(root: Path, markers: Iterable[str] = CONTAINER_MARKERS) -> str:
    """What a missing qgis.core means: "fail" in the test images, "skip" on a host without QGIS."""
    return "fail" if in_test_image(root, markers) else "skip"
