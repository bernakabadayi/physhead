# From a given hair ply file, sample k points along N dimension and p points along M dimension

import numpy as np
from pytorch3d.structures import Pointclouds
from pytorch3d.io import IO
import torch
import os
import argparse


def main(args):

    n_strand = args.n_strand
    n_segments = args.n_segments

    k = args.k   # Number of points to sample along N dimension, strand
    p = args.p    # Number of points to sample along M dimension, segment

    init_pc = IO().load_pointcloud(args.input_ply)
    point_cloud = init_pc._points_list[0].numpy() # point_cloud: N x 3, N = 818 * 100
    hair_pc = point_cloud.reshape(-1, n_segments, 3)

    def linear_sample_k_p(array, k, p):
        # [N, M, 3] -> [k, p, 3]
        N, M, _ = array.shape
        N_indices = np.linspace(0, N - 1, k, dtype=int)
        sampled_N_points = array[N_indices]

        M_indices = np.linspace(0, M - 1, p, dtype=int)
        return sampled_N_points[:, M_indices]

    sampled_points = linear_sample_k_p(hair_pc, k, p) # (4, 10, 3)
    first_n_points = torch.from_numpy(sampled_points.reshape(1, -1, 3))

    strand_colors = (np.random.rand(k, 3) * 255).astype(np.uint8)
    point_colors = np.repeat(strand_colors[:, None, :], p, axis=1).reshape(1, -1, 3)

    pcl = Pointclouds(points=first_n_points, features=torch.from_numpy(point_colors))

    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)    
        
    out_f = '{}/guided_2_k{}_p{}.ply'.format(args.out_dir, k, p)
    IO().save_pointcloud(pcl, out_f)
    print(out_f)

    reshaped_pc = np.reshape(point_cloud, (-1, n_segments, 3))
    out_f = out_f.replace('ply', 'npy')

    print('sampled_points: ', sampled_points.shape)
    np.save(out_f, sampled_points)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(conflict_handler='resolve')
    parser.add_argument('--input_ply', default='data/input/nh_strands.ply', type=str)
    
    parser.add_argument('--out_dir', default="./data/output")
    parser.add_argument('--k', default=1000, type=int, help='Number of points to sample along N dimension, strand')
    parser.add_argument('--p', default=32, type=int, help='Number of points to sample along M dimension, number of points in a segment, better to pick a power of 2 for simulation')
    parser.add_argument('--n_strand', default=60000, type=int, help='Number of strands')
    parser.add_argument('--n_segments', default=100, type=int, help='Number of segments in each strand')

    args, _ = parser.parse_known_args()
    args = parser.parse_args()

    main(args)
    
