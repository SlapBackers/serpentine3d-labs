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

**Separate parts.** An STL exported from an assembly is often several pieces
that don't touch. Each piece becomes its own object and is recognised on its
own, the way Rhino lets you pick them. `splitdisjointmesh` (Rhino's name)
splits a mesh into its pieces without converting anything.

**Curved parts stay meshes.** A part that is mostly curved (a glass, a
sculpture, a scan) has nothing worth rebuilding as faces, so it is spotted in
a second or two and left as a light mesh instead of being turned into tens of
thousands of faces.

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

Import an STL, select it, type `meshtosolid` and press Enter. To pick the
pieces of a mesh apart without converting them, use `splitdisjointmesh`.

To remove the plugin, delete `meshtosolid.py` from the plugins folder.

## Limits

- The mesh must be closed (watertight).
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
