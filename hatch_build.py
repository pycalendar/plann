"""Build-time generation of the shell tab-completion files shipped in the wheel.

Click's completion does nothing until the shell has a completion function
registered for ``plann``.  Click documents doing that through a line in a shell
rc file, which is one manual step too many.  Shipping the very same script as
wheel shared-data removes the step: bash-completion's dynamic loader resolves
the real path of the command being completed and probes
``<prefix>/share/bash-completion/completions/<cmd>``, zsh autoloads
``<prefix>/share/zsh/site-functions/_<cmd>`` and fish reads
``<prefix>/share/fish/vendor_completions.d/<cmd>.fish``.  This also covers
distribution packages built from the wheel (e.g. an AUR PKGBUILD running
``python -m installer``), as those install under ``/usr``.

The scripts are generated here rather than committed so they can never drift
from the click version in the build.  They are self-contained shell code that
runs ``plann`` itself in completion mode.  Only the program name goes into
them, so a bare ``click.Command`` stands in for the real CLI and the build does
not need plann's runtime dependencies.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

SCRIPT = "plann"
COMPLETE_VAR = "_PLANN_COMPLETE"

# Shell -> (staging basename, wheel shared-data destination).  The paths are
# fixed by the shells, not by us.
SHARED_DATA = {
    "bash": (SCRIPT, f"share/bash-completion/completions/{SCRIPT}"),
    "zsh": (f"_{SCRIPT}", f"share/zsh/site-functions/_{SCRIPT}"),
    "fish": (f"{SCRIPT}.fish", f"share/fish/vendor_completions.d/{SCRIPT}.fish"),
}


def completion_script(shell: str) -> str:
    """Return what ``_PLANN_COMPLETE=<shell>_source plann`` prints."""
    import click
    from click.shell_completion import get_completion_class

    completion = get_completion_class(shell)(click.Command(SCRIPT), {}, SCRIPT, COMPLETE_VAR)
    # Formatting the template directly rather than calling source(), which for
    # bash also probes the bash version of the build host.
    return completion.source_template % completion.source_vars()


class CompletionBuildHook(BuildHookInterface):
    """Write the completion files to a temp dir and add them to the wheel."""

    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        if self.target_name != "wheel":
            return

        self._staging = Path(tempfile.mkdtemp(prefix="plann-completions-"))
        for shell, (basename, destination) in SHARED_DATA.items():
            source = self._staging / basename
            source.write_text(completion_script(shell))
            # Absolute sources are fine here; hatchling only joins relative ones
            # against the project root.
            build_data["shared_data"][str(source)] = destination

    def finalize(self, version: str, build_data: dict[str, Any], artifact_path: str) -> None:
        staging = getattr(self, "_staging", None)
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
