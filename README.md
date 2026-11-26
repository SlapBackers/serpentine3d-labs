# Serpentine3D Labs

Try proposed [Serpentine3D](https://github.com/chisomobanzi/Serpentine3D)
features today, in the official app, as plugins.

Each plugin here is a preview of a change proposed to Serpentine3D itself.
None of them is a separate version of the app: a plugin adds commands to the
official Serpentine3D and changes nothing else, and it is retired once its
change is merged upstream.

## Plugins

| Plugin | Version | What it adds | Proposal |
|---|---|---|---|
| [meshtosolid](docs/meshtosolid.md) | 0.3.0 | Split an STL into its real parts, snap to its corners and hole centres, and turn parts into editable solids with real flat faces and holes | [#184](https://github.com/chisomobanzi/Serpentine3D/issues/184) |
| [editdimension](docs/editdimension.md) | 0.3.0 | Pick an edge or face and retype a box's sizes, fillets, chamfers and holes, or a cylinder's diameter and height, holding the point you choose | [#182](https://github.com/chisomobanzi/Serpentine3D/discussions/182) |

What changed in each version: [CHANGELOG.md](CHANGELOG.md). Every version is
also a [release](https://github.com/SlapBackers/serpentine3d-labs/releases)
with its file attached, to download it or go back to an earlier one. A
plugin's version is in the first line of its file.

## Install a plugin

1. Install Serpentine3D 0.13.1 or later from its
   [releases page](https://github.com/chisomobanzi/Serpentine3D/releases/latest).
2. Download the plugin's file from the [`plugins`](plugins) folder (open the
   file on GitHub, then the download button).
3. Put it in the plugins folder, creating the folders if needed:
   - macOS and Linux: `~/.serpentine3d/plugins/` (in the macOS Finder,
     Cmd+Shift+G and paste the path)
   - Windows: `C:\Users\<you>\.serpentine3d\plugins\`
4. Restart Serpentine3D: it looks for plugins when it starts. Type `plugins`
   to see what is loaded.

To remove a plugin, delete its file and restart.

## Feedback

Each plugin's proposal is where feedback is most useful: what worked, what
didn't, and the file that showed it. That is where the Serpentine3D
maintainer decides whether and how the change goes in.

## How it works

1. An idea is proposed on Serpentine3D first, as an issue or a discussion.
2. Its code is written on a branch of
   [SlapBackers/Serpentine3D](https://github.com/SlapBackers/Serpentine3D), in
   the shape Serpentine3D wants and with its tests, ready to become the pull
   request.
3. The plugin is built from that branch by [`tools/build.py`](tools/build.py),
   so the plugin and the pull request are the same code. Files in `plugins/`
   are never edited by hand.
4. Every change is tested here against the latest Serpentine3D release and its
   current `main`, and the build checks that each plugin still matches its
   branch and that its version has a changelog entry.
5. A new version gets an entry in [CHANGELOG.md](CHANGELOG.md), then
   `python tools/release.py <plugin>` tags it and publishes the release.
6. When the maintainer accepts the change, the branch becomes the pull
   request and the plugin is retired.

Some parts of an idea can only live in Serpentine3D itself (a change to an
existing panel, or to the file format). A plugin then previews the rest, and
the pull request does the full integration.

## Licence

MIT, like Serpentine3D.
