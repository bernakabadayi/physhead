from scipy.interpolate import CubicSpline
import numpy as np
import trimesh
import argparse
import os

def upsample_spline_batch(sim_points, num_points=100):
    """
    Upsample multiple hair strands using cubic spline interpolation.

    Args:
        sim_points: np.ndarray of shape (N, M, 3) where
                    N = number of strands,
                    M = number of simulated points (e.g., 4)
        num_points: number of points to upsample to (e.g., 100)
    Returns:
        upsampled: np.ndarray of shape (N, num_points, 3)
    """
    N, M, _ = sim_points.shape
    t_sim = np.linspace(0, 1, M)
    t_full = np.linspace(0, 1, num_points)
    upsampled = np.zeros((N, num_points, 3), dtype=np.float32)

    for i in range(N):
        strand = sim_points[i]
        for j in range(3):  # x, y, z
            spline = CubicSpline(t_sim, strand[:, j])
            upsampled[i, :, j] = spline(t_full)
    
    return upsampled

# Example usage
# sim_points = np.random.rand(100, 4, 3)
# reconstructed = upsample_spline_batch(sim_points, num_points=100)
# print(reconstructed.shape)  # (100, 100, 3)

parser = argparse.ArgumentParser(description="Upsample sparse hair strands to dense PLY files via cubic spline.")
parser.add_argument("--curves_dir", "-i",
    default="/curves_ply",
    help="Input directory containing sparse .ply files.")
parser.add_argument("--outdir", "-o", default=None,
    help="Output directory for dense .ply files. Defaults to <curves_dir>/../dense.")
parser.add_argument("--n_pts", type=int, default=50,
    help="Number of points to upsample each strand to (default: 50).")
parser.add_argument("--n_strands", type=int, default=700,
    help="Number of hair strands per frame (default: 700).")
args = parser.parse_args()

curves_dir = args.curves_dir
outdir = args.outdir or curves_dir.replace("curves_ply", "dense")
n_pts = args.n_pts
n_strands = args.n_strands

os.makedirs(outdir, exist_ok=True)
for f in sorted(os.listdir(curves_dir)):
    if f.endswith('.ply'):
        frame_idx = f.split('_')[-1].split('.')[0]
        path = os.path.join(curves_dir, f)
        v = trimesh.load(path).vertices
        v = np.array(v).reshape(n_strands, -1, 3)
        reconstructed = upsample_spline_batch(v, num_points=n_pts)
        out_path = f'{outdir}/{frame_idx.zfill(3)}.ply'
        trimesh.PointCloud(reconstructed.reshape(-1,3)).export(out_path)



