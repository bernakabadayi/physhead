import maya.cmds as cmds
import maya.mel as mel
import pickle
import time

begin_time = time.time()

PICKLE_PATH = '/Users/bernakabadayi/Downloads/output/guided_2_k50_p20_dist.pickle'
MESH_NAME = 'male:transform1'
HAIR_SHAPE = 'hairSystemShape1'
NUM_CURVES = 50  # cap for testing; set to len(control_points) for full run

with open(PICKLE_PATH, 'rb') as fp:
    control_points = pickle.load(fp)

print(f"Total curves in file: {len(control_points)}, creating: {NUM_CURVES}")

# Create NURBS curves
for i in range(NUM_CURVES):
    cmds.curve(d=3, p=control_points[i], name=f"Curve{i}")

# Group all created curves
cmds.select(cmds.ls(type="nurbsCurve"), r=True)
cmds.group(name="NurbsCurves_Group")

# Make curves dynamic against the mesh
mel.eval("select -r NurbsCurves_Group;")
mel.eval(f"select -add {MESH_NAME};")
mel.eval('makeCurvesDynamic 2 { "1", "1", "1", "1", "0"};')

# Make mesh an nCloth collider
mel.eval(f"select -r {MESH_NAME};")
mel.eval("makeCollideNCloth;")

# Hide original curves
mel.eval("select -r NurbsCurves_Group;")
cmds.hide()

# Hair system — collisions
cmds.setAttr(f"{HAIR_SHAPE}.selfCollide", 1)
cmds.setAttr(f"{HAIR_SHAPE}.friction", 0.51087)
cmds.setAttr(f"{HAIR_SHAPE}.stickiness", 0.51087)

# Hair system — resistance
cmds.setAttr(f"{HAIR_SHAPE}.stretchResistance", 600)
cmds.setAttr(f"{HAIR_SHAPE}.compressionResistance", 600.0)
# cmds.setAttr(f"{HAIR_SHAPE}.bendResistance", 10)
cmds.setAttr(f"{HAIR_SHAPE}.bendResistance", 60)
cmds.setAttr(f"{HAIR_SHAPE}.twistResistance", 1.718)
cmds.setAttr(f"{HAIR_SHAPE}.extraBendLinks", 3)

# Hair system — forces
cmds.setAttr(f"{HAIR_SHAPE}.mass", 2)
cmds.setAttr(f"{HAIR_SHAPE}.drag", 0.65)
cmds.setAttr(f"{HAIR_SHAPE}.tangentialDrag", 0.0965909)
# cmds.setAttr(f"{HAIR_SHAPE}.damp", 0.25)
cmds.setAttr(f"{HAIR_SHAPE}.damp", 0.8)
cmds.setAttr(f"{HAIR_SHAPE}.stretchDamp", 1)
cmds.setAttr(f"{HAIR_SHAPE}.dynamicsWeight", 1)
cmds.setAttr(f"{HAIR_SHAPE}.staticCling", 0.025)
# cmds.setAttr(f"{HAIR_SHAPE}.startCurveAttract", 0.15)
cmds.setAttr(f"{HAIR_SHAPE}.startCurveAttract", 0.6)

elapsed_time = time.time() - begin_time
print(f"Setup took {elapsed_time:.2f} seconds.")