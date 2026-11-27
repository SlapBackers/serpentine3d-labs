# attach: objects that follow the face they sit on

[← Serpentine3D Labs](../README.md)

A [Serpentine3D](https://github.com/chisomobanzi/Serpentine3D) plugin for
placement and anchoring. Put a cylinder on a cube's top, measured from two
of its edges: when the cube gets taller, wider, moves or turns, the
cylinder stays where you put it.

## Use

Type `attach`, then:

1. **Object to attach**: click the cylinder (or have it selected first).
2. **Face to attach it to**: click the cube's top. The cylinder doesn't have
   to be on it yet.
3. **Side that sits on it**: click the cylinder's end, or press Enter for its
   lowest side. It turns so that side lies flat on the face, and is put
   down on it.
4. **Edge to measure from**: click an edge of the face, or press Enter for
   the nearest.
5. **Distance from that edge**: type it, or press Enter to keep where it is.
6. **Second edge**, across the first: click it, or Enter for the nearest.
7. **Distance from that edge**: the same.

On the distance prompts, the **Keep** chip says what it holds when the face
changes size: `Edge` (Enter) keeps the distance from the edge, `Share` keeps
its share of the face, so centred stays centred.

## What you see

- **Select the cylinder**: the cube's face is tinted, the two edges it is
  measured from are drawn heavier, a dimension runs from each edge to it
  (the distance, or the share as a %), and a badge says what it is
  attached to. Properties shows the same under `attached to`.
- **Select the cube**: whatever is attached to it is outlined, so you see
  what will move with it.

## What follows

- **Up and down** it rides the face; **across** it keeps its distances (or
  shares) from the two edges, however the face changes: `editdimension`,
  the gumball, `move`, `scale`.
- **Turning** the cube swings it round and turns it with the cube.
- **Stacks move as stacks**: a ball attached to the cylinder follows when the
  cube grows.
- If the face gets too small for it, it keeps its place and hangs over the
  edge, and the command history says so.

## What ends a link

- **Moving it by hand**, even across the same face: the history says so.
  Run `attach` again to give it a new place. Moving it together with the
  cube (both selected) keeps the link.
- **Deleting the cube**: it stays where it is, no longer attached. Undo
  brings both back, attached.
- `unattach` takes a link away.

Links are kept in the object's user text, so they are saved with the file,
and undo and redo carry them. Links made with 0.1.x are not read: attach
those objects again.

## Limits

- The face must be flat, on a solid or surface (not a mesh).
- Turning is read from the cube's flat faces: a parent with only two flat
  faces facing each other (a cylinder) can't tell a turn about its own
  axis.

## Feedback

Proposed upstream in
[Serpentine3D#186](https://github.com/chisomobanzi/Serpentine3D/discussions/186):
that is the place for what worked, what didn't, and the file that showed it.

## Where the code lives

On the
[`attach` branch](https://github.com/SlapBackers/Serpentine3D/tree/attach):
`serpentine3d/core/attachments.py`, the drawing in
`serpentine3d/ui/attachment_marks.py`, and the `attach` and `unattach`
commands. This plugin is built from it. What the pull request changes in
Serpentine3D itself (drawing in the viewport, and moving several objects as
one change) the plugin does from outside, at startup.
