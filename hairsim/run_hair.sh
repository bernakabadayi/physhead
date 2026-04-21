#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# activate conda (override CONDA_BASE if your install lives elsewhere)
CONDA_BASE="${CONDA_BASE:-$HOME/anaconda3}"
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate physheadsim


# ─── Config ─────────

SUBJECT="20230313--1653--RHL466"
EXPRESSION='rightleft'

INP_PATH="data/input/${EXPRESSION}/${SUBJECT}/"
INPUT_HAIR_PLY="${INP_PATH}/nh_strands.ply"
OUTPUT_DIR="data/output/${EXPRESSION}/${SUBJECT}"

K=100 # sampled n_strands
P=20 # sampled n_points along strand

N_STRAND=60000 # n_strands in original hairstyle
N_SEGMENTS=100 # n_pts in each strand (original hairstyle)

# ───────────────────

# sample sparse strands and points
python hair_scripts/dense2sparse.py \
    --input_ply $INPUT_HAIR_PLY \
    --out_dir $OUTPUT_DIR \
    --k $K \
    --p $P \
    --n_strand $N_STRAND \
    --n_segments $N_SEGMENTS

# redistribute
python hair_scripts/redistribute_points.py --inp_path "${OUTPUT_DIR}/guided_2_k${K}_p${P}.npy"

# convert npy to pickle for Maya
python hair_scripts/npy2pickle.py \
    --npy_path "${OUTPUT_DIR}/guided_2_k${K}_p${P}_dist.npy"