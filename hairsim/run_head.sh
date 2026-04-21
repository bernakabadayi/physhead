#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# activate conda (override CONDA_BASE if your install lives elsewhere)
CONDA_BASE="${CONDA_BASE:-$HOME/anaconda3}"
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate physheadsim

# ─── User config ─────────
SUBJECT="20230313--1653--RHL466"
EXPRESSION="rightleft"
FPS=24                                                   # should match Maya fps
BLENDER_PATH="/is/cluster/fast/bkabadayi/blender/blender"  # I use Blender 3.6.8

# ─── paths ───────────────
INP_PATH="data/input/${EXPRESSION}/${SUBJECT}"
MESH_DIR="${INP_PATH}/flame_ply"
MESH_EXT="ply"

OUTPUT_DIR="data/output/${EXPRESSION}/${SUBJECT}"
BLENDER_OUTPUT="${OUTPUT_DIR}/output.blend"
ABC_OUTPUT="${OUTPUT_DIR}/mesh_0000.abc"
ABC_OUTPUT_UV="${OUTPUT_DIR}/mesh_0000_uv.abc"
BLENDER_OUTPUT_UV="${OUTPUT_DIR}/output_uv.blend"

# Takes mesh folder and converts into single npy file
python head_scripts/meshfolder2npy_maya.py --meshdir "${MESH_DIR}" --ext "${MESH_EXT}" --outdir "${OUTPUT_DIR}"

# Get number of frames from meshes.npy
NUM_FRAMES=$(python -c "import numpy as np; print(np.load('${OUTPUT_DIR}/meshes.npy').shape[0])")
echo "Number of frames: ${NUM_FRAMES}"

# converts list of meshes into abc and save them to output.blend
${BLENDER_PATH} --background --python head_scripts/mesh2abc.py \
    -- \
    --meshes_npy "${OUTPUT_DIR}/meshes.npy" \
    --mesh_ply "${MESH_DIR}/00000.ply" \
    --output_blend "${BLENDER_OUTPUT}" \
    --fps ${FPS}

# save abc output
${BLENDER_PATH} ${BLENDER_OUTPUT} \
    --background \
    --python head_scripts/export_abc.py \
    -- \
    --output_abc "${ABC_OUTPUT}" \
    --isrotate \
    --fps ${FPS}

# add uv and transform 90
${BLENDER_PATH} "${BLENDER_OUTPUT}" \
    --background --python head_scripts/adduv.py \
    --python-expr "import bpy; bpy.ops.wm.save_as_mainfile(filepath='${BLENDER_OUTPUT_UV}')"


# save abc output
${BLENDER_PATH} ${BLENDER_OUTPUT_UV} \
    --background \
    --python head_scripts/export_abc.py \
    -- \
    --output_abc "${ABC_OUTPUT_UV}" \
    --fps ${FPS}

${BLENDER_PATH} --background \
    --python head_scripts/rename_abc.py \
    -- \
    --input_abc "${ABC_OUTPUT_UV}" \
    --output_abc "${OUTPUT_DIR}/00000.abc" \
    --name "00000" \
    --fps ${FPS} \
    --start 1 \
    --end ${NUM_FRAMES}
