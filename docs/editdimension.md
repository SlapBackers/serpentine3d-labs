# editdimension: retype sizes, fillets, chamfers and holes

[← Serpentine3D Labs](../README.md)

A [Serpentine3D](https://github.com/chisomobanzi/Serpentine3D) plugin that
lets you change the numbers a solid was made with after the fact: a box's
sizes, fillets, chamfers and holes, or a cylinder's diameter and height. Pick
an edge or face and type the new number.

**This is a preview of a proposed change to Serpentine3D**
([discussion #182](https://github.com/chisomobanzi/Serpentine3D/discussions/182)).
It adds one command to the official app and changes nothing else.

## What it does

1. Draw a box, 40 x 30 x 20.
2. Fillet some edges at 3 with `filletedge` or the gumball.
3. The box is too small: Ctrl+Shift-click one of its edges and type
   `editdimension`. It asks for the point that stays put (press Enter for the
   side it offers), then shows 40. Type 50. The box grows, and the fillets
   stay 3 on the same edges.
4. The fillets now look too small: Ctrl+Shift-click a fillet, run
   `editdimension`, type 5.

What you pick decides what you edit:

| You pick | It shows | Typing a new number |
|---|---|---|
| A box's straight edge | The box's length along that edge | Changes it, holding the point you chose (below). |
| A box's flat side | The distance to the side across | Changes it; Enter keeps the side across in place, so the picked side moves. |
| A fillet (its face or its curved edge) | Its radius | Changes that fillet. `0` removes it. |
| A chamfer's face | Its distance | Changes that chamfer. `0` removes it. |
| A hole's wall or rim | Its diameter | Changes the hole. `0` fills it. |
| A blind hole's floor | Its depth | Changes how deep it goes from the face it was drilled in. |
| A cylinder's round side or edge | Its diameter | Changes it; the axis stays put. |
| A cylinder's end or straight edge | Its height | Changes it, holding the point you chose. |

Holes stay where they are when a box changes size, and a blind hole moves
with the face it was drilled in, keeping its depth.

**What stays put** is asked every time a length changes, before the number:

- **Click a point**, snapping to a corner, an edge or anything else: the
  solid changes length about it, so that point stays exactly where it is.
- **Choose a side**: `Bottom`, `Middle` or `Top` along Z (`Left`/`Right`
  along X, `Front`/`Back` along Y, `Start`/`End` on a solid turned off the
  world axes).
- **Press Enter** for the side offered: the side across from a picked face;
  otherwise the side standing on the construction plane, so a box drawn on
  Z=0 and made taller grows upwards, never through the plane; otherwise the
  low side.

Nothing is stored on the object. The sizes and fillets are read back from the
shape each time, and the box is only rebuilt if that reading reproduces it
exactly. So it works on any box with filleted edges, however it was drawn,
moved, turned or imported, and a file saved with it opens anywhere.

## Install

See [Install a plugin](../README.md#install-a-plugin); the file is
[`plugins/editdimension.py`](../plugins/editdimension.py).

## Limits

- Boxes (with fillets, equal-distance chamfers and holes square to a side)
  and plain cylinders, for now. Anything else is left alone with a message.
- A hole's position can't be retyped yet, only its diameter and depth.
- The number is typed at the command line. Showing it beside the edge in the
  viewport needs a change to Serpentine3D itself.

## Feedback

On [discussion #182](https://github.com/chisomobanzi/Serpentine3D/discussions/182).

## Where the code lives

On the
[`editable-dimensions` branch](https://github.com/SlapBackers/Serpentine3D/tree/editable-dimensions)
as `serpentine3d/core/box_dimensions.py` and the `editdimension` command; this
plugin is built from it.
