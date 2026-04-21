import numpy as np
import pickle
import argparse

def np2pickle(npy_path):
    data = np.load(npy_path)

    pickle_path = npy_path.replace('.npy', '.pickle')

    control_points = [curve.tolist() for curve in data]
    with open(pickle_path, 'wb') as fp:
        pickle.dump(control_points, fp)
        
    print(f"Pickle file saved to {pickle_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(conflict_handler='resolve')
    parser.add_argument('--npy_path', default='/is/cluster/fast/bkabadayi/eccv26/seqs_004/guided_2_k500_p20.npy', type=str)
    args = parser.parse_args()
    np2pickle(args.npy_path)
    
