"""Render a single frame of the DENSE hair (from a flat PLY point cloud) over
a head mesh (PLY) with Blender.

Usage:
    blender --background --python render_dense_single.py -- \
        --head_ply /path/to/flame_ply/00000.ply \
        --hair_ply /path/to/nh_strands_k60000_p50_dist.ply \
        --n_strands 60000 --n_points 50 \
        --output_dir /path/to/outdir

Hair PLY layout assumed (as produced by the repo's scripts): binary_little_endian
with vertex properties x y z red green blue (floats), total vertices = K*P, strand
i occupies vertices [i*P, (i+1)*P).
"""

import argparse
import colorsys
import math
import os
import re
import sys

import bpy
import numpy as np


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--head_ply", required=True)
    p.add_argument("--hair_ply", required=True)
    p.add_argument("--n_strands", type=int, default=60000)
    p.add_argument("--n_points", type=int, default=50)
    p.add_argument("--output_dir", required=True)
    p.add_argument("--output_name", default="dense_render.png")
    p.add_argument("--resolution", type=int, default=1024)
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--strand_radius", type=float, default=0.00015,
                   help="Bevel radius (meters) — dense hair wants thin strands.")
    p.add_argument("--strands_per_object", type=int, default=2000,
                   help="How many strands to pack into each Blender curve datablock.")
    p.add_argument("--engine", default="CYCLES", choices=["CYCLES", "BLENDER_EEVEE"])
    p.add_argument("--device", default="CPU", choices=["CPU", "GPU"])
    p.add_argument("--cam_loc", type=float, nargs=3, default=[0.0, -0.6, 0.05],
                   help="Camera world location (matches render_blender.py default).")
    p.add_argument("--target_loc", type=float, nargs=3, default=[0.0, 0.0, -0.03],
                   help="Look-at target (matches render_blender.py default).")
    p.add_argument("--hair_rot", type=float, nargs=3, default=[90.0, 0.0, 0.0],
                   help="Euler XYZ (degrees) applied to hair via a parent empty.")
    p.add_argument("--head_rot", type=float, nargs=3, default=[90.0, 0.0, 0.0],
                   help="Euler XYZ (degrees) applied to the head mesh (FLAME -> sim frame).")
    p.add_argument("--bg_color", type=float, nargs=3, default=[0.92, 0.92, 0.93])
    p.add_argument("--hair_color", type=float, nargs=3, default=[0.18, 0.12, 0.08],
                   help="Base hair color when --rainbow is not set.")
    p.add_argument("--rainbow", action="store_true",
                   help="Give each strand a distinct color (golden-ratio hue sequence).")
    p.add_argument("--rainbow_palette", type=int, default=1024,
                   help="Size of the shared rainbow material pool used when --rainbow is set.")
    p.add_argument("--exposure", type=float, default=-2.0)
    return p.parse_args(argv)


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


def make_hair_material(color):
    mat = bpy.data.materials.new("HairMat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.55
    return mat


def make_rainbow_materials(n):
    mats = []
    for i in range(n):
        h = (i * 0.61803398875) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, 0.85, 0.95)
        mat = bpy.data.materials.new(f"StrandMat_{i:04d}")
        mat.use_nodes = True
        bs = mat.node_tree.nodes["Principled BSDF"]
        bs.inputs["Base Color"].default_value = (r, g, b, 1.0)
        bs.inputs["Roughness"].default_value = 0.4
        mats.append(mat)
    return mats


def import_head(head_ply, mesh_mat, head_rot_deg):
    before = set(bpy.data.objects)
    bpy.ops.import_mesh.ply(filepath=head_ply)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        o.name = "HeadMesh"
        o.data.materials.clear()
        o.data.materials.append(mesh_mat)
        for poly in o.data.polygons:
            poly.use_smooth = True
        o.rotation_euler = (
            math.radians(head_rot_deg[0]),
            math.radians(head_rot_deg[1]),
            math.radians(head_rot_deg[2]),
        )
    return new[0] if new else None


_PLY_TYPE_TO_NUMPY = {
    "float": "<f4", "float32": "<f4",
    "double": "<f8", "float64": "<f8",
    "uchar": "<u1", "uint8": "<u1",
    "char": "<i1", "int8": "<i1",
    "ushort": "<u2", "uint16": "<u2",
    "short": "<i2", "int16": "<i2",
    "uint": "<u4", "uint32": "<u4",
    "int": "<i4", "int32": "<i4",
}


