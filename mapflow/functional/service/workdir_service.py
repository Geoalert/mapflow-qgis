"""The working directory: where the plugin writes results, AOIs and cached search layers.

Holds no widget (`spec/007_architecture.md` § Layer rules). Choosing a directory is a file dialog
and explaining why one is needed is a message box; both are `WorkdirView`'s. What is here is the
part with no UI in it — what the configured path currently is, whether it can actually be written
to, and creating the ``Temp`` subdirectory under it.
"""
import logging
import shutil
from pathlib import Path
from typing import Optional

from ..app_context import AppContext

logger = logging.getLogger(__name__)

#: Everything the plugin writes goes under this subdirectory of the user's chosen output
#: directory, so cleaning up never touches anything of theirs that sits alongside it.
TEMP_SUBDIRECTORY = "Temp"


class WorkdirService:
    """Where the plugin may write, and whether it currently can."""

    def __init__(self, app_context: AppContext):
        self.app_context = app_context

    @property
    def configured_path(self) -> str:
        """What the user last chose, whether or not it still exists."""
        return self.app_context.settings.value('outputDir') or ""

    def remember(self, path: str) -> None:
        self.app_context.settings.setValue('outputDir', path)

    def is_usable(self) -> bool:
        """Whether results can be written right now.

        Checks the directory still exists rather than trusting the setting: it is remembered
        across sessions, and an external drive or a deleted folder makes it stale.
        """
        temp_dir = self.app_context.temp_dir
        return temp_dir is not None and temp_dir.exists()

    def setup_tempdir(self) -> Optional[str]:
        """Create the working ``Temp`` directory under the configured output directory.

        Returns ``None`` on success (or when no output directory is configured), or a
        human-readable error string when the directory is unavailable. **Never raises**: this runs
        during plugin startup (``classFactory``), and a failure here must not abort the whole
        plugin. The directory can be unusable for several reasons — an external drive that is not
        mounted (its ``/Volumes/<name>`` stub is left root-owned and unwritable -> PermissionError),
        a deleted parent (FileNotFoundError), a read-only or full filesystem — so it catches
        broadly and falls back to "no working directory", letting the user pick another.
        """
        output_dir = self.configured_path
        if not output_dir:
            return None  # don't ask for a directory at plugin start
        temp_dir = Path(output_dir, TEMP_SUBDIRECTORY)
        try:
            shutil.rmtree(temp_dir)  # remove the previous session's temp dir
        except Exception as e:
            # Best-effort cleanup of a stale directory; the run continues either way.
            logger.warning("Could not remove old temp dir '%s': %s", temp_dir, e)
        try:
            temp_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.app_context.temp_dir = None
            logger.exception("Working directory '%s' is unavailable", output_dir)
            return str(e)
        self.app_context.temp_dir = temp_dir
        return None
