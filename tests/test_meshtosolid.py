"""meshtosolid loads into Serpentine3D and converts real STLs."""


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
    assert any("Tetra: left as a mesh" in s for s in said)
    assert doc.get("Tetra").kind == "mesh"


def _two_plates(tmp_path):
    from serpentine3d.core import geometry as g
    from serpentine3d.core.mesh import merge
    plate = g.make_box((0, 0, 0), 60, 40, 8)
    for x in (15, 45):
        plate = g.boolean_difference(plate,
                                     g.make_cylinder((x, 20, -1), 3, 10))
    a = _stl_mesh(plate, tmp_path)
    b = _stl_mesh(g.translate(plate, (0, 100, 0)), tmp_path)
    return merge([a, b])


def test_separate_pieces_become_separate_solids(loaded, tmp_path):
    from serpentine3d.core import geometry as g
    from serpentine3d.scripting import Document
    doc = Document()
    doc.add(_two_plates(tmp_path), name="Parts")
    doc.run("meshtosolid", ["Parts", ""])
    assert doc.get("Parts") is None
    for name in ("Parts 1", "Parts 2"):
        assert doc.get(name).kind == "solid"
        assert len(g.faces_of(doc.get(name).shape)) == 8


def test_splitdisjointmesh_makes_one_mesh_per_piece(loaded, tmp_path):
    from serpentine3d.scripting import Document
    doc = Document()
    doc.add(_two_plates(tmp_path), name="Parts")
    doc.run("splitdisjointmesh", ["Parts", ""])
    assert doc.get("Parts 1").kind == "mesh"
    assert doc.get("Parts 2").kind == "mesh"
