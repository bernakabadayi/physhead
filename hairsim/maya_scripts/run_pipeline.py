import maya.cmds as cmds
import maya.mel as mel
import runpy
import time

# ─────────────────────────────────────────────
#  1. PATHS TO YOUR 3 SCRIPTS — edit these
# ─────────────────────────────────────────────
SCRIPT_1_LOAD_MESH  = '/Users/bernakabadayi/dev-local/physhead_simulation/maya_scripts/1_load_abc.py'
SCRIPT_2_LOAD_HAIR  = '/Users/bernakabadayi/dev-local/physhead_simulation/maya_scripts/2_create_nurbs.py'
SCRIPT_3_SAVE_SIM   = '/Users/bernakabadayi/dev-local/physhead_simulation/maya_scripts/3_savesim.py'

# ─────────────────────────────────────────────
#  2. check each script and replace the 'sequence_name', PICKLE_PATH and save_folder
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
#  3. run run_pipeline.py in Maya's script editor (Python not MEL)
# ─────────────────────────────────────────────
def run_script(path, label):
    print(f"\n{'='*50}")
    print(f"  Running: {label}")
    print(f"{'='*50}")
    t0 = time.time()
    runpy.run_path(path, run_name="__main__")
    print(f"  Done in {time.time() - t0:.2f}s")


# run_script(SCRIPT_1_LOAD_MESH, "Stage 1 — Load Mesh")
# run_script(SCRIPT_2_LOAD_HAIR, "Stage 2 — Load Hair")
run_script(SCRIPT_3_SAVE_SIM,  "Stage 3 — Save Simulation")

print("\nPipeline complete")