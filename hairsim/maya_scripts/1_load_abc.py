import maya.cmds as cmds
import maya.mel as mel
import os

def clean_scene():
    non_delete_objects = {'topShape', 'sideShape', 'perspShape', 'frontShape',
                          'front', 'persp', 'side', 'top'}
    
    all_objects = cmds.ls(type='transform')
    to_delete = [i for i in all_objects if i not in non_delete_objects and cmds.objExists(i)]
    
    if to_delete:
        cmds.delete(to_delete)

def upload_mesh_sequence(sequence_name=None):
    if sequence_name is None:
        raise ValueError("A valid Alembic file path must be provided.")
    if not os.path.exists(sequence_name):
        raise FileNotFoundError(f"Alembic file not found: {sequence_name}")
    
    command = (
        f'file -import -type "Alembic" -ignoreVersion -ra true '
        f'-mergeNamespacesOnClash false -namespace "male" -pr '
        f'-importFrameRate true -importTimeRange "override" "{sequence_name}";'
    )
    mel.eval(command)

clean_scene()
mel.eval('currentTime 1;')
upload_mesh_sequence(sequence_name='/Users/bernakabadayi/Downloads/output/00000.abc')