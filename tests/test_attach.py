"""attach loads into Serpentine3D and a cylinder follows its cube."""

import pytest


def _top(shape):
    from serpentine3d.core import geometry as g
    return next(i for i, f in enumerate(g.faces_of(shape))
                if g.bbox(f)[0][2] == pytest.approx(g.bbox(shape)[1][2]))


def _scene():
    from serpentine3d.core import geometry as g
    from serpentine3d.scripting import Document
    doc = Document()
    cube = doc.add(g.make_box((0, 0, 0), 40, 30, 20), name="Cube")
    doc.add(g.make_cylinder((10, 10, 20), 3, 10), name="Cyl")
    doc.selection.set_subobjects([(cube.id, "face", _top(cube.shape))])
    return doc, cube


def test_the_cylinder_rides_the_top_when_the_cube_grows(loaded):
    from serpentine3d.core import geometry as g
    doc, cube = _scene()
    doc.run("attach", ["Cyl", "0,0,20", "Distance", "No"])
    doc.scene.replace_shape(cube.id, g.make_box((0, 0, 0), 60, 30, 35))
    lo, hi = g.bbox(doc.get("Cyl").shape)
    assert lo[2] == pytest.approx(35, abs=1e-6)
    assert (lo[0] + hi[0]) / 2 == pytest.approx(10, abs=1e-6)


def test_proportion_keeps_it_centred(loaded):
    from serpentine3d.core import geometry as g
    doc, cube = _scene()
    doc.scene.replace_shape(doc.get("Cyl").id,
                            g.make_cylinder((20, 15, 20), 3, 10))
    doc.run("attach", ["Cyl", "", "Proportion", "No"])
    doc.scene.replace_shape(cube.id, g.make_box((0, 0, 0), 60, 50, 20))
    lo, hi = g.bbox(doc.get("Cyl").shape)
    assert ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2) == pytest.approx(
        (30, 25), abs=1e-6)


def test_detach_stops_it(loaded):
    from serpentine3d.core import geometry as g
    doc, cube = _scene()
    doc.run("attach", ["Cyl", "", "Distance", "No"])
    doc.run("detach", ["Cyl", ""])
    doc.scene.replace_shape(cube.id, g.make_box((0, 0, 0), 40, 30, 35))
    assert g.bbox(doc.get("Cyl").shape)[0][2] == pytest.approx(20, abs=1e-6)
