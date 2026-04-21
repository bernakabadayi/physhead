import bpy

source_obj_path = 'asset/frame_00000_1999_rgb_init_all.obj'

bpy.ops.import_scene.obj(filepath=source_obj_path)


imported_objs = bpy.context.selected_objects
src_obj = next((o for o in imported_objs if o.type == 'MESH'), None)

if src_obj is None:
    raise RuntimeError("No mesh found in OBJ")

print("Source:", src_obj.name)
print("UV layers:", [uv.name for uv in src_obj.data.uv_layers])

# tgt_obj = bpy.data.objects["mesh_0000"]
# double check the name of the imported object
tgt_obj = bpy.data.objects["00000"]

if not src_obj.data.uv_layers:
    print("ERROR: Source mesh has no UV map!")
else:
    src_uv = src_obj.data.uv_layers[0]

    tgt_uv = tgt_obj.data.uv_layers.get(src_uv.name)
    if tgt_uv is None:
        tgt_uv = tgt_obj.data.uv_layers.new(name=src_uv.name)

    for src_loop, tgt_loop in zip(src_uv.data, tgt_uv.data):
        tgt_loop.uv = src_loop.uv.copy()

    print("UVs successfully copied!")


if tgt_obj is not None:
    tgt_obj.rotation_euler[0] += 1.5708  # 90 degrees in radians
    print("Target object rotated by 90 degrees around X-axis --needed for Maya")

# Delete imported source object
bpy.data.objects.remove(src_obj, do_unlink=True)

# Optional: remove orphan mesh data (cleanup)
for mesh in bpy.data.meshes:
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

print("Source object deleted from the scene.")