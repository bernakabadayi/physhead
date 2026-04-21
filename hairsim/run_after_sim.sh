#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse command-line arguments (defaults are for the sample data)
EXPRESSION="${1:-rightleft}"
SUBJECT="${2:-20230313--1653--RHL466}"

# activate conda (override CONDA_BASE if your install lives elsewhere)
CONDA_BASE="${CONDA_BASE:-$HOME/anaconda3}"
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate physheadsim

# ─── Config ─────────

INP_PATH="data/input/${EXPRESSION}/${SUBJECT}/"
INPUT_HAIR_PLY="${INP_PATH}/nh_strands.ply" # change the input 
OUTPUT_DIR="data/sim_out/${EXPRESSION}/${SUBJECT}"

K=50 # n_strands (sparse)
P=100 # how n_pts in original hair style 

# ───────────────────

# convert simulation pickle files to ply
python hair_scripts/pickle2ply.py --input_folder "${OUTPUT_DIR}/curves"

# 1. densify densify hair style along the strand (i.e. for sample data there is 100 pts in each strand)
python hair_scripts/to100.py \
  --curves_dir "${OUTPUT_DIR}/curves_ply" \
  --outdir "${OUTPUT_DIR}/dense" \
  --n_pts $P \
  --n_strands $K

# 2. motion transfer using strand skinning, change k if needed
python hair_scripts/motion_transfer.py \
  --n_strands $K \
  --n_segment $P \
  --expression "${EXPRESSION}" \
  --simulation_dir "${OUTPUT_DIR}" \
  --dense_path "${INPUT_HAIR_PLY}" \
  --k 10


