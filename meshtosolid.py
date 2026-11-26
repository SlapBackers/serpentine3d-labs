# Serpentine3D plugin: try the meshtobrep prototype (#184) in the released app.
#
# Copy this file into ~/.serpentine3d/plugins/ and restart Serpentine3D.
# It adds two commands:
#   meshtosolid        what the prototype branch's meshtobrep does
#   splitdisjointmesh  split a mesh into its separate pieces (Rhino's name)
# Delete the file to remove them. Generated from SlapBackers/Serpentine3D,
# branch stl-recognise-shapes.
# Home: https://github.com/SlapBackers/serpentine3d-meshtosolid

"""Turn a closed triangle mesh back into the solid it was cut from.

meshtobrep used to make one flat face per triangle, so a printed bracket of
50,000 triangles came back as 50,000 faces: slow to boolean, impossible to
fillet, and not even closed into a solid. Most meshes worth editing are
mechanical parts, flat faces and round holes, and those can be found again.

Two passes, then a check:

1. A straight extrusion. Plates, brackets and spacers are one outline pushed
   straight through. For each of the mesh's main normal directions, every
   triangle has to lie on one of two parallel caps or stand square to them.
   If so, the outline of a cap is fitted with lines, arcs and circles and
   extruded, so the holes come back as true cylinders.
2. Flat regions. Otherwise, neighbouring triangles on one plane are grouped
   and each group becomes a single flat face; what is curved stays as
   triangles, so a part that is half recognised is still half cleaner.
3. The check. The solid is measured against the mesh before it is handed
   back. One that is open, invalid or of the wrong volume is not returned:
   the caller falls back to the faceted shell, and is told why.

The extrusion test and the check follow SolidCraft's Convert Mesh
(solidcore/crates/solidcore/src/mesh_reconstruction, Apache-2.0), written
afresh here; the region pass is what reaches parts that are not extrusions.
"""



import math
from dataclasses import dataclass

import numpy as np

from serpentine3d.core import occ
from serpentine3d.core.mesh import MeshShape, _weld

# The most directions tried as an extrusion axis, largest area first. A real
# extrusion's axis is the normal of its caps, which are never small.
_MAX_AXES = 16
# Two triangles are on one plane when their normals agree this closely.
_COPLANAR_DEG = 0.5
# A vertex where the outline turns by less than this, between chords of
# similar length, is inside an arc rather than at a corner.
_SMOOTH_TURN_DEG = 25.0
_SIMILAR_CHORDS = 2.5
# The flat-regions pass only goes ahead when groups of at least this many
# coplanar triangles cover most of the part, and the solid would not have
# an unworkable number of faces.
_FLAT_GROUP = 3
_FOLD_DEG = 30.0        # sharper than this between faces is an edge drawn
_MOST_CURVED = 0.5
_MAX_FACES = 20000
# Fewest points that make a whole loop a circle rather than a polygon: a
# hexagon is a nut and an octagon is drawn on purpose, not a hole. Every
# export of a round hole worth editing has more sides than this.
_MIN_CIRCLE_POINTS = 12


class RecogniseError(Exception):
    """The mesh could not be rebuilt; the caller should keep the facets."""


@dataclass
class Recognised:
    shape: object           # a TopoDS solid
    kind: str               # "extrusion" or "faces"
    faces: int              # how many faces the solid has
    triangles: int          # how many triangles it came from


def default_tolerance(mesh: MeshShape) -> float:
    """How far a fitted line or arc may stray from the mesh's points.

    STL keeps coordinates as float32, about seven digits, and a CAD export
    puts its points on the true curve, so a point is off its circle only by
    rounding. A hundred-thousandth of the part's size is well clear of that
    and still far finer than anything a printer resolves."""
    lo, hi = mesh.bbox()
    diag = float(np.linalg.norm(np.subtract(hi, lo)))
    return max(diag * 1e-5, 1e-4)


