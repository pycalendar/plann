"""Shell tab-completion files shipped in the wheel.

What makes Tab work with no user setup at all is the completion files
``hatch_build.py`` ships as wheel shared-data.  A typo in a destination path
lands a file somewhere the shell never looks, which no other test would notice.
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_build_hook():
    """Import the root-level ``hatch_build.py``, which is not on sys.path."""
    spec = importlib.util.spec_from_file_location("plann_hatch_build", ROOT / "hatch_build.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_completion_scripts_call_back_into_plann():
    hook = _load_build_hook()
    for shell in ("bash", "zsh", "fish"):
        script = hook.completion_script(shell)
        # Self-contained: the script runs plann itself in completion mode
        assert f"_PLANN_COMPLETE={shell}_complete" in script
        assert "plann" in script
    assert "complete -o nosort -F _plann_completion plann" in hook.completion_script("bash")
    # zsh autoloads only files whose first line carries the tag
    assert hook.completion_script("zsh").startswith("#compdef plann")


def test_build_hook_ships_completions_as_shared_data(tmp_path):
    hook = _load_build_hook()
    instance = hook.CompletionBuildHook(str(ROOT), {}, None, None, str(tmp_path), "wheel", app=None)

    build_data = {"shared_data": {}}
    instance.initialize("standard", build_data)
    try:
        # Destinations are relative to the install prefix.  bash-completion's
        # dynamic loader resolves the real path of the command and probes
        # <prefix>/share/bash-completion/completions/<cmd>; zsh autoloads from
        # <prefix>/share/zsh/site-functions/_<cmd>; fish reads
        # <prefix>/share/fish/vendor_completions.d/<cmd>.fish
        assert sorted(build_data["shared_data"].values()) == [
            "share/bash-completion/completions/plann",
            "share/fish/vendor_completions.d/plann.fish",
            "share/zsh/site-functions/_plann",
        ]
        for source in build_data["shared_data"]:
            assert "_PLANN_COMPLETE" in Path(source).read_text()
    finally:
        instance.finalize("standard", build_data, str(tmp_path / "x.whl"))
    for source in build_data["shared_data"]:
        assert not Path(source).exists()


def test_build_hook_ignores_the_sdist(tmp_path):
    hook = _load_build_hook()
    instance = hook.CompletionBuildHook(str(ROOT), {}, None, None, str(tmp_path), "sdist", app=None)
    build_data = {"shared_data": {}}
    instance.initialize("standard", build_data)
    assert build_data["shared_data"] == {}
