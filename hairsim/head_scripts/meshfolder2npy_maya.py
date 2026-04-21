import os
import numpy as np
import trimesh
import argparse
# import hairsim.head_scripts.util as util

def obj2ply(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    meshes = os.listdir(input_dir)

    for filename in meshes:
        if filename.endswith('.obj'):

            obj_file_path = os.path.join(input_dir, filename)
            mesh = trimesh.load(obj_file_path, process=False)

            ply_file_name = os.path.splitext(filename)[0] + '.ply'
            ply_file_path = os.path.join(output_dir, ply_file_name)
            
            mesh.export(ply_file_path)

            print(f'Converted {filename} to {ply_file_name}')


def meshfolder2npy_maya(mesh_folder, ext='ply', write_folder=None):

    if not os.path.exists(mesh_folder):
        assert False, f"Input folder '{mesh_folder}' does not exist."

    mesh_files = sorted([f for f in os.listdir(mesh_folder) if f.endswith(f'.{ext}')])

    all_vertices = []
    for mesh_file in mesh_files:
        file_path = os.path.join(mesh_folder, mesh_file)
        
        mesh = trimesh.load(file_path, process=False)
        v = np.array(mesh.vertices)
        all_vertices.append(v)

    # Convert the list of vertex arrays into a 3D numpy array (frames x vertices x 3)
    all_vertices_np = np.array(all_vertices)

    if write_folder is not None:
        os.makedirs(write_folder, exist_ok=True)
        out_dir = write_folder
    else:
        out_dir = os.path.dirname(os.path.abspath(mesh_folder))

    print(os.path.dirname(os.path.abspath(mesh_folder)))
    np.save(f'{out_dir}/meshes.npy', all_vertices_np)
    print(f"Saved vertices for {len(mesh_files)} meshes., ", all_vertices_np.shape)


def parse_args():
    parser = argparse.ArgumentParser(description="Stack mesh vertices into a numpy array.")
    parser.add_argument("--meshdir", help="Directory containing mesh files.")
    parser.add_argument("--ext", default="obj", help="")
    parser.add_argument("--outdir",default=None,
                        help="Optional output directory for meshes.npy. Defaults to input directory.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.ext == 'obj':
        new_outdir = os.path.join(args.outdir, 'plys')
        os.makedirs(new_outdir, exist_ok=True)
        obj2ply(args.meshdir, new_outdir)
        args.meshdir = new_outdir
        args.ext = 'ply'
    meshfolder2npy_maya(args.meshdir, ext=args.ext, write_folder=args.outdir)