def recognise(mesh: MeshShape, tolerance: float | None = None) -> Recognised:
    """The solid a closed mesh describes, as few faces as can be found.

    Raises RecogniseError when the mesh is not closed or neither pass gives
    a solid that matches it; nothing faceted is ever returned from here."""
    if tolerance is None:
        tolerance = default_tolerance(mesh)
    prepared = _Prepared(mesh)
    if not prepared.closed:
        raise RecogniseError("the mesh is not closed, so it has no inside")
    for axis in prepared.axes():
        shape = _extrusion(prepared, axis, tolerance)
        if shape is not None:
            return Recognised(shape, "extrusion", _face_count(shape),
                              len(prepared.tris))
    shape = _flat_regions(prepared, tolerance)
    return Recognised(shape, "faces", _face_count(shape), len(prepared.tris))


def convert_pieces(mesh: MeshShape, name: str, echo=None) -> list:
    """[(name, shape)] for each separate piece of the mesh: a solid where
    one was recognised, the piece itself, still a mesh, where not.

    Shared by meshtobrep and the plugin, so both say the same things.
    A lone piece keeps the mesh's name; several are numbered."""
    say = echo or (lambda _text: None)
    pieces = split_pieces(mesh)
    if len(pieces) > 1:
        say(f"{name}: {len(pieces)} separate parts.")
    out = []
    for k, piece in enumerate(pieces, 1):
        label = name if len(pieces) == 1 else f"{name} {k}"
        try:
            found = recognise(piece)
        except RecogniseError as exc:
            say(f"{label}: left as a mesh, {exc}.")
            out.append((label, piece))
            continue
        what = ("a straight extrusion" if found.kind == "extrusion"
                else "flat faces")
        say(f"{label}: {found.triangles:,} triangles became "
            f"{found.faces:,} faces ({what}).")
        out.append((label, found.shape))
    return out


# --- separate parts ---------------------------------------------------------

def split_pieces(mesh: MeshShape) -> list:
    """The mesh's separate pieces, largest first: Rhino's SplitDisjointMesh.

    An STL has no notion of parts, but a file exported from an assembly is
    several closed pieces that never touch. Each is found as the triangles
    that reach one another through shared corners."""
    points, canonical = _weld(np.asarray(mesh.vertices, np.float64))
    tris = canonical[np.asarray(mesh.triangles, np.int64)]
    if not len(tris):
        return [mesh]
    # Every corner takes the smallest label among the triangles it is in,
    # then labels are chased to their root; repeated until nothing moves.
    label = np.arange(len(points))
    while True:
        lowest = label[tris].min(axis=1)
        moved = label.copy()
        np.minimum.at(moved, tris.ravel(), np.repeat(lowest, 3))
        while True:
            chased = moved[moved]
            if np.array_equal(chased, moved):
                break
            moved = chased
        if np.array_equal(moved, label):
            break
        label = moved
    owner = label[tris[:, 0]]
    roots, piece_of, sizes = np.unique(owner, return_inverse=True,
                                       return_counts=True)
    if len(roots) == 1:
        return [mesh]
    piece_of = np.asarray(piece_of).ravel()
    pieces = []
    for k in np.argsort(-sizes, kind="stable"):
        own = tris[piece_of == k]
        used, local = np.unique(own, return_inverse=True)
        pieces.append(MeshShape(points[used],
                                np.asarray(local).reshape(-1, 3)))
    return pieces


# --- the mesh, welded and measured ------------------------------------------

