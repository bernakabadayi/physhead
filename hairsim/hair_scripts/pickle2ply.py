import pickle
import numpy as np
import trimesh
import random
import os
import argparse

parser = argparse.ArgumentParser(description="Convert pickle curve files to PLY point clouds.")
parser.add_argument(
    "--input_folder", "-i",
    default="/is/cluster/fast/vsklyarova/Projects/AVA/Ava-256-2_EXP_cheek002_2/Ava-256-2_EXP_cheek002_simulations/20230310--1106--FCT871/nod40/curves",
    help="Path to folder containing .pickle files.",
)
parser.add_argument(
    "--output_folder", "-o",
    default=None,
    help="Path to output folder for .ply files. Defaults to <input_folder>/../curves_ply.",
)
args = parser.parse_args()

input_folder = args.input_folder

if not os.path.exists(input_folder):
    raise FileNotFoundError(f"Input folder '{input_folder}' does not exist.")

output_folder = args.output_folder or input_folder.replace("curves", "curves_ply")
os.makedirs(output_folder, exist_ok=True)

# Iterate through all pickle files in the folder
for file_name in os.listdir(input_folder):
    if file_name.endswith('.pickle'):
        # Construct full paths
        pickle_path = os.path.join(input_folder, file_name)
        ply_path = os.path.join(output_folder, file_name.replace('.pickle', '.ply'))

        # Load the pickle file
        with open(pickle_path, 'rb') as fp:
            control_points = pickle.load(fp)

        # Generate the PLY data
        vertices = []
        colors = []
        for strand in control_points:
            # Generate a random color for the strand (RGB in range 0-255)
            color = [random.randint(0, 255) for _ in range(3)]
            
            for point in strand:
                vertices.append(point)
                colors.append(color)

        # Convert to numpy arrays
        vertices = np.array(vertices)
        colors = np.array(colors)

        # Create a Trimesh object and save to PLY
        ply_data = trimesh.Trimesh(vertices=vertices, process=False)
        ply_data.visual.vertex_colors = colors
        ply_data.export(ply_path)

        print(f"Processed {file_name} -> {ply_path}")

print("All pickle files have been processed.")
