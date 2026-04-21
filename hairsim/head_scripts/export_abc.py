import bpy
import argparse
import sys

# Parse arguments after '--'
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

parser = argparse.ArgumentParser()
parser.add_argument("--output_abc", type=str, default="./mesh_0000.abc", help="Output ABC file path")
parser.add_argument("--isrotate", action="store_true")
parser.add_argument("--fps", type=int, default=20, help="Frames per second")

args = parser.parse_args(argv)

print("Args", args)

scene = bpy.context.scene
scene.render.fps = args.fps

start = scene.frame_start
end = scene.frame_end

print("Frame range:", start, end)

# change the obj name if its not the same
# obj = bpy.data.objects.get("mesh_0000")
obj = bpy.data.objects.get("00000")

# rotate around x-axis by 90 degrees. this is needed for maya
if obj is not None:
    if args.isrotate:
        obj.rotation_euler[0] += 1.5708  # 90 degrees in radians

if obj is None:
    raise RuntimeError("mesh_0000 not found, mesh name might be different")

bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

bpy.ops.wm.alembic_export(
    filepath=f"{args.output_abc}",
    selected=True,
    start=start,
    end=end,
    uvs=True,
    normals=True
)

print("Alembic exported.")
