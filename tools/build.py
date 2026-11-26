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
        "version": "0.3.0",
        "issue": 184,
        "branch": "stl-recognise-shapes",
        "modules": ["serpentine3d/core/mesh_parts.py",
                    "serpentine3d/core/mesh_snaps.py",
                    "serpentine3d/core/mesh_recognise.py"],
        "summary": [
            "meshparts          split an STL into its parts",
            "meshtosolid        convert STL parts into solids with real "
            "flat faces and holes",
            "splitdisjointmesh  split a mesh into every separate piece",
            "and: imported meshes snap to their corners and hole centres",
        ],
    },
    "editdimension": {
        "version": "0.3.0",
        "issue": 182,
        "branch": "editable-dimensions",
        "modules": ["serpentine3d/core/solid_dimensions.py"],
        "summary": [
            "editdimension  pick an edge or face and retype a size, fillet, "
            "chamfer or hole",
        ],
    },
    "attach": {
        "version": "0.1.0",
        "issue": 0,
        "branch": "attach",
        "modules": ["serpentine3d/core/attachments.py"],
        "summary": [
            "attach  attach an object to a face so it follows when the "
            "face moves",
            "detach  take an attachment away",
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
        dotted = module[:-3].replace("/", ".")
        package, _, leaf = dotted.rpartition(".")
        text = re.sub(
            rf"^([ \t]*)from {re.escape(package)} import {leaf} as (\w+)[ \t]*$",
            r"\1\2 = sys.modules[__name__]", text, flags=re.M)
        # `from serpentine3d.core.mesh_parts import components`: the name is
        # already defined in the plugin, so the import has nothing to do
        text = re.sub(
            rf"^([ \t]*)from {re.escape(dotted)} import [\w, ]+[ \t]*$",
            r"\1pass  # carried in this plugin", text, flags=re.M)
    return text


def _top_names(text: str) -> set:
    import ast
    names = set()
    for node in ast.parse(text).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target,
                                                           ast.Name):
            names.add(node.target.id)
    return names


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
        f"# Serpentine3D Labs plugin: {name} {spec['version']}",
        "#",
        (f"# A preview of a proposed Serpentine3D change "
         f"(chisomobanzi/Serpentine3D#{spec['issue']})." if spec["issue"]
         else "# A preview of a change to be proposed to Serpentine3D."),
        "# Put this file in ~/.serpentine3d/plugins/ and restart Serpentine3D.",
        "# Commands:",
        *(f"#   {line}" for line in spec["summary"]),
        "# Delete the file to remove them.",
        "#",
        f"# Generated by tools/build.py from {FORK}, branch "
        f"{spec['branch']};",
        "# do not edit by hand. Home: "
        "https://github.com/SlapBackers/serpentine3d-labs",
        "# Changes: see CHANGELOG.md there.",
        "",
        f'__version__ = "{spec["version"]}"',
    ]
    parts = ["\n".join(lines)]
    defined = {}
    for module in spec["modules"]:
        text = _absolute_imports(_read(module, spec["branch"], source), module)
        # modules joined into one file share one namespace: the same name
        # in two of them would quietly become the last one's
        for top in _top_names(text):
            if top in defined:
                raise SystemExit(f"{top} is defined in both {defined[top]} "
                                 f"and {module}; rename one on the branch")
            defined[top] = module
        parts.append(_inlined(text, spec["modules"]))
    with open(os.path.join(ROOT, "tools", name, "commands.py"),
              encoding="utf-8") as f:
        commands = f.read()
    parts.append(_EXTRACT.sub(
        lambda m: _extract(m, spec["branch"], source, spec["modules"]),
        commands))
    return "\n\n".join(part.strip("\n") for part in parts) + "\n"


def _changelog() -> str:
    with open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as f:
        return f.read()


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
            if f"## {name} {PLUGINS[name]['version']}" not in _changelog():
                stale += 1
                print(f"{name}: CHANGELOG.md has no entry for "
                      f"{PLUGINS[name]['version']}")
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
