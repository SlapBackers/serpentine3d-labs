from serpentine3d.commands.base import SelectReq


def _snap_to_mesh_corners():
    """Serpentine3D asks one function for every object's snap points, and
    in the released app it gives a mesh none. Wrapping it there gives every
    command the mesh's corners and hole centres; the branch changes that
    function itself (core/snaps.py)."""
    from serpentine3d.core import snaps
    original = snaps._static_snap_points
    if getattr(original, "_labs_mesh_snaps", False):
        return

    def with_mesh_snaps(shape):
        if isinstance(shape, MeshShape):
            return mesh_snap_points(shape)
        return original(shape)

    with_mesh_snaps._labs_mesh_snaps = True
    snaps._static_snap_points = with_mesh_snaps


def serpentine3d_plugin(ctx):
    base = ctx.requests()
    command = ctx.command
    _snap_to_mesh_corners()

    # @extract serpentine3d/commands/organize.py::cmd_meshparts

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
