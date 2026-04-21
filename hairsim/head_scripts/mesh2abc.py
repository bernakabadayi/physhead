
import bpy
import numpy as np
import sys
import argparse

# Parse custom arguments passed after '--' in the Blender command line
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument("--meshes_npy", required=True, help="Path to meshes .npy file")
parser.add_argument("--mesh_ply", required=True, help="Path to the reference .ply mesh file")
parser.add_argument("--fps", type=int, default=30, help="Frames per second")
parser.add_argument("--output_blend", required=True, help="Path to output .blend file")
args = parser.parse_args(argv)

# Delete default objects (camera, lights, and any other objects)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Also delete orphaned data
for block in bpy.data.meshes:
    if block.users == 0:
        bpy.data.meshes.remove(block)

for block in bpy.data.materials:
    if block.users == 0:
        bpy.data.materials.remove(block)

for block in bpy.data.cameras:
    bpy.data.cameras.remove(block)

for block in bpy.data.lights:
    bpy.data.lights.remove(block)

vertices_data = np.load(args.meshes_npy)  #  [n, 5023, 3]
print('Vertices data shape:', vertices_data.shape)

num_frames, num_vertices, _ = vertices_data.shape
# num_frames= 60

# Function to update mesh vertices and set keyframes every 5 frames
def set_keyframes(mesh_obj, vertices_data, keyframe_interval=5):
    
#    if not mesh_obj.data.shape_keys:
#        # Add a basis shape key if there are none
#        mesh_obj.shape_key_add(name="Basis", from_mix=False)
#    
    for frame in range(0, num_frames, keyframe_interval):
        vertices = vertices_data[frame]
        
        # Update each vertex's position
        mesh = mesh_obj.data
        for i, vertex in enumerate(mesh.vertices):
            vertex.co = vertices[i]
            vertex.keyframe_insert(data_path="co", frame=frame+1)
        
        # Insert keyframe for vertex positions
        mesh_obj.data.update()
        #mesh_obj.keyframe_insert(data_path="data.vertices", frame=frame + 1)
        #mesh_obj.data.shape_keys.key_blocks[0].keyframe_insert(data_path="value", frame=frame + 1)
 

# Load the first mesh into the scene
file_p = args.mesh_ply
bpy.ops.import_mesh.ply(filepath=file_p)  # Load the first mesh

mesh_obj = bpy.context.scene.objects['00000']

# Set keyframes for vertex positions every 5 frames
set_keyframes(mesh_obj, vertices_data, keyframe_interval=1)


scene = bpy.context.scene
scene.render.fps = args.fps
scene.frame_start = 1
scene.frame_end = num_frames  
bpy.context.scene.frame_set(1)

import sys
# Save the blend file
output_path = None
for i, arg in enumerate(argv):
    if arg == "--output_blend":
        output_path = argv[i+1]

if output_path:
    bpy.ops.wm.save_as_mainfile(filepath=output_path)