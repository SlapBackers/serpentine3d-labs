"""editdimension loads into Serpentine3D and runs the #182 workflow."""

import pytest


def _upright(shape):
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.GeomAbs import GeomAbs_CurveType
    from serpentine3d.core import geometry as g
    out = []
    for e in g.edges_of(shape):
        c = BRepAdaptor_Curve(e)
        if c.GetType() == GeomAbs_CurveType.GeomAbs_Line \
                and abs(c.Line().Direction().Z()) > 0.999:
            out.append(e)
    return out


def _index_along_x(shape):
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.GeomAbs import GeomAbs_CurveType
    from serpentine3d.core import geometry as g
    for i, e in enumerate(g.edges_of(shape)):
        c = BRepAdaptor_Curve(e)
        if c.GetType() == GeomAbs_CurveType.GeomAbs_Line \
                and abs(c.Line().Direction().X()) > 0.999:
            return i


def _cylinders(shape):
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_SurfaceType
    from serpentine3d.core import geometry as g
    return [(i, BRepAdaptor_Surface(f).Cylinder().Radius())
            for i, f in enumerate(g.faces_of(shape))
            if BRepAdaptor_Surface(f).GetType()
            == GeomAbs_SurfaceType.GeomAbs_Cylinder]


def _box_doc():
    from serpentine3d.core import geometry as g
    from serpentine3d.scripting import Document
    box = g.make_box((0, 0, 0), 40, 30, 20)
    doc = Document()
    obj = doc.add(g.fillet_edges(box, 3.0, edges=_upright(box)), name="Box")
    return doc, obj


def test_an_edge_grows_the_box_and_the_fillets_stay(loaded):
    from serpentine3d.core import geometry as g
    doc, obj = _box_doc()
    doc.selection.set_subobjects([(obj.id, "edge", _index_along_x(obj.shape))])
    doc.run("editdimension", ["50"])
    shape = doc.get("Box").shape
    lo, hi = g.bbox(shape)
    assert hi[0] - lo[0] == pytest.approx(50)
    assert sorted(r for _i, r in _cylinders(shape)) == pytest.approx([3] * 4)


def test_a_fillet_takes_a_new_radius(loaded):
    doc, obj = _box_doc()
    face = _cylinders(obj.shape)[0][0]
    doc.selection.set_subobjects([(obj.id, "face", face)])
    doc.run("editdimension", ["5"])
    radii = sorted(r for _i, r in _cylinders(doc.get("Box").shape))
    assert radii == pytest.approx([3, 3, 3, 5])


def test_a_cylinder_is_left_alone(loaded):
    from serpentine3d.core import geometry as g
    from serpentine3d.scripting import Document
    doc = Document()
    obj = doc.add(g.make_cylinder((0, 0, 0), 5, 10), name="Tube")
    doc.selection.set_subobjects([(obj.id, "face", 0)])
    said = doc.run("editdimension", [])
    assert any("no dimensions to edit" in s for s in said)


def _index_along_z(shape):
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.GeomAbs import GeomAbs_CurveType
    from serpentine3d.core import geometry as g
    for i, e in enumerate(g.edges_of(shape)):
        c = BRepAdaptor_Curve(e)
        if c.GetType() == GeomAbs_CurveType.GeomAbs_Line \
                and abs(c.Line().Direction().Z()) > 0.999:
            return i


def test_a_box_on_the_plane_grows_upwards(loaded):
    from serpentine3d.core import geometry as g
    doc, obj = _box_doc()
    doc.selection.set_subobjects([(obj.id, "edge", _index_along_z(obj.shape))])
    doc.run("editdimension", ["50"])
    lo, hi = g.bbox(doc.get("Box").shape)
    assert lo[2] == pytest.approx(0, abs=1e-6)
    assert hi[2] == pytest.approx(50)
