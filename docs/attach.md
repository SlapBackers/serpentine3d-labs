# attach: objects that follow the face they sit on

[← Serpentine3D Labs](../README.md)

A [Serpentine3D](https://github.com/chisomobanzi/Serpentine3D) plugin for
placement and anchoring. A cylinder stands on a cube; when the cube changes,
the cylinder should follow in the way you chose.

## Use

1. Ctrl+Shift-click the face the object sits on (the cube's top).
2. Type `attach`, then answer:
   - **the object** to attach (the cylinder);
   - **the point it is measured from**: snap to a corner, an edge or any
     point, or press Enter for the face's centre;
   - **how it keeps its place sideways**: `Distance` (its distance from that
     point stays the same, like a hole dimensioned from an edge) or
     `Proportion` (its share of the face stays the same, so centred stays
     centred);
   - **whether it follows a chain**: `No` (default) or `Yes` (below).

From then on, up and down it rides the face, and sideways it keeps its place
the way you chose, however the face changes: `editdimension`, the gumball, a
move of the whole cube.

`unattach` takes a link away.

## Chains

Put a ball on the cylinder and attach it to the cylinder's top. When the cube
grows, the cylinder rides up. The ball does **not**, unless its link was made
with "follow a chain" set to `Yes`: one level is the default, because links
you didn't ask for are a source of surprises.

## Good to know

- Nothing links by itself: only `attach` makes a link.
- A follower moved by hand keeps its new place; the link measures it again.
- Links are kept in the object's user text, so they are saved with the file,
  and undo and redo carry them.

## Limits

- The face must be flat and on the outside of its object, and the object a
  solid or surface (not a mesh) for now.
- If the object carrying the face is turned, its followers don't follow the
  turn yet.

## Feedback

Proposed upstream in
[Serpentine3D#186](https://github.com/chisomobanzi/Serpentine3D/discussions/186):
that is the place for what worked, what didn't, and the file that showed it.

## Where the code lives

On the
[`attach` branch](https://github.com/SlapBackers/Serpentine3D/tree/attach)
as `serpentine3d/core/attachments.py` and the `attach` and `unattach`
commands; this plugin is built from it.