class _Prepared:
    """Welded points, triangles of real area, their normals and edges."""

    def __init__(self, mesh: MeshShape):
        points, canonical = _weld(np.asarray(mesh.vertices, np.float64))
        tris = canonical[np.asarray(mesh.triangles, np.int64)]
        distinct = ((tris[:, 0] != tris[:, 1]) & (tris[:, 1] != tris[:, 2])
                    & (tris[:, 0] != tris[:, 2]))
        tris = tris[distinct]
        p0, p1, p2 = (points[tris[:, i]] for i in range(3))
        cross = np.cross(p1 - p0, p2 - p0)
        double_area = np.linalg.norm(cross, axis=1)
        diag = float(np.linalg.norm(points.max(0) - points.min(0))) \
            if len(points) else 0.0
        real = double_area > (diag * 1e-9) ** 2
        self.points = points
        self.tris = tris[real]
        self.cross = cross[real]
        self.areas = double_area[real] / 2
        self.normals = self.cross / double_area[real][:, None]
        self.size = diag
        self.closed, self.pairs = self._edges()

    def _edges(self):
        """Whether every edge has two triangles running opposite ways, and
        the pairs of triangles that meet along an edge."""
        tris = self.tris
        if not len(tris):
            return False, np.zeros((0, 2), np.int64)
        n = len(self.points)
        start = tris.ravel()
        end = tris[:, [1, 2, 0]].ravel()
        key = np.minimum(start, end) * n + np.maximum(start, end)
        forward = start < end
        owner = np.repeat(np.arange(len(tris)), 3)
        order = np.argsort(key, kind="stable")
        key, forward, owner = key[order], forward[order], owner[order]
        firsts = np.concatenate(([0], np.flatnonzero(key[1:] != key[:-1]) + 1))
        counts = np.diff(np.concatenate((firsts, [len(key)])))
        if not np.all(counts == 2):
            return False, np.zeros((0, 2), np.int64)
        if np.any(forward[firsts] == forward[firsts + 1]):
            return False, np.zeros((0, 2), np.int64)
        return True, np.column_stack((owner[firsts], owner[firsts + 1]))

    def axes(self):
        """The directions a cap could face, by how much area faces them."""
        n = self.normals.copy()
        flip = (n[:, 0] < -1e-9) | ((np.abs(n[:, 0]) <= 1e-9) & (
            (n[:, 1] < -1e-9) | ((np.abs(n[:, 1]) <= 1e-9) & (n[:, 2] < 0))))
        n[flip] *= -1
        keys = np.round(n * 1e5).astype(np.int64)
        _, group = np.unique(keys, axis=0, return_inverse=True)
        group = np.asarray(group).ravel()
        weight = np.bincount(group, weights=self.areas)
        out = []
        for g in np.argsort(-weight)[:_MAX_AXES]:
            members = group == g
            axis = (n[members] * self.areas[members, None]).sum(axis=0)
            length = np.linalg.norm(axis)
            if length > 0:
                out.append(axis / length)
        return out

    def volume(self) -> float:
        p0 = self.points[self.tris[:, 0]]
        return float(abs(np.einsum("ij,ij->i", p0, self.cross).sum() / 6))

    def area(self) -> float:
        return float(self.areas.sum())


# --- boundaries of a set of triangles ---------------------------------------

def _boundary_loops(tris: np.ndarray, n_points: int) -> list | None:
    """The closed loops of point indices bounding these triangles, each
    running the way the triangles do. None where the boundary touches
    itself at a point, which has no single way round."""
    start = tris.ravel()
    end = tris[:, [1, 2, 0]].ravel()
    directed = start * n_points + end
    reverse = end * n_points + start
    outer = ~np.isin(reverse, directed)
    starts, ends = start[outer], end[outer]
    if len(np.unique(starts)) != len(starts):
        return None
    following = dict(zip(starts.tolist(), ends.tolist()))
    loops = []
    while following:
        first, at = next(iter(following.items()))
        loop = [first]
        del following[first]
        while at != first:
            if at not in following:
                return None
            loop.append(at)
            at = following.pop(at)
        loops.append(loop)
    return loops


# --- pass 1: a straight extrusion -------------------------------------------

