# editdimension: retype a box's sizes and fillets

[← Serpentine3D Labs](../README.md)

A [Serpentine3D](https://github.com/chisomobanzi/Serpentine3D) plugin that
lets you change a box's size or a fillet's radius after the fact, by picking
an edge and typing the new number.

**This is a preview of a proposed change to Serpentine3D**
([discussion #182](https://github.com/chisomobanzi/Serpentine3D/discussions/182)).
It adds one command to the official app and changes nothing else.

## What it does

1. Draw a box, 40 x 30 x 20.
2. Fillet some edges at 3 with `filletedge` or the gumball.
3. The box is too small: Ctrl+Shift-click one of its edges, type
   `editdimension`, and it shows 40. Type 50. The box grows, and the fillets
   stay 3 on the same edges.
4. The fillets now look too small: Ctrl+Shift-click a fillet, run
   `editdimension`, type 5.

What you pick decides what you edit:

| You pick | It shows | Typing a new number |
|---|---|---|
| A straight edge | The box's length along that edge | Changes it, holding the anchor (below). |
| A flat face | The distance to the face across | Moves the face you picked; the face across holds. |
| A fillet (its face or its curved edge) | Its radius | Changes that fillet. `0` removes it. |

**The anchor** is what stays put when a length changes:

- By default, a box standing on the construction plane stays on it: a box
  drawn on Z=0 and made taller grows upwards, never through the plane.
  Otherwise the low side holds (bottom, left, front).
- `Anchor=Bottom`, `Middle` or `Top` picks a side (`Left`/`Right` along X,
  `Front`/`Back` along Y; `Start`/`End` on a box turned off the world axes).
- `Anchor=Point` asks for a point after the number: snap to a corner or
  anywhere, and the box scales about it, so that point stays where it is.

Nothing is stored on the object. The sizes and fillets are read back from the
shape each time, and the box is only rebuilt if that reading reproduces it
exactly. So it works on any box with filleted edges, however it was drawn,
moved, turned or imported, and a file saved with it opens anywhere.

## Install

See [Install a plugin](../README.md#install-a-plugin); the file is
[`plugins/editdimension.py`](../plugins/editdimension.py).

## Limits

- Boxes and their fillets only, for now. A solid that is anything else (a
  cylinder, a box with a hole, a chamfer) is left alone with a message.
- The number is typed at the command line. Showing it beside the edge in the
  viewport needs a change to Serpentine3D itself.

## Feedback

On [discussion #182](https://github.com/chisomobanzi/Serpentine3D/discussions/182).

## Where the code lives

On the
[`editable-dimensions` branch](https://github.com/SlapBackers/Serpentine3D/tree/editable-dimensions)
as `serpentine3d/core/box_dimensions.py` and the `editdimension` command; this
plugin is built from it.
