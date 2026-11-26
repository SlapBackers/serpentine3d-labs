"""Build a labs plugin from the code on its Serpentine3D fork branch.

Each plugin's logic is written once, in the shape Serpentine3D itself wants,
on a branch of SlapBackers/Serpentine3D that becomes the pull request. The
plugin is that code with its imports made absolute, plus tools/<plugin>/commands.py, which registers its commands, copying
them from the branch where it says `# @extract`. Nothing is edited by
hand in plugins/, so the plugin and the pull request cannot drift apart.

    python tools/build.py meshtosolid           rebuild plugins/meshtosolid.py
    python tools/build.py meshtosolid --check   fail if it is out of date
    python tools/build.py --all --check         every plugin
    python tools/build.py NAME --source DIR     read a local checkout instead
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
import urllib.request

FORK = "SlapBackers/Serpentine3D"

PLUGINS = {
    "meshtosolid": {
        "issue": 184,
        "branch": "stl-recognise-shapes",
        "modules": ["serpentine3d/core/mesh_recognise.py"],
        "summary": [
            "meshtosolid        convert STL meshes into solids with real "
            "flat faces and holes",
            "splitdisjointmesh  split a mesh into its separate pieces",
        ],
    },
    "editdimension": {
        "issue": 182,
        "branch": "editable-dimensions",
        "modules": ["serpentine3d/core/box_dimensions.py"],
        "summary": [
            "editdimension  pick a box's edge, face or fillet and retype "
            "its size or radius",
        ],
    },
}

# In tools/<plugin>/commands.py, a line `# @extract path::function` is
# replaced by that function, decorator and all, taken from the branch: a
# command written for Serpentine3D is used as it is, not copied by hand.
_EXTRACT = re.compile(r"^([ \t]*)# @extract (\S+)::(\w+)[ \t]*$", re.M)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(module: str, branch: str, source: str | None) -> str:
    if source:
        with open(os.path.join(source, module), encoding="utf-8") as f:
            return f.read()
    url = f"https://raw.githubusercontent.com/{FORK}/{branch}/{module}"
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8")


def _absolute_imports(text: str, module: str) -> str:
    """`from .mesh import X` inside serpentine3d/core/ becomes
    `from serpentine3d.core.mesh import X`; a plugin is loaded from a file,
    not as part of the package, so relative imports have nothing to be
    relative to."""
    package = os.path.dirname(module).replace("/", ".").split(".")

    def resolve(match):
        indent, dots, rest = match.group(1), match.group(2), match.group(3)
        base = package[:len(package) - (len(dots) - 1)]
        target = ".".join(base + ([rest] if rest else []))
        return f"{indent}from {target} import"

    text = re.sub(r"^([ \t]*)from (\.+)(\w[\w.]*)? import", resolve, text,
                  flags=re.M)
    # a plugin file is one module: the future import may only open a file
    return re.sub(r"^from __future__ import annotations\n", "", text,
                  flags=re.M)


def _inlined(text: str, modules: list) -> str:
    """An import of a module this plugin carries inside itself is the
    plugin: `from serpentine3d.core import box_dimensions as bd` would look
    for a module the released app does not have."""
    for module in modules:
        package, _, leaf = module[:-3].replace("/", ".").rpartition(".")
        text = re.sub(
            rf"^([ \t]*)from {re.escape(package)} import {leaf} as (\w+)[ \t]*$",
            r"\1\2 = sys.modules[__name__]", text, flags=re.M)
    return text


def _extract(match, branch, source, modules) -> str:
    import ast
    import textwrap
    indent, path, name = match.group(1), match.group(2), match.group(3)
    text = _read(path, branch, source)
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            first = min([node.lineno] + [d.lineno for d in
                                         node.decorator_list])
            lines = text.splitlines()[first - 1:node.end_lineno]
            body = textwrap.dedent("\n".join(lines))
            body = _inlined(_absolute_imports(body, path), modules)
            return textwrap.indent(body, indent)
    raise SystemExit(f"{name} not found in {path} on {branch}")


def build(name: str, source: str | None = None) -> str:
    spec = PLUGINS[name]
    lines = [
        f"# Serpentine3D Labs plugin: {name}",
        "#",
        f"# A preview of a proposed Serpentine3D change "
        f"(chisomobanzi/Serpentine3D#{spec['issue']}).",
        "# Put this file in ~/.serpentine3d/plugins/ and restart Serpentine3D.",
        "# Commands:",
        *(f"#   {line}" for line in spec["summary"]),
        "# Delete the file to remove them.",
        "#",
        f"# Generated by tools/build.py from {FORK}, branch "
        f"{spec['branch']};",
        "# do not edit by hand. Home: "
        "https://github.com/SlapBackers/serpentine3d-labs",
        "",
    ]
    parts = ["\n".join(lines)]
    for module in spec["modules"]:
        parts.append(_absolute_imports(_read(module, spec["branch"], source),
                                       module))
    with open(os.path.join(ROOT, "tools", name, "commands.py"),
              encoding="utf-8") as f:
        commands = f.read()
    parts.append(_EXTRACT.sub(
        lambda m: _extract(m, spec["branch"], source, spec["modules"]),
        commands))
    return "\n\n".join(part.strip("\n") for part in parts) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("names", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--source")
    args = ap.parse_args(argv)
    names = list(PLUGINS) if args.all else args.names
    if not names:
        ap.error("name a plugin, or --all")
    stale = 0
    for name in names:
        path = os.path.join(ROOT, "plugins", f"{name}.py")
        text = build(name, args.source)
        if args.check:
            with open(path, encoding="utf-8") as f:
                current = f.read()
            if current != text:
                stale += 1
                print(f"{name}: out of date with its branch")
                sys.stdout.writelines(difflib.unified_diff(
                    current.splitlines(True), text.splitlines(True),
                    path, "rebuilt", n=1))
            else:
                print(f"{name}: up to date")
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"{name}: written")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
