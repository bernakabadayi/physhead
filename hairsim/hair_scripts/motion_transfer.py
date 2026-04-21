import numpy as np
from sklearn.neighbors import NearestNeighbors
import trimesh
import os
import shutil
import argparse
from pytorch3d.io import IO
from pytorch3d.structures import Pointclouds
import torch


def read_motion(curves_dir, num_frames=1000, num_strands=500, segments=16):
    motion_data = []

    ply_files = [f for f in os.listdir(curves_dir) if f.endswith('.ply')]
    ply_files.sort()
    num_frames = len(ply_files)
    
    for frame_idx in range(num_frames):
        # frame_name = f'curves_frame_{frame_idx + 1:03}.ply'
        frame_name = f'{frame_idx + 1:03}.ply'
        
        frame_file = os.path.join(curves_dir, frame_name)
        
        sparse_motion = trimesh.load_mesh(frame_file, process=False)
        frame_motion = sparse_motion.vertices.reshape(num_strands, segments, 3)
        
        motion_data.append(frame_motion)

    # [num_frames, num_strands, segments, 3]
    motion_data = np.stack(motion_data, axis=0)
    return motion_data, num_frames, segments

def convert_motion_np_sequence(motion_data, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    sim_ply = out_dir + '_ply'
    os.makedirs(sim_ply, exist_ok=True)

    for frame_idx, frame_motion in enumerate(motion_data):
        frame_file = os.path.join(out_dir, f'frame_{frame_idx + 1}.npy')
        print(frame_file)
        np.save(frame_file, frame_motion)

        # save as pointcloud 
        particles = frame_motion.reshape(-1, 3)
        particles = torch.from_numpy(particles)
        pc = torch.unsqueeze(particles, 0)
        save_path = os.path.join(sim_ply, f'frame_{frame_idx + 1}.ply')
        IO().save_pointcloud(Pointclouds(pc), save_path)



def sparse_to_dense_strand_based_relative_motion(sparse_motion, dense_strands, k=10):
    t, num_sparse_strands, nsegments, _ = sparse_motion.shape
    num_dense_strands = dense_strands.shape[0]
    
    # Initialize the output array
    dense_motion = np.zeros((t, num_dense_strands, nsegments, 3))
    
    # Compute the roots for KNN in the initial frame
    sparse_strand_roots = sparse_motion[0, :, 0, :]  # Shape [500, 3]
    dense_strand_roots = dense_strands[:, 0, :]      # Shape [50000, 3]

    # K-nearest neighbors for strand roots (calculated only once based on the first frame)
    nn = NearestNeighbors(n_neighbors=k).fit(sparse_strand_roots)
    distances, indices = nn.kneighbors(dense_strand_roots)
    
    # Compute weights for each neighbor (based on distances)
    weights = 1 / (distances + 1e-8)  # Avoid division by zero
    weights /= weights.sum(axis=1, keepdims=True)  # Normalize weights

    # Initialize the first frame for dense motion directly from the dense strands
    # You can start from dense_strands directly here, no need to use sparse motion to adjust it.
    dense_motion[0] = dense_strands  # Directly initialize with the dense strand positions    

    # Transfer relative motion frame by frame
    for frame in range(1, t):
        for dense_idx in range(num_dense_strands):
            # Get KNN sparse strands for the dense strand in the current frame
            nearest_sparse_indices = indices[dense_idx]
            
            # Calculate relative displacement for each segment by averaging KNN sparse displacements
            relative_displacement = np.einsum('i,ijk->jk', weights[dense_idx], 
                                              sparse_motion[frame, nearest_sparse_indices] - sparse_motion[frame - 1, nearest_sparse_indices])
            
            # Apply the relative displacement to the dense strand based on the previous frame's position
            dense_motion[frame, dense_idx] = dense_motion[frame - 1, dense_idx] + relative_displacement

        print(f'Processed frame {frame + 1}/{t}')
    
    return dense_motion

def main():
    parser = argparse.ArgumentParser(description='Transfer motion from sparse to dense hair strands')
    parser.add_argument('--n_strands', type=int, default=200, help='Number of sparse strands')
    parser.add_argument('--n_segment', type=int, default=40, help='Number of segments per strand')
    parser.add_argument('--expression', type=str, default='HAIR-1-rotate', help='Expression name')
    parser.add_argument('--simulation_dir', type=str, required=True, 
                        help='Simulation directory')
    parser.add_argument('--dense_path', type=str, required=True,
                        help='Path to dense hair mesh')
    parser.add_argument('--k', type=int, default=10, help='Number of nearest neighbors')
    
    args = parser.parse_args()
    
    n_strands = args.n_strands
    n_segment = args.n_segment
    expression = args.expression
    k = args.k
    
    simulation_dir = args.simulation_dir
    curves_dir = f'{simulation_dir}/dense'
    save_dir = f'{simulation_dir}/sim'
    dense_path = args.dense_path
    
    if not os.path.exists(dense_path):
        assert False, f"Input folder '{dense_path}' does not exist."
    
    dense_strands = trimesh.load_mesh(dense_path, process=False).vertices.reshape(-1, n_segment, 3)
    sparse_motion, t, nsegments = read_motion(curves_dir, num_strands=n_strands, segments=n_segment)
    dense_motion = sparse_to_dense_strand_based_relative_motion(sparse_motion, dense_strands, k=k)
    
    if os.path.exists(save_dir):
        shutil.rmtree(save_dir)
    
    os.makedirs(save_dir, exist_ok=True)
    convert_motion_np_sequence(dense_motion, save_dir)

if __name__ == "__main__":
    main()





