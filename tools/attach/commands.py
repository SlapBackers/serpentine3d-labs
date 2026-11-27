import sys

from serpentine3d.commands.base import SelectReq
from serpentine3d.core import geometry as g


def _hook_into_the_app():
    """What the pull request changes in Serpentine3D itself, done from
    outside for this preview: a viewport draws the attachments of what is
    selected, and moving several objects at once (the move commands, the
    gumball) is one change, so an object moved together with what it
    stands on stays attached."""
    from serpentine3d.commands import transform
    from serpentine3d.ui import gumball, viewport

    if getattr(viewport.Viewport, "_labs_attach", False):
        return
    viewport.Viewport._labs_attach = True
    dots = viewport.Viewport._paint_dots

    def _paint_dots(self, w, h):
        dots(self, w, h)
        paint(self, w, h)

    viewport.Viewport._paint_dots = _paint_dots
    do = transform._do

    def _do(ctx, *args, **kwargs):
        with ctx.scene.batched():
            return do(ctx, *args, **kwargs)

    transform._do = _do
    apply = gumball.Gumball._apply

    def _apply(self, fn):
        with self.vp.scene.batched():
            return apply(self, fn)

    gumball.Gumball._apply = _apply


def serpentine3d_plugin(ctx):
    command = ctx.command
    if ctx.scene is not None:
        # links saved in an open file follow too
        window = getattr(ctx, "window", None)
        watch(ctx.scene, window.ctx.echo if window is not None else None)
        try:
            _hook_into_the_app()
        except Exception as exc:                            # noqa: BLE001
            print(f"attach: drawing links is unavailable ({exc})",
                  file=sys.stderr)

    # @extract serpentine3d/commands/organize.py::cmd_attach

    # @extract serpentine3d/commands/organize.py::cmd_unattach
