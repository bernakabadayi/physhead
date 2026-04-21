import numpy as np
from pytorch3d.structures import Pointclouds
from pytorch3d.io import IO
import torch
import argparse

def calculate_curve_length_3d(points):
    total_length = 0.0
    for i in range(1, len(points)):
        total_length += np.linalg.norm(np.array(points[i]) - np.array(points[i-1]))
    return total_length

def redistribute_points_3d(points, num_points):
    curve_length = calculate_curve_length_3d(points)
    target_spacing = curve_length / (num_points - 1)

    new_points = [points[0]]
    accumulated_distance = 0.0

    for i in range(1, len(points)):
        segment_length = np.linalg.norm(np.array(points[i]) - np.array(points[i-1]))
        accumulated_distance += segment_length
        while accumulated_distance >= target_spacing:
            overshoot = accumulated_distance - target_spacing
            ratio = 1 - (overshoot / segment_length)
            new_point = tuple(points[i-1] + ratio * (np.array(points[i]) - np.array(points[i-1])))
            new_points.append(new_point)
            accumulated_distance = overshoot
    new_points.append(points[-1])

    return new_points[:num_points] if len(new_points) > num_points else new_points


def main(args):
    
    inp_path = args.inp_path
    
    strands = np.load(inp_path)
    print(strands.shape) # (4, 10, 3)

    num_points_desired = strands.shape[1]
    new_sparse_hair = []

    for idx, strand in enumerate(strands):
        new_curve_points_3d = redistribute_points_3d(strand, num_points_desired)
        pc = np.array(new_curve_points_3d)
        #print('shape of new hair', pc.shape)
        new_sparse_hair.append(pc)
        
    first_n_points = np.concatenate(new_sparse_hair, axis=0)
    first_n_points = torch.from_numpy(first_n_points.reshape(1, -1, 3))
    
    num_strands = len(new_sparse_hair)
    strand_colors = (np.random.rand(num_strands, 3) * 255).astype(np.uint8)
    point_colors = np.repeat(strand_colors, num_points_desired, axis=0).reshape(1, -1, 3)
    
    pcl = Pointclouds(points=first_n_points, features=torch.from_numpy(point_colors))

    out_f =  inp_path.replace('.npy', '_dist.ply')
    IO().save_pointcloud(pcl, out_f)

    reshaped_pc = np.reshape(first_n_points, (-1, num_points_desired, 3))
    out_f = out_f.replace('ply', 'npy')

    np.save(out_f, reshaped_pc)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(conflict_handler='resolve')
    parser.add_argument('--inp_path', default='./guided_2_k50000_p16.npy', type=str)

    args, _ = parser.parse_known_args()
    args = parser.parse_args()

    main(args)




