"""The plugin loads into Serpentine3D and its command converts a real STL."""

import os
import shutil

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, "..", "meshtosolid.py")


@pytest.fixture(scope="module")
def loaded(tmp_path_factory):
    plugins = tmp_path_factory.mktemp("plugins")
    shutil.copy(PLUGIN, plugins / "meshtosolid.py")
    os.environ["SERP3D_PLUGIN_DIR"] = str(plugins)
    os.environ["SERP3D_CONFIG"] = str(plugins / "settings.json")
    from serpentine3d.plugins import load_plugins
    names = load_plugins(None)
    assert "meshtosolid" in names
    return names


def _stl_mesh(shape, tmp_path):
    from serpentine3d.fileio import stl
    path = str(tmp_path / "part.stl")
    stl.export_stl([("part", shape)], path, quality="fine")
    return stl.import_stl(path)[0][1]


def test_a_plate_with_holes_becomes_eight_faces(loaded, tmp_path):
    from serpentine3d.core import geometry as g
    from serpentine3d.scripting import Document
    plate = g.make_box((0, 0, 0), 60, 40, 8)
    for x in (15, 45):
        plate = g.boolean_difference(plate,
                                     g.make_cylinder((x, 20, -1), 3, 10))
    doc = Document()
    doc.add(_stl_mesh(plate, tmp_path), name="Plate")
    said = doc.run("meshtosolid", ["Plate", ""])
    obj = doc.get("Plate")
    assert obj.kind == "solid"
    assert len(g.faces_of(obj.shape)) == 8
    assert any("became 8 faces (a straight extrusion)" in s for s in said)


def test_a_part_with_nothing_to_find_is_still_converted(loaded):
    import numpy as np
    from serpentine3d.core import geometry as g
    from serpentine3d.core.mesh import MeshShape
    from serpentine3d.scripting import Document
    tetra = MeshShape(
        np.array([[0, 0, 0], [10, 0, 0], [0, 10, 0], [0, 0, 10]], float),
        np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]], np.uint32))
    doc = Document()
    doc.add(tetra, name="Tetra")
    said = doc.run("meshtosolid", ["Tetra", ""])
    assert any("kept as triangles" in s for s in said)
    assert len(g.faces_of(doc.get("Tetra").shape)) == 4
