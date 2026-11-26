"""Every labs plugin, loaded into Serpentine3D the way the app loads them."""

import os
import shutil

import pytest

PLUGINS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                       "plugins")


@pytest.fixture(scope="session")
def loaded(tmp_path_factory):
    folder = tmp_path_factory.mktemp("plugins")
    for name in os.listdir(PLUGINS):
        if name.endswith(".py"):
            shutil.copy(os.path.join(PLUGINS, name), folder / name)
    os.environ["SERP3D_PLUGIN_DIR"] = str(folder)
    os.environ["SERP3D_CONFIG"] = str(folder / "settings.json")
    from serpentine3d.plugins import load_plugins
    names = load_plugins(None)
    expected = {n[:-3] for n in os.listdir(PLUGINS) if n.endswith(".py")}
    assert expected <= set(names), f"not loaded: {expected - set(names)}"
    return names
