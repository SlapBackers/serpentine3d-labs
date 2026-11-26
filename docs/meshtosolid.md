# meshtosolid: STL recognition

[← Serpentine3D Labs](../README.md)

A [Serpentine3D](https://github.com/chisomobanzi/Serpentine3D) plugin that turns an imported STL into a solid you can actually edit: flat faces come
back as single faces, and holes in plates and brackets come back as true
cylinders.

**This is a prototype for a proposed change to Serpentine3D itself**
([issue #184](https://github.com/chisomobanzi/Serpentine3D/issues/184)). It
isn't a separate version of the app. It adds one command to the official app
and changes nothing else. If the change is accepted upstream, this plugin
goes away.

## What it does

Today `meshtobrep` makes one flat face per triangle, so a 50,000-triangle
bracket becomes a 50,000-face shell that won't boolean or fillet.
`meshtosolid`:

1. **Straight extrusions** (plates, brackets, spacers): finds the direction the
   part was pushed along, fits the outline with lines, arcs and circles, and
   extrudes it. Holes and slots become true cylinders.
2. **Other parts**: merges coplanar triangles into single flat faces. Curved
   areas stay as triangles.
3. **Checks the result** against the mesh (valid, closed, same volume). If it
   doesn't match, the mesh is left as it is, and the command says why.

**Parts, not pieces.** An STL keeps no parts, only triangles, and a real file
has far more pieces than parts: one product model of 733,000 triangles had
1,916 pieces but 434 closed parts, the rest being open surfaces and fragments
left by the export. `meshparts` makes each closed piece a part and puts every
other piece in the smallest part around it; what belongs nowhere stays
together as one loose mesh. It asks for the smallest part to keep separate
(Enter keeps every one). `meshtosolid` works the same way, part by part.
`splitdisjointmesh` (Rhino's name) still splits into every single piece.

**Snapping to the mesh.** With the plugin loaded, an imported mesh's corners
snap as end points and the centres of its holes and round bosses as centre
points. Every command uses them: draw from a corner, put a construction plane
through three corners, centre a circle on a hole.

**Curved parts stay meshes.** A part that is mostly curved (a glass, a
sculpture, a scan) has nothing worth rebuilding as faces, so it is left as a
light mesh instead of being turned into tens of thousands of faces. A
1,000,000-triangle test assembly splits into its parts in about 2 seconds
and converts in about 4.5.

The command line reports what happened, for example
`Plate: 36,412 triangles became 8 faces (a straight extrusion).`

## Install

1. Install Serpentine3D 0.13.1 or later from its
   [releases page](https://github.com/chisomobanzi/Serpentine3D/releases/latest).
2. Download [`plugins/meshtosolid.py`](../plugins/meshtosolid.py) (on GitHub:
   open the file, then the download button).
3. Put it in the plugins folder, creating the folders if needed:
   - macOS and Linux: `~/.serpentine3d/plugins/` (in the macOS Finder,
     Cmd+Shift+G and paste the path)
   - Windows: `C:\Users\<you>\.serpentine3d\plugins\`
4. Restart Serpentine3D. Type `plugins` to check that `meshtosolid` is listed.

## Use

Import an STL, select it and type `meshparts` to get its parts as separate
meshes, or `meshtosolid` to convert the parts that can be into solids at the
same time. Snapping to corners and hole centres works as soon as the plugin
is loaded.

To remove the plugin, delete `meshtosolid.py` from the plugins folder.

## Limits

- Only closed parts are converted to solids; a part with open surfaces stays
  a mesh (it still splits out and snaps).
- Holes are rebuilt as true cylinders only on straight-extrusion parts. On
  other parts, flat faces merge but hole walls stay as triangles.
- Spheres, cones and fillet rounds are not recognised yet; a part made mostly
  of them stays a mesh.

## Feedback

Comments on what worked and what didn't, ideally with the STL, are most useful
on [issue #184](https://github.com/chisomobanzi/Serpentine3D/issues/184), where
the change is being discussed with the Serpentine3D maintainer.

## Credits

The straight-extrusion test and the final check follow the approach of
SolidCraft's Convert Mesh
([tangency-labs/solidcraft](https://github.com/tangency-labs/solidcraft),
Apache-2.0), written afresh in Python.

The code lives on the
[`stl-recognise-shapes` branch](https://github.com/SlapBackers/Serpentine3D/tree/stl-recognise-shapes)
as a change to `meshtobrep`, and this plugin is built from it.