def _extrusion(m: _Prepared, axis: np.ndarray, tolerance: float):
    heights = m.points @ axis
    low, high = float(heights.min()), float(heights.max())
    if high - low <= tolerance:
        return None
    at = heights[m.tris]
    bottom = np.all(np.abs(at - low) <= tolerance, axis=1)
    top = np.all(np.abs(at - high) <= tolerance, axis=1)
    if not bottom.any() or not top.any():
        return None
    # A wall stands square to the caps: seen along the axis it has no area.
    # Measured as a width rather than an angle, because the narrow triangles
    # walls are made of turn float32 rounding into large angular errors.
    walls = ~(bottom | top)
    if walls.any():
        p = m.points[m.tris[walls]]
        span = np.linalg.norm(p - np.roll(p, 1, axis=1), axis=2).max(axis=1)
        flat = np.abs(m.cross[walls] @ axis)
        if np.any(flat > 2 * tolerance * np.maximum(span, tolerance)):
            return None
    loops = _boundary_loops(m.tris[bottom], len(m.points))
    if not loops:
        return None
    frame = _Frame(axis, low)
    outlines = [frame.flatten(m.points[loop]) for loop in loops]
    profile = _nest(outlines)
    if profile is None:
        return None
    fitted = {i: _fit_loop(outlines[i], tolerance) for i in range(len(loops))}
    shape = _build_extrusion(frame, profile, fitted, high - low)
    if shape is None:
        return None
    sag = max(seg.sag for segs in fitted.values() for seg in segs)
    return _checked(shape, m, max(tolerance, sag))


class _Frame:
    """2D coordinates on the bottom cap's plane, and back to 3D."""

    def __init__(self, axis, height):
        self.axis = np.asarray(axis, float)
        helper = np.eye(3)[int(np.argmin(np.abs(self.axis)))]
        self.u = np.cross(self.axis, helper)
        self.u /= np.linalg.norm(self.u)
        self.v = np.cross(self.axis, self.u)
        self.origin = self.axis * height

    def flatten(self, pts):
        return np.column_stack((pts @ self.u, pts @ self.v))

    def lift(self, uv):
        return self.origin + uv[0] * self.u + uv[1] * self.v


def _signed_area(pts) -> float:
    x, y = pts[:, 0], pts[:, 1]
    return float((x * np.roll(y, -1) - np.roll(x, -1) * y).sum() / 2)


def _inside(point, poly) -> bool:
    """Even-odd test of a 2D point against a closed polygon."""
    x, y = point
    x0, y0 = poly[:, 0], poly[:, 1]
    x1, y1 = np.roll(x0, -1), np.roll(y0, -1)
    crosses = (y0 > y) != (y1 > y)
    with np.errstate(divide="ignore", invalid="ignore"):
        at = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
    return bool(np.count_nonzero(crosses & (x < at)) % 2)


def _nest(outlines):
    """[(outer, [holes])] by how deep each loop sits inside the others: an
    outline inside an even number of others is material, inside an odd
    number a hole in the smallest one around it."""
    areas = [abs(_signed_area(o)) for o in outlines]
    if min(areas) <= 0:
        return None
    around = [[j for j in range(len(outlines))
               if j != i and areas[j] > areas[i]
               and _inside(outlines[i][0], outlines[j])]
              for i in range(len(outlines))]
    profile = {}
    for i, containers in enumerate(around):
        if len(containers) % 2 == 0:
            profile.setdefault(i, [])
    for i, containers in enumerate(around):
        if len(containers) % 2 == 1:
            parent = min(containers, key=areas.__getitem__)
            if parent not in profile:
                return None
            profile[parent].append(i)
    return list(profile.items())


# --- fitting an outline with lines, arcs and circles -------------------------

@dataclass
class _Seg:
    kind: str               # "line", "arc" or "circle"
    points: tuple           # line: (a, b); arc: (a, mid, b); circle: (centre,)
    radius: float = 0.0
    sag: float = 0.0        # how far the mesh's chords sit inside the curve


def _fit_circle(pts):
    """Least-squares circle through 2D points: (centre, radius, worst miss)."""
    mean = pts.mean(axis=0)
    q = pts - mean
    a = np.column_stack((2 * q, np.ones(len(q))))
    b = (q ** 2).sum(axis=1)
    (cx, cy, c), *_ = np.linalg.lstsq(a, b, rcond=None)
    r = math.sqrt(max(c + cx * cx + cy * cy, 0.0))
    miss = float(np.abs(np.hypot(q[:, 0] - cx, q[:, 1] - cy) - r).max())
    return mean + (cx, cy), r, miss


