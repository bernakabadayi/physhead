import maya.cmds as cmds
import maya.mel as mel
import pickle
import os
import json
import time

# its nice to save meshes to check if they aligned with input meshes

HAIR_ATTRS = [
    'selfCollide', 'friction', 'stickiness',
    'stretchResistance', 'compressionResistance', 'bendResistance',
    'twistResistance', 'extraBendLinks',
    'mass', 'drag', 'tangentialDrag', 'damp', 'stretchDamp',
    'dynamicsWeight', 'staticCling', 'startCurveAttract',
]

NUCLEUS_ATTRS = [
    'gravity', 'gravityDirectionX', 'gravityDirectionY', 'gravityDirectionZ',
    'airDensity', 'windSpeed', 'windDirectionX', 'windDirectionY', 'windDirectionZ',
    'windNoise', 'subSteps', 'maxCollisionIterations', 'timeScale', 'spaceScale',
    'startFrame',
]


def save_sim_params(save_folder, end_frame, mesh_name, hair_shape='hairSystemShape1'):
    params = {
        'end_frame': end_frame,
        'mesh_name': mesh_name,
        'hair_shape': hair_shape,
        'frame_rate': cmds.currentUnit(query=True, time=True),
    }

    if cmds.objExists(hair_shape):
        params['hair_system'] = {
            attr: cmds.getAttr(f'{hair_shape}.{attr}') for attr in HAIR_ATTRS
        }

    nuclei = cmds.ls(type='nucleus')
    params['nucleus'] = {
        n: {attr: cmds.getAttr(f'{n}.{attr}') for attr in NUCLEUS_ATTRS}
        for n in nuclei
    }

    out_path = os.path.join(save_folder, 'sim_params.json')
    with open(out_path, 'w') as fp:
        json.dump(params, fp, indent=2)
    print(f"Saved simulation parameters to {out_path}")


def save_simulations(save_folder, end_frame=1, mesh_name='male:transform1'):

    curves_dir = os.path.join(save_folder, 'curves')
    meshes_dir = os.path.join(save_folder, 'meshes')
    os.makedirs(curves_dir, exist_ok=True)
    os.makedirs(meshes_dir, exist_ok=True)

    save_sim_params(save_folder, end_frame, mesh_name)

    # Get all dynamic output curve shapes once
    all_curves = cmds.ls(type='nurbsCurve')
    follicle_shapes = [c for c in all_curves if 'curveShape' in c]
    print(f"Found {len(follicle_shapes)} curves to export.")

    # Cache CV counts — spans/degree don't change per frame
    cv_counts = {
        name: cmds.getAttr(f'{name}.spans') + cmds.getAttr(f'{name}.degree')
        for name in follicle_shapes
    }

    for frame in range(1, end_frame):
        cmds.currentTime(frame)
        all_pos = []

        for curve_name in follicle_shapes:
            num_cvs = cv_counts[curve_name]
            cv_list = [f'{curve_name}.cv[{i}]' for i in range(num_cvs)]

            # Batch query all CVs in one call instead of one per CV
            flat = cmds.xform(cv_list, query=True, translation=True, worldSpace=True)
            positions = [flat[i*3:(i*3)+3] for i in range(num_cvs)]
            all_pos.append(positions)

        frame_num = str(frame).zfill(3)

        # Save curve data
        curves_path = os.path.join(curves_dir, f'curves_frame_{frame_num}.pickle')
        with open(curves_path, 'wb') as fp:
            pickle.dump(all_pos, fp)

        # Save mesh as OBJ
        cmds.select(mesh_name, replace=True)
        mesh_path = os.path.join(meshes_dir, f'mesh_{frame_num}.obj')
        cmds.file(
            mesh_path,
            force=True,
            options="groups=1;ptgroups=1;materials=0;smoothing=0;normals=0",
            typ="OBJexport",
            pr=True,
            es=True
        )
        cmds.select(clear=True)

        print(f"Saved frame {frame_num}")


cmds.currentTime(1)
start_time = time.time()

save_simulations(
    save_folder='/Users/bernakabadayi/dev-local/physhead_simulation/sim_out',
    end_frame=70,
    mesh_name='male:transform1'
)

elapsed = time.time() - start_time
print(f"Simulation saving took {elapsed:.2f} seconds.")
cmds.currentTime(1)