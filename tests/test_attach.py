"""attach loads into Serpentine3D: a cylinder put on a cube follows it."""

import sys

import pytest


def _scene():
    from serpentine3d.core import geometry as g
    from serpentine3d.scripting import Document
    doc = Document()
    doc.add(g.make_box((0, 0, 0), 40, 30, 20), name="Cube")
    doc.add(g.make_cylinder((10, 10, 40), 3, 10), name="Cyl")
    return doc


def _attach(doc, first="", second="", keep=""):
    # typed answers: the face nearest the object, its lowest side, the
    # nearest edges; an empty distance keeps where it landed
    chip = [f"Keep={keep}"] if keep else []
    answers = ["Cyl", "Cube", "", "", *chip, first, "", *chip, second]
    return doc.run("attach", answers)


def _bottom(doc):
    from serpentine3d.core import geometry as g
    lo, hi = g.bbox(doc.get("Cyl").shape)
    return (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]


def _box(doc, *box):
    from serpentine3d.core import geometry as g
    doc.scene.replace_shape(doc.get("Cube").id, g.make_box(*box))


def test_it_is_put_on_the_top_and_rides_it(loaded):
    doc = _scene()
    said = _attach(doc)
    assert _bottom(doc) == pytest.approx((10, 10, 20), abs=1e-6)
    assert any("Cyl attached to Cube" in s for s in said)
    _box(doc, (0, 0, 0), 40, 30, 35)
    assert _bottom(doc) == pytest.approx((10, 10, 35), abs=1e-6)


def test_share_keeps_its_place_as_a_share(loaded):
    doc = _scene()
    _attach(doc, keep="Share")
    _box(doc, (0, 0, 0), 80, 30, 20)
    assert _bottom(doc)[0] == pytest.approx(20, abs=1e-6)


def test_it_turns_with_the_cube(loaded):
    from serpentine3d.core import geometry as g
    doc = _scene()
    _attach(doc)
    cube = doc.get("Cube")
    doc.scene.replace_shape(cube.id,
                            g.rotate(cube.shape, (0, 0, 0), (0, 0, 1), 90))
    assert _bottom(doc) == pytest.approx((-10, 10, 20), abs=1e-6)


def test_moving_it_by_hand_ends_the_link(loaded):
    from serpentine3d.core import geometry as g
    doc = _scene()
    _attach(doc)
    cyl = doc.get("Cyl")
    doc.scene.replace_shape(cyl.id, g.translate(cyl.shape, (3, 0, 0)))
    assert any("no longer attached" in s for s in doc.messages)
    _box(doc, (0, 0, 0), 40, 30, 35)
    assert _bottom(doc)[2] == pytest.approx(20, abs=1e-6)


def test_moved_together_it_stays_attached(loaded):
    plugin = next(m for m in list(sys.modules.values())
                  if hasattr(m, "_hook_into_the_app"))
    plugin._hook_into_the_app()          # what the app gets at startup
    doc = _scene()
    _attach(doc)
    doc.selection.set([doc.get("Cyl").id, doc.get("Cube").id])
    doc.run("move", ["0,0,0", "0,0,5"])
    assert not any("no longer attached" in s for s in doc.messages)
    _box(doc, (0, 0, 5), 40, 30, 30)
    assert _bottom(doc) == pytest.approx((10, 10, 35), abs=1e-6)


def test_unattach_stops_it(loaded):
    doc = _scene()
    _attach(doc)
    doc.run("unattach", ["Cyl", ""])
    _box(doc, (0, 0, 0), 40, 30, 35)
    assert _bottom(doc)[2] == pytest.approx(20, abs=1e-6)
