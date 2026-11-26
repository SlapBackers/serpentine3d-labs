# Changelog

What changed in each plugin, newest first. Each version is also a
[release](https://github.com/SlapBackers/serpentine3d-labs/releases) with its
file attached, so an earlier one can be downloaded again.

Versions are per plugin. Until a plugin's change is merged into Serpentine3D
they stay below 1.0: 0.x.0 adds or changes behaviour, 0.x.y fixes it.

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
