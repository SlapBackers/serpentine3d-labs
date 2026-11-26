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