def _sagitta(radius, chord) -> float:
    half = min(chord / (2 * radius), 1.0)
    return radius * (1 - math.cos(math.asin(half)))


def _drop_collinear(pts, tolerance):
    """The loop without points that lie on the line between their
    neighbours: a box's side cut into strips is still one side.

    Every pass drops the first point of each run of such points, never two
    neighbours at once, since dropping both would judge each against a
    neighbour that is no longer there."""
    while len(pts) > 3:
        a, c = np.roll(pts, 1, axis=0), np.roll(pts, -1, axis=0)
        ac = c - a
        length = np.hypot(ac[:, 0], ac[:, 1])
        ab = pts - a
        with np.errstate(divide="ignore", invalid="ignore"):
            off = np.abs(ac[:, 0] * ab[:, 1] - ac[:, 1] * ab[:, 0]) / length
            along = (ab * ac).sum(axis=1) / length
        on_line = (length > 0) & (off <= tolerance) & (along > 0) \
            & (along < length)
        drop = on_line & ~np.roll(on_line, 1)
        if not drop.any() or len(pts) - drop.sum() < 3:
            break
        pts = pts[~drop]
    return pts


def _fit_loop(pts, tolerance):
    """The segments a closed 2D outline is made of."""
    if len(pts) >= _MIN_CIRCLE_POINTS:
        centre, r, miss = _fit_circle(pts)
        extent = float(np.ptp(pts, axis=0).max())
        if miss <= tolerance and r < extent:
            chord = float(np.linalg.norm(pts - np.roll(pts, 1, axis=0),
                                         axis=1).max())
            return [_Seg("circle", (centre,), r, _sagitta(r, chord))]
    pts = _drop_collinear(pts, tolerance * 0.1)
    n = len(pts)
    before = pts - np.roll(pts, 1, axis=0)
    after = np.roll(pts, -1, axis=0) - pts
    lb, la = np.linalg.norm(before, axis=1), np.linalg.norm(after, axis=1)
    turn = np.degrees(np.arctan2(before[:, 0] * after[:, 1]
                                 - before[:, 1] * after[:, 0],
                                 (before * after).sum(axis=1)))
    ratio = np.maximum(lb, la) / np.maximum(np.minimum(lb, la), 1e-300)
    smooth = (np.abs(turn) < _SMOOTH_TURN_DEG) & (ratio < _SIMILAR_CHORDS)
    if smooth.all() or not smooth.any():
        return [_Seg("line", (pts[i], pts[(i + 1) % n])) for i in range(n)]
    # start at a corner so no run of smooth points wraps past the end
    first = int(np.flatnonzero(~smooth)[0])
    order = [(first + k) % n for k in range(n)] + [first]
    segs = []
    k = 0
    while k < n:
        i = order[k]
        run_end = k + 1
        sign = np.sign(turn[order[run_end]]) if run_end < n else 0
        while (run_end < n and smooth[order[run_end]]
               and np.sign(turn[order[run_end]]) == sign):
            run_end += 1
        # order[k] is a corner or a tangent point; order[k+1 .. run_end-1]
        # are smooth and order[run_end] ends the run
        if run_end - k >= 3:
            idx = order[k:run_end + 1]
            centre, r, miss = _fit_circle(pts[idx])
            if miss <= tolerance:
                chord = float(np.linalg.norm(np.diff(pts[idx], axis=0),
                                             axis=1).max())
                mid = pts[idx[len(idx) // 2]]
                segs.append(_Seg("arc", (pts[idx[0]], mid, pts[idx[-1]]), r,
                                 _sagitta(r, chord)))
                k = run_end
                continue
        segs.append(_Seg("line", (pts[i], pts[order[k + 1]])))
        k += 1
    return segs


# --- building the solid -----------------------------------------------------

def _pnt(p):
    return occ.gp_Pnt(float(p[0]), float(p[1]), float(p[2]))


def _wire(frame: _Frame, segs):
    mk = occ.BRepBuilderAPI_MakeWire()
    for seg in segs:
        if seg.kind == "circle":
            centre = frame.lift(seg.points[0])
            ax = occ.gp_Ax2(_pnt(centre), occ.gp_Dir(*map(float, frame.axis)))
            edge = occ.BRepBuilderAPI_MakeEdge(
                occ.gp_Circ(ax, float(seg.radius))).Edge()
        elif seg.kind == "arc":
            a, mid, b = (frame.lift(p) for p in seg.points)
            arc = occ.GC_MakeArcOfCircle(_pnt(a), _pnt(mid), _pnt(b))
            if not arc.IsDone():
                return None
            edge = occ.BRepBuilderAPI_MakeEdge(arc.Value()).Edge()
        else:
            a, b = (frame.lift(p) for p in seg.points)
            edge = occ.BRepBuilderAPI_MakeEdge(_pnt(a), _pnt(b)).Edge()
        mk.Add(edge)
        if not mk.IsDone():
            return None
    return mk.Wire()


def _prism(frame, plane, segs, height):
    """One outline pushed up the axis into a solid."""
    from OCP.BRepLib import BRepLib
    wire = _wire(frame, segs)
    if wire is None:
        return None
    mk = occ.BRepBuilderAPI_MakeFace(plane, wire, True)
    if not mk.IsDone():
        return None
    d = frame.axis * height
    prism = occ.BRepPrimAPI_MakePrism(
        mk.Face(), occ.gp_Vec(float(d[0]), float(d[1]), float(d[2])))
    if not prism.IsDone():
        return None
    solid = occ.to_solid(prism.Shape())
    BRepLib.OrientClosedSolid_s(solid)    # outward, whichever way it ran
    return solid


def _build_extrusion(frame, profile, fitted, height):
    """Each outline extruded, its holes extruded and cut away.

    Cutting rather than adding the holes to the cap face spares asking
    which way round each loop runs: a hole wire running the same way as
    its outline makes a face OpenCASCADE calls invalid, and a full circle
    has no direction of its own to go by."""
    from serpentine3d.core.geometry import GeometryError, boolean_difference
    plane = occ.gp_Pln(occ.gp_Ax3(_pnt(frame.origin),
                                  occ.gp_Dir(*map(float, frame.axis)),
                                  occ.gp_Dir(*map(float, frame.u))))
    solids = []
    for outer, holes in profile:
        solid = _prism(frame, plane, fitted[outer], height)
        if solid is None:
            return None
        for hole in holes:
            cutter = _prism(frame, plane, fitted[hole], height)
            if cutter is None:
                return None
            try:
                solid = boolean_difference(solid, cutter)
            except GeometryError:
                return None
        solids.append(solid)
    if len(solids) == 1:
        return solids[0]
    compound = occ.TopoDS_Compound()
    builder = occ.BRep_Builder()
    builder.MakeCompound(compound)
    for s in solids:
        builder.Add(compound, s)
    return compound


# --- pass 2: flat regions ---------------------------------------------------

def _flat_regions(m: _Prepared, tolerance: float):
    """Each run of coplanar neighbours as one face, the rest as triangles."""
    region = _coplanar_groups(m, tolerance)
    _worth_rebuilding(m, region)
    faces = []
    loose = []
    for label in np.unique(region):
        members = np.flatnonzero(region == label)
        face = _region_face(m, members, tolerance) if len(members) > 1 \
            else None
        if face is None:
            loose.extend(members.tolist())
        else:
            faces.append(face)
    if not faces:
        raise RecogniseError("no flat regions or extrusion were found")
    for t in loose:
        faces.append(_triangle_face(m.points[m.tris[t]]))
    shape = _sew_solid(faces, tolerance)
    from serpentine3d.core.geometry import merge_coplanar_faces
    try:
        tidy = merge_coplanar_faces(shape)
        if tidy.ShapeType() == occ.SOLID:
            shape = tidy
    except Exception:                                   # noqa: BLE001
        pass                                            # keep it untidied
    checked = _checked(shape, m, tolerance)
    if checked is None:
        raise RecogniseError("the rebuilt solid does not match the mesh")
    return checked


def _worth_rebuilding(m: _Prepared, region: np.ndarray):
    """Refuse, before any kernel work, a part that is mostly curved.

    A curved surface is meshed in strips of flat four-sided patches, two
    triangles each, which merge into faces that help nobody edit it: a
    rendering model of a glass would come back as a hundred thousand faces
    after minutes of sewing. Size alone cannot tell such a patch from a
    box's side, which is two triangles too. Its edges can: a real face
    meets a neighbour at a fold somewhere, while a patch on a curve meets
    every neighbour almost flat. A group is a face when it is large or
    has a fold on its border, and faces have to make up most of the part."""
    labels, group_of, sizes = np.unique(region, return_inverse=True,
                                        return_counts=True)
    group_of = np.asarray(group_of).ravel()
    a, b = m.pairs[:, 0], m.pairs[:, 1]
    border = group_of[a] != group_of[b]
    fold = border & (np.einsum("ij,ij->i", m.normals[a], m.normals[b])
                     < math.cos(math.radians(_FOLD_DEG)))
    is_face = sizes >= _FLAT_GROUP
    is_face[group_of[a[fold]]] = True
    is_face[group_of[b[fold]]] = True
    loose = int(sizes[~is_face].sum())
    faces = int(is_face.sum()) + loose
    if loose > len(region) * _MOST_CURVED or faces > _MAX_FACES:
        raise RecogniseError("too little of it is flat to be worth "
                             "rebuilding")


def _coplanar_groups(m: _Prepared, tolerance: float) -> np.ndarray:
    """A label per triangle; neighbours on one plane share it."""
    a, b = m.pairs[:, 0], m.pairs[:, 1]
    same_way = np.einsum("ij,ij->i", m.normals[a], m.normals[b]) \
        > math.cos(math.radians(_COPLANAR_DEG))
    # same plane, not just parallel: b's corners on a's plane
    offset = np.abs(np.einsum(
        "ij,ij->i", m.normals[a],
        m.points[m.tris[b, 0]] - m.points[m.tris[a, 0]]))
    join = same_way & (offset <= tolerance)
    parent = np.arange(len(m.tris))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in zip(a[join].tolist(), b[join].tolist()):
        ri, rj = root(i), root(j)
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)
    return np.array([root(i) for i in range(len(parent))])


def _region_face(m: _Prepared, members, tolerance):
    """One flat face for a group of triangles, or None if they are not
    flat after all or their outline cannot be followed."""
    tris = m.tris[members]
    used = np.unique(tris)
    pts = m.points[used]
    centre = pts.mean(axis=0)
    _, _, vt = np.linalg.svd(pts - centre, full_matrices=False)
    normal = vt[-1]
    if np.abs((pts - centre) @ normal).max() > tolerance:
        return None             # drifted round a gentle curve: not a plane
    if np.dot(normal, m.normals[members].sum(axis=0)) < 0:
        normal = -normal
    loops = _boundary_loops(tris, len(m.points))
    if not loops:
        return None
    from OCP.ShapeFix import ShapeFix_Face
    helper = np.eye(3)[int(np.argmin(np.abs(normal)))]
    u = np.cross(normal, helper)
    plane = occ.gp_Pln(occ.gp_Ax3(_pnt(centre),
                                  occ.gp_Dir(*map(float, normal)),
                                  occ.gp_Dir(*map(float, u))))
    flat = [np.column_stack(((m.points[lp] - centre) @ u,
                             (m.points[lp] - centre) @ np.cross(normal, u)))
            for lp in loops]
    outer = int(np.argmax([abs(_signed_area(f)) for f in flat]))
    wires = []
    for lp in loops:
        poly = occ.BRepBuilderAPI_MakePolygon()
        for i in lp:
            poly.Add(_pnt(m.points[i]))
        poly.Close()
        if not poly.IsDone():
            return None
        wires.append(poly.Wire())
    mk = occ.BRepBuilderAPI_MakeFace(plane, wires[outer], True)
    for i, w in enumerate(wires):
        if i != outer:
            mk.Add(w)
    if not mk.IsDone():
        return None
    fix = ShapeFix_Face(mk.Face())
    fix.Perform()
    return fix.Face()


def _triangle_face(corners):
    poly = occ.BRepBuilderAPI_MakePolygon(*(_pnt(p) for p in corners), True)
    return occ.BRepBuilderAPI_MakeFace(poly.Wire(), True).Face()


def _sew_solid(faces, tolerance):
    from OCP.BRepCheck import BRepCheck_Shell, BRepCheck_Status
    from OCP.BRepLib import BRepLib
    sew = occ.BRepBuilderAPI_Sewing(tolerance)
    for f in faces:
        sew.Add(f)
    sew.Perform()
    sewn = sew.SewedShape()
    if sewn is None or sewn.IsNull() or sewn.ShapeType() != occ.SHELL:
        raise RecogniseError("the faces did not sew into one closed shell")
    shell = occ.to_shell(sewn)
    if BRepCheck_Shell(shell).Closed() != BRepCheck_Status.BRepCheck_NoError:
        raise RecogniseError("the sewn shell is not closed")
    mk = occ.BRepBuilderAPI_MakeSolid(shell)
    if not mk.IsDone():
        raise RecogniseError("the shell would not close into a solid")
    solid = mk.Solid()
    BRepLib.OrientClosedSolid_s(solid)
    return solid


# --- the check --------------------------------------------------------------

def _checked(shape, m: _Prepared, deviation: float):
    """The shape if it is a valid solid of the mesh's volume, else None.

    A rebuilt hole is a true circle where the mesh had a polygon inside it,
    so the volumes differ by up to the chords' sag over the surface; more
    than that, and something was fitted wrongly."""
    from serpentine3d.core.geometry import is_valid, volume
    try:
        if not is_valid(shape):
            return None
        solid_volume = abs(volume(shape))
    except Exception:                                   # noqa: BLE001
        return None
    allowed = 2 * deviation * m.area() + 1e-9 * max(m.volume(), 1.0)
    if abs(solid_volume - m.volume()) > allowed:
        return None
    return shape


def _face_count(shape) -> int:
    n = 0
    exp = occ.TopExp_Explorer(shape, occ.FACE)
    while exp.More():
        n += 1
        exp.Next()
    return n


def serpentine3d_plugin(ctx):
    base = ctx.requests()

    @ctx.command("meshtosolid")
    def cmd_meshtosolid(c):
        """Convert closed meshes into solids with their flat faces and holes
        (prototype of meshtobrep from #184)."""
        objs = yield base.SelectReq("Select meshes to convert",
                                    kinds=("mesh",))
        solids = meshes = 0
        for o in objs:
            results = convert_pieces(o.shape, o.name, c.echo)
            if len(results) == 1:
                c.scene.replace_shape(o.id, results[0][1])
            else:
                with c.scene.batched():
                    for name, shape in results:
                        c.scene.add(shape, name=name, layer_id=o.layer_id)
                    c.scene.remove(o.id)
            for _name, shape in results:
                if isinstance(shape, MeshShape):
                    meshes += 1
                else:
                    solids += 1
        c.echo(f"{solids} solid(s) made"
               + (f", {meshes} part(s) left as meshes." if meshes else "."))

    @ctx.command("splitdisjointmesh")
    def cmd_splitdisjointmesh(c):
        """Split meshes into their separate pieces, one object each."""
        objs = yield base.SelectReq("Select meshes to split", kinds=("mesh",))
        for o in objs:
            pieces = split_pieces(o.shape)
            if len(pieces) == 1:
                c.echo(f"{o.name} is already one piece.")
                continue
            with c.scene.batched():
                for k, piece in enumerate(pieces, 1):
                    c.scene.add(piece, name=f"{o.name} {k}",
                                layer_id=o.layer_id)
                c.scene.remove(o.id)
            c.echo(f"{o.name}: split into {len(pieces)} pieces.")
