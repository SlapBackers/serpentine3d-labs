import sys

from serpentine3d.commands.base import OptionReq, SelectReq
from serpentine3d.core import geometry as g


def serpentine3d_plugin(ctx):
    command = ctx.command
    if ctx.scene is not None:
        watch(ctx.scene)          # links saved in an open file follow too

    # @extract serpentine3d/commands/organize.py::cmd_attach

    # @extract serpentine3d/commands/organize.py::cmd_unattach
