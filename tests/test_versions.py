"""Every plugin says which version it is, and it is the one being built."""

import os
import sys

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                     "tools")


def test_each_loaded_plugin_knows_its_version(loaded):
    sys.path.insert(0, TOOLS)
    try:
        import build
    finally:
        sys.path.remove(TOOLS)
    for name, spec in build.PLUGINS.items():
        module = sys.modules[f"serpentine3d_plugin_{name}"]
        assert module.__version__ == spec["version"]