def read_ply_hair(path, n_strands, n_points):
    """Return an (n_strands, n_points, 3) float32 numpy array of strand points."""
    with open(path, "rb") as f:
        data = f.read()
    head_end = data.find(b"end_header\n") + len(b"end_header\n")
    header = data[:head_end].decode(errors="replace")
    if "format binary_little_endian" not in header:
        raise RuntimeError(f"Only binary_little_endian PLY supported. Header:\n{header}")
    nv_match = re.search(r"element vertex (\d+)", header)
    if not nv_match:
        raise RuntimeError("Could not find vertex count in PLY header")
    nv = int(nv_match.group(1))
    expected = n_strands * n_points
    if nv != expected:
        raise RuntimeError(f"Vertex count {nv} != n_strands*n_points = {expected}")

    body_props = []
    in_vertex = False
    for line in header.splitlines():
        s = line.strip()
        if s.startswith("element vertex"):
            in_vertex = True; continue
        if s.startswith("element") and in_vertex:
            break
        if in_vertex and s.startswith("property"):
            parts = s.split()
            body_props.append((parts[1], parts[2]))

    dtype_fields = []
    for ptype, pname in body_props:
        np_t = _PLY_TYPE_TO_NUMPY.get(ptype)
        if np_t is None:
            raise RuntimeError(f"Unsupported PLY property type: {ptype}")
        dtype_fields.append((pname, np_t))
    dtype = np.dtype(dtype_fields)

    record_size = dtype.itemsize
    body = np.frombuffer(data, dtype=dtype, count=nv, offset=head_end)
    if {"x", "y", "z"}.difference(body.dtype.names):
        raise RuntimeError(f"PLY missing x/y/z; got fields {body.dtype.names}")

    xyz = np.stack([body["x"], body["y"], body["z"]], axis=-1).astype(np.float32)
    return xyz.reshape(n_strands, n_points, 3)


def build_hair_batched(strands, radius, materials, scene, hair_parent, strands_per_object):
    """Build hair curves. `materials` is a list of materials; if length > 1 each
    spline is assigned a rotating material slot by strand index."""
    n = strands.shape[0]
    n_points = strands.shape[1]
    n_batches = (n + strands_per_object - 1) // strands_per_object
    n_mats = len(materials)
    print(f"[info] building {n} strands x {n_points} pts across {n_batches} curve objects ({n_mats} materials)")

    xyzw = np.empty((n, n_points, 4), dtype=np.float32)
    xyzw[..., :3] = strands
    xyzw[..., 3] = 1.0

    for b in range(n_batches):
        lo = b * strands_per_object
        hi = min(n, lo + strands_per_object)
        cu = bpy.data.curves.new(f"HairBatch_{b:03d}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = radius
        cu.bevel_resolution = 1
        cu.use_fill_caps = True
        for m in materials:
            cu.materials.append(m)
        for s_idx in range(lo, hi):
            spline = cu.splines.new("POLY")
            spline.points.add(n_points - 1)
            spline.points.foreach_set("co", xyzw[s_idx].ravel())
            if n_mats > 1:
                spline.material_index = s_idx % n_mats
        obj = bpy.data.objects.new(f"Hair_{b:03d}", cu)
        scene.collection.objects.link(obj)
        if hair_parent is not None:
            obj.parent = hair_parent
        print(f"[batch {b+1}/{n_batches}] linked strands {lo}..{hi-1}")


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    reset_scene()
    scene = bpy.context.scene
    configure_render(scene, args)
    build_world(scene, args.bg_color)

    mesh_mat = make_mesh_material()
    if args.rainbow:
        hair_materials = make_rainbow_materials(max(1, args.rainbow_palette))
    else:
        hair_materials = [make_hair_material(args.hair_color)]

    head_obj = import_head(args.head_ply, mesh_mat, args.head_rot)
    if head_obj is None:
        raise RuntimeError("Failed to import head PLY")
    bpy.context.view_layer.update()

    build_camera(scene, args.cam_loc, args.target_loc)
    build_lights(scene)

    hair_parent = bpy.data.objects.new("HairRoot", None)
    hair_parent.rotation_euler = (
        math.radians(args.hair_rot[0]),
        math.radians(args.hair_rot[1]),
        math.radians(args.hair_rot[2]),
    )
    scene.collection.objects.link(hair_parent)

    print(f"[info] reading hair PLY: {args.hair_ply}")
    strands = read_ply_hair(args.hair_ply, args.n_strands, args.n_points)
    print(f"[info] loaded {len(strands)} strands x {len(strands[0])} points")

    build_hair_batched(strands, args.strand_radius, hair_materials, scene, hair_parent,
                       args.strands_per_object)

    out_path = os.path.join(args.output_dir, args.output_name)
    scene.render.filepath = out_path
    print(f"[render] -> {out_path}")
    bpy.ops.render.render(write_still=True)
    print("[done]")


if __name__ == "__main__":
    main()
