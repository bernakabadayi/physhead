"""Render simulated hair strands + head mesh per frame with Blender.

Usage (run inside Blender):
    blender --background --python render_blender.py -- \
        --input_dir  /lustre/home/bkabadayi/dev-cluster/cvpr2026/physhead/hairsim/data/sim_out \
        --output_dir /lustre/home/bkabadayi/dev-cluster/cvpr2026/physhead/hairsim/data/sim_out/hair_renders

Inputs per frame i (1-based, 3-digit zero-padded):
    <input_dir>/curves/curves_frame_{i:03d}.pickle  -> list/array of shape (N_STRANDS, N_POINTS, 3)
    <input_dir>/meshes/mesh_{i:03d}.obj
Output:
    <output_dir>/render_{i:03d}.png
"""

import argparse
import colorsys
import math
import os
import pickle
import shutil
import subprocess
import sys

import bpy


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--input_dir", required=True,
                   help="Directory containing curves/ and meshes/ subdirectories.")
    p.add_argument("--output_dir", required=True,
                   help="Where rendered PNGs are written.")
    p.add_argument("--resolution", type=int, default=1024)
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--strand_radius", type=float, default=0.0008,
                   help="Bevel radius (meters) giving hair strands their visual thickness.")
    p.add_argument("--engine", default="CYCLES", choices=["CYCLES", "BLENDER_EEVEE"])
    p.add_argument("--device", default="CPU", choices=["CPU", "GPU"])
    p.add_argument("--cam_loc", type=float, nargs=3, default=[0.0, -0.6, 0.05],
                   help="Camera world location (x y z). Default assumes head faces -Y.")
    p.add_argument("--target_loc", type=float, nargs=3, default=[0.0, 0.0, -0.03],
                   help="Point the camera tracks to (roughly head centroid).")
    p.add_argument("--hair_rot", type=float, nargs=3, default=[90.0, 0.0, 0.0],
                   help="Euler XYZ rotation (degrees) applied to hair strands via a parent empty.")
    p.add_argument("--bg_color", type=float, nargs=3, default=[0.92, 0.92, 0.93])
    p.add_argument("--exposure", type=float, default=-2.0,
                   help="Scene view exposure (stops). Lower = darker.")
    p.add_argument("--start", type=int, default=None, help="First frame index (inclusive).")
    p.add_argument("--end", type=int, default=None, help="Last frame index (inclusive).")
    p.add_argument("--stride", type=int, default=1)
    p.add_argument("--fps", type=int, default=24, help="Frame rate for the assembled video.")
    p.add_argument("--video_name", default="hair_render.mp4",
                   help="Output video filename inside --output_dir. Empty string disables video.")
    return p.parse_args(argv)


def assemble_video(output_dir, frame_indices, fps, video_name):
    if not video_name or not frame_indices:
        return
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        print("[warn] ffmpeg not found on PATH; skipping video assembly")
        return
    start = min(frame_indices)
    video_path = os.path.join(output_dir, video_name)
    cmd = [
        ffmpeg, "-y",
        "-framerate", str(fps),
        "-start_number", str(start),
        "-i", os.path.join(output_dir, "render_%03d.png"),
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        video_path,
    ]
    print(f"[info] assembling video -> {video_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[warn] ffmpeg failed (exit {result.returncode}):\n{result.stderr}")
    else:
        print(f"[video] {video_path}")


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def configure_render(scene, args):
    scene.render.engine = args.engine
    scene.render.resolution_x = args.resolution
    scene.render.resolution_y = args.resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.exposure = args.exposure
    scene.view_settings.view_transform = "Standard"
    if args.engine == "CYCLES":
        scene.cycles.samples = args.samples
        try:
            scene.cycles.device = args.device
        except Exception as e:
            print(f"[warn] could not set cycles device to {args.device}: {e}")
    else:
        scene.eevee.taa_render_samples = args.samples


def build_world(scene, bg_color):
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*bg_color, 1.0)
    bg.inputs[1].default_value = 1.0


def build_camera(scene, cam_loc, target_loc):
    target = bpy.data.objects.new("CamTarget", None)
    target.location = tuple(target_loc)
    scene.collection.objects.link(target)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 50
    cam_obj = bpy.data.objects.new("Cam", cam_data)
    cam_obj.location = tuple(cam_loc)
    scene.collection.objects.link(cam_obj)

    cons = cam_obj.constraints.new("TRACK_TO")
    cons.target = target
    cons.track_axis = "TRACK_NEGATIVE_Z"
    cons.up_axis = "UP_Y"
    scene.camera = cam_obj


def build_lights(scene):
    target = bpy.data.objects.get("CamTarget")

    def track_to(obj):
        if target is None:
            return
        cons = obj.constraints.new("TRACK_TO")
        cons.target = target
        cons.track_axis = "TRACK_NEGATIVE_Z"
        cons.up_axis = "UP_Y"

    def add_area(name, loc, energy, size=1.0):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.size = size
        obj = bpy.data.objects.new(name, data)
        obj.location = loc
        scene.collection.objects.link(obj)
        track_to(obj)
        return obj

    add_area("Key",  ( 0.6, -0.6,  0.5), energy=100, size=1.0)
    add_area("Fill", (-0.6, -0.3,  0.2), energy=40,  size=1.5)
    add_area("Rim",  ( 0.0,  0.4,  0.6), energy=80,  size=1.0)

    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 1.0
    sun_obj = bpy.data.objects.new("Sun", sun_data)
    sun_obj.location = (0.0, -0.3, 1.0)
    sun_obj.rotation_euler = (math.radians(45), 0, math.radians(20))
    scene.collection.objects.link(sun_obj)


