# Changelog

What changed in each plugin, newest first. Each version is also a
[release](https://github.com/SlapBackers/serpentine3d-labs/releases) with its
file attached, so an earlier one can be downloaded again.

Versions are per plugin. Until a plugin's change is merged into Serpentine3D
they stay below 1.0: 0.x.0 adds or changes behaviour, 0.x.y fixes it.

## attach 0.1.2

2026-11-27

- Proposed upstream as
  [Serpentine3D#186](https://github.com/chisomobanzi/Serpentine3D/discussions/186);
  the plugin's first lines now link to it. No change in behaviour.

## attach 0.1.1

2026-11-27

- `detach` is now **`unattach`** (like `ungroup` and `unlock`): typing the
  first four letters of a command runs it, and `deta` has to keep running
  `detail`.

## attach 0.1.0

2026-11-27

- First preview of placement and anchoring: `attach` links an object to the
  face it sits on, so it follows when that face moves. A cylinder on a cube
  rides the cube's top when the cube gets taller, and stays with it when the
  cube is moved.
- Across the face it keeps, as chosen when attaching, its **distance** from a
  point (a corner, an edge, any point; Enter for the centre), or its
  **proportion** of the face (centred stays centred).
- **One level by default**: a ball on the cylinder stays put when the cube
  changes, unless its own link was made to follow a chain.
- Nothing links by itself. `detach` takes a link away. A follower moved by
  hand keeps its new place. Links are saved with the file (as user text), and
  undo and redo carry them.

## meshtosolid 0.3.0

2026-11-26

- **`meshparts`: an STL splits into its parts, not every piece.** A real
  product file (733,000 triangles) had 1,916 pieces but 434 closed parts; the
  rest were open surfaces and fragments left by the export. Each closed piece
  is now a part, and every other piece joins the smallest part around it (or
  that it touches); what belongs nowhere stays together as one loose mesh. It
  asks for the smallest part to keep separate; Enter keeps every one.
- **Imported meshes snap**: corners as end points and the centres of holes
  and round bosses as centre points, so any command can build on an STL: a
  line from a corner, a plane through three corners, a circle on a hole.
- **meshtosolid works part by part**, and is fast on big files: a
  1,000,000-triangle test assembly splits into its parts in about 2 seconds
  and converts in about 4.5, with 273 of 415 parts becoming clean solids.
  Grouping is vectorised; a slow step that rescanned the whole part for every
  flat face is gone.

## editdimension 0.3.0

2026-11-26

- **The point that stays put is always asked for**, before the new length:
  click any point or snap to one, choose a side (`Bottom`, `Middle`, `Top`,
  and so on), or press Enter for the side offered. What 0.2.0 chose on its
  own is now just the Enter answer. Replaces the `Anchor=` option.
- **Chamfers**: pick a chamfer's face to retype its distance (`0` removes
  it); a box keeps its chamfers when it changes size.
- **Holes** square to a side, through or blind: pick the wall or rim to
  retype the diameter (`0` fills it), a blind hole's floor to retype its
  depth. Holes stay where they are when the box changes size, and a blind
  hole keeps its depth from the face it was drilled in.
- **Cylinders**: the round side or a round edge gives the diameter (the axis
  stays put), an end or the straight edge the height (with the same anchor
  prompt as a box).

## editdimension 0.2.0

2026-11-26

- **An anchor says what stays put** when a size changes. By default, a box
  standing on the construction plane stays on it (a box drawn on Z=0 and made
  taller grows upwards, never through the plane); otherwise the low side
  holds.
- `Anchor=Bottom`, `Middle` or `Top` (`Left`/`Right` along X, `Front`/`Back`
  along Y) chooses a side; `Anchor=Point` holds any point you pick, and the
  box scales about it.
- Replaces `Grow=Both/End/Start` from 0.1.0. A picked face still moves while
  the face across holds.

## editdimension 0.1.0

2026-11-26

- First preview of
  [#182](https://github.com/chisomobanzi/Serpentine3D/discussions/182): pick a
  box's straight edge, flat face or fillet and retype its size or radius;
  fillets keep their radius when the box changes size.
- The box and fillets are read back from the shape, so it works however the
  box was drawn, filleted, moved or imported, and nothing is stored.
- A picked edge grew the box from its centre (`Grow=End`/`Start` to hold one
  end).

## meshtosolid 0.2.0

2026-11-26

- **Separate parts.** An STL holding several pieces that don't touch is split
  first, one object per piece, each recognised on its own.
- New command `splitdisjointmesh` (Rhino's name) splits a mesh into its pieces
  without converting anything.
- **Big curved models are fast.** A mostly curved part is spotted before any
  kernel work and left as a mesh, instead of being sewn into tens of thousands
  of faces; a 204,000-triangle model in two pieces takes under two seconds.
- A mesh that can't be matched is now left as a mesh rather than converted
  triangle by triangle.

## meshtosolid 0.1.0

2026-11-26

- First preview of
  [#184](https://github.com/chisomobanzi/Serpentine3D/issues/184): straight
  extrusions rebuilt from their outline with true lines, arcs and circles, so
  holes are real cylinders; other parts have their coplanar triangles merged
  into flat faces; the result is checked against the mesh before it is used.
