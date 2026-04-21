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
parser.add_argument("--input_abc", type=str, required=True, help="Input ABC file path to import")
parser.add_argument("--output_abc", type=str, required=True, help="Output ABC file path")
parser.add_argument("--name", type=str, required=True, help="New name for the imported mesh object")
parser.add_argument("--fps", type=int, default=30, help="Frames per second for ABC export")
parser.add_argument("--start", type=int, default=None, help="Start frame (overrides imported ABC)")
parser.add_argument("--end", type=int, default=None, help="End frame (overrides imported ABC)")
args = parser.parse_args(argv)

print("Args", args)

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Import the ABC file
bpy.ops.wm.alembic_import(filepath=args.input_abc)

print("Imported ABC:", args.input_abc)

# Find the imported mesh object and rename it
mesh_objects = [o for o in bpy.data.objects if o.type == 'MESH']
if not mesh_objects:
    raise RuntimeError("No mesh object found after ABC import")

obj = mesh_objects[0]
print(f"Renaming '{obj.name}' -> '{args.name}'")
obj.name = args.name
obj.data.name = args.name

scene = bpy.context.scene

# Set FPS
scene.render.fps = args.fps

# Override frame range if provided
if args.start is not None:
    scene.frame_start = args.start
if args.end is not None:
    scene.frame_end = args.end

start = scene.frame_start
end = scene.frame_end
print("Frame range:", start, end)

# Export as ABC with new name
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

bpy.ops.wm.alembic_export(
    filepath=args.output_abc,
    selected=True,
    start=start,
    end=end,
    uvs=True,
    normals=True
)

print("Alembic exported to:", args.output_abc)