def make_mesh_material():
    mat = bpy.data.materials.new("MeshMat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.45, 0.40, 0.37, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85
    if "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = 0.1
    return mat


def make_strand_materials(n):
    mats = []
    for i in range(n):
        # Golden-ratio hue sequence → visually distinct rainbow across adjacent strands.
        h = (i * 0.61803398875) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, 0.85, 0.95)
        mat = bpy.data.materials.new(f"StrandMat_{i:03d}")
        mat.use_nodes = True
        bs = mat.node_tree.nodes["Principled BSDF"]
        bs.inputs["Base Color"].default_value = (r, g, b, 1.0)
        bs.inputs["Roughness"].default_value = 0.4
        mats.append(mat)
    return mats


def clear_frame_objects():
    for obj in list(bpy.data.objects):
        if obj.name.startswith(("HeadMesh", "Hair_")):
            bpy.data.objects.remove(obj, do_unlink=True)
    for block in list(bpy.data.meshes):
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in list(bpy.data.curves):
        if block.users == 0 and block.name.startswith("HairCurve_"):
            bpy.data.curves.remove(block)


def load_mesh(obj_path, mesh_mat, scene):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.obj(filepath=obj_path,
                             use_split_objects=False,
                             use_split_groups=False)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        o.name = "HeadMesh"
        o.data.materials.clear()
        o.data.materials.append(mesh_mat)
        # Smooth shading so the head looks less faceted.
        for poly in o.data.polygons:
            poly.use_smooth = True
    return new


def build_hair(strands, radius, strand_mats, scene, hair_parent):
    n_mats = len(strand_mats)
    for i, strand in enumerate(strands):
        cu = bpy.data.curves.new(f"HairCurve_{i:03d}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = radius
        cu.bevel_resolution = 2
        cu.use_fill_caps = True
        spline = cu.splines.new("POLY")
        spline.points.add(len(strand) - 1)
        for j, p in enumerate(strand):
            spline.points[j].co = (float(p[0]), float(p[1]), float(p[2]), 1.0)
        cu.materials.append(strand_mats[i % n_mats])
        obj = bpy.data.objects.new(f"Hair_{i:03d}", cu)
        scene.collection.objects.link(obj)
        if hair_parent is not None:
            obj.parent = hair_parent


def list_frames(input_dir, start, end, stride):
    curves_dir = os.path.join(input_dir, "curves")
    mesh_dir = os.path.join(input_dir, "meshes")
    frames = []
    for fname in sorted(os.listdir(curves_dir)):
        if not fname.endswith(".pickle"):
            continue
        try:
            idx = int(fname.replace("curves_frame_", "").replace(".pickle", ""))
        except ValueError:
            continue
        if start is not None and idx < start:
            continue
        if end is not None and idx > end:
            continue
        if (idx - (start or idx)) % stride != 0:
            continue
        mesh_path = os.path.join(mesh_dir, f"mesh_{idx:03d}.obj")
        if not os.path.exists(mesh_path):
            print(f"[warn] missing mesh for frame {idx}: {mesh_path}")
            continue
        frames.append((idx, os.path.join(curves_dir, fname), mesh_path))
    return frames


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    reset_scene()
    scene = bpy.context.scene
    configure_render(scene, args)
    build_world(scene, args.bg_color)
    build_camera(scene, args.cam_loc, args.target_loc)
    build_lights(scene)

    mesh_mat = make_mesh_material()
    # Will be resized to match actual strand count on the first frame.
    strand_mats = []

    # Persistent empty that parents all hair strands. Rotating the empty
    # rotates the whole hair group without mutating the underlying point data.
    hair_parent = bpy.data.objects.new("HairRoot", None)
    hair_parent.rotation_euler = (
        math.radians(args.hair_rot[0]),
        math.radians(args.hair_rot[1]),
        math.radians(args.hair_rot[2]),
    )
    scene.collection.objects.link(hair_parent)

    frames = list_frames(args.input_dir, args.start, args.end, args.stride)
    print(f"[info] {len(frames)} frames to render -> {args.output_dir}")
    rendered_indices = []

    for idx, curve_path, mesh_path in frames:
        clear_frame_objects()
        load_mesh(mesh_path, mesh_mat, scene)

        with open(curve_path, "rb") as fp:
            strands = pickle.load(fp)  # list/array of shape (N_STRANDS, N_POINTS, 3)
        if len(strand_mats) < len(strands):
            strand_mats = make_strand_materials(len(strands))

        build_hair(strands, args.strand_radius, strand_mats, scene, hair_parent)

        out_path = os.path.join(args.output_dir, f"render_{idx:03d}.png")
        scene.render.filepath = out_path
        print(f"[frame {idx:03d}] {len(strands)} strands -> {out_path}")
        bpy.ops.render.render(write_still=True)
        rendered_indices.append(idx)

    assemble_video(args.output_dir, rendered_indices, args.fps, args.video_name)
    print("[done]")


if __name__ == "__main__":
    main()
