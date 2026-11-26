"""Publish a plugin's current version as a GitHub release.

    python tools/release.py editdimension

Checks the plugin is up to date with its branch and has a changelog entry,
then tags `<plugin>-v<version>` and creates a release with the plugin file
attached and that version's changelog entry as its notes. Needs the `gh`
command, signed in to an account that can publish to this repository.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402


def _notes(name: str, version: str) -> str:
    text = build._changelog()
    match = re.search(rf"^## {re.escape(name)} {re.escape(version)}\n(.*?)"
                      r"(?=^## |\Z)", text, flags=re.M | re.S)
    if not match:
        raise SystemExit(f"CHANGELOG.md has no entry for {name} {version}")
    return match.group(1).strip()


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0] not in build.PLUGINS:
        raise SystemExit(f"usage: release.py {{{','.join(build.PLUGINS)}}}")
    name = argv[0]
    version = build.PLUGINS[name]["version"]
    if build.main([name, "--check"]):
        raise SystemExit("rebuild the plugin first: python tools/build.py "
                         + name)
    tag = f"{name}-v{version}"
    path = os.path.join(build.ROOT, "plugins", f"{name}.py")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(_notes(name, version))
        f.write(f"\n\nInstall: put `{name}.py` in `~/.serpentine3d/plugins/`"
                " and restart Serpentine3D.\n")
    subprocess.run(["gh", "release", "create", tag, path,
                    "--title", f"{name} {version}", "--notes-file", f.name,
                    "--target", "main"], check=True, cwd=build.ROOT)
    os.unlink(f.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
