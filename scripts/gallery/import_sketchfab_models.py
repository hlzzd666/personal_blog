"""将用户下载的草帽、果实与 Logo 整理为本地展馆资产；保留原始许可和可编辑源文件。"""
import argparse
import hashlib
import json
import shutil
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/gallery/model'
PUBLIC = ROOT / 'web/public/gallery/artifacts'
parser = argparse.ArgumentParser()
parser.add_argument('--source-dir', type=Path, default=OUT / 'downloads')
parser.add_argument('--render', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
OUT.mkdir(parents=True, exist_ok=True)
PUBLIC.mkdir(parents=True, exist_ok=True)
(OUT / 'downloads').mkdir(exist_ok=True)


def glb_json(raw):
    length = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + length]), length


def preserve_credit(path, original):
    raw = path.read_bytes()
    document, length = glb_json(raw)
    document['asset']['extras'] = original['asset'].get('extras', {}) | {
        'modifications': 'Normalized units and origin; static meshes combined by material. Original shape, colors and textures retained.'}
    credit = original['asset'].get('extras', {})
    document['asset']['copyright'] = f"{credit.get('title', '')} by {credit.get('author', '')}; {credit.get('license', '')}"
    encoded = json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    encoded += b' ' * (-len(encoded) % 4)
    tail = raw[20 + length:]
    path.write_bytes(struct.pack('<III', 0x46546C67, 2, 20 + len(encoded) + len(tail)) +
                     struct.pack('<II', len(encoded), 0x4E4F534A) + encoded + tail)


def bounds(objects):
    # 旋转后的局部包围盒会包含空角；用顶点求边界，保证合批前后原点一致。
    points = [o.matrix_world @ vertex.co for o in objects for vertex in o.data.vertices]
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    return low, high


for name, filename in [('straw-hat', 'luffys_straw_hat.glb'), ('gum-gum', 'gomu_gomu_no_mi.glb'), ('one-piece-logo', 'one_piece_logo.glb')]:
    source = args.source_dir / filename
    original_bytes = source.read_bytes()
    original, _ = glb_json(original_bytes)
    retained = OUT / 'downloads' / filename
    if source.resolve() != retained.resolve():
        shutil.copy2(source, retained)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.import_scene.gltf(filepath=str(source))
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    # 烘焙节点变换再统一尺寸，避免导出后把 Sketchfab 包装节点重复缩放。
    for obj in objects:
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
    low, high = bounds(objects)
    center = (low + high) / 2
    offset = Vector((-center.x, -center.y, -low.z))
    normalize = Matrix.Scale(1 / max(high - low), 4) @ Matrix.Translation(offset)
    for obj in objects:
        obj.data.transform(normalize @ obj.matrix_world)
        obj.matrix_world = Matrix.Identity(4)
    for obj in list(bpy.context.scene.objects):
        if obj.type != 'MESH':
            bpy.data.objects.remove(obj, do_unlink=True)
    # 这些源网格各自使用单材质；仅合并相同材质，保留 UV 和法线。
    batches = {}
    for obj in objects:
        assert len(obj.data.materials) == 1, obj.name
        batches.setdefault(obj.data.materials[0], []).append(obj)
    for material, batch in batches.items():
        bpy.ops.object.select_all(action='DESELECT')
        for obj in batch:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = batch[0]
        if len(batch) > 1:
            bpy.ops.object.join()
        bpy.context.object.name = f'{name}-{material.name}'
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.context.view_layer.update()
    low, high = bounds(objects)
    for obj in objects:
        obj.select_set(True)
    destination = PUBLIC / f'{name}.glb'
    bpy.ops.export_scene.gltf(filepath=str(destination), export_format='GLB', use_selection=True,
                              export_yup=True, export_cameras=False, export_lights=False)
    preserve_credit(destination, original)
    report = {'id': name, 'sourceFile': filename, 'sourceSha256': hashlib.sha256(original_bytes).hexdigest(),
              'sourceBytes': len(original_bytes), 'bytes': destination.stat().st_size,
              'triangles': sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objects),
              'drawCalls': len(objects), 'blenderBounds': [list(low), list(high)],
              'source': original['asset'].get('extras', {}),
              'changes': ['统一单位、中心与落地位置', '按材质合批', '保留原始外形、颜色及贴图']}
    (OUT / f'imported-{name}-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    bpy.ops.file.pack_all()
    # 检视灯光和相机不进入网页 GLB。
    scene = bpy.context.scene
    world = bpy.data.worlds.new('Studio')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.12, .16, .2, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .5
    scene.world = world
    aim = Vector((0, 0, (high.z - low.z) / 2))
    for position, energy in [((-2, -3, 4), 300), ((2, -1, 3), 150), ((0, 2, 3), 180)]:
        bpy.ops.object.light_add(type='AREA', location=position)
        lamp = bpy.context.object
        lamp.data.energy = energy
        lamp.data.size = 3
        lamp.rotation_euler = (aim - lamp.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.object.camera_add(location=(.07, -3, .4) if name == 'one-piece-logo' else (1.4, -3, 1.65))
    camera = bpy.context.object
    camera.rotation_euler = (aim - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 1.18 if name == 'one-piece-logo' else 1.45
    scene.camera = camera
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1100 if name == 'one-piece-logo' else 850
    scene.render.resolution_y = 450 if name == 'one-piece-logo' else 850
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(OUT / f'imported-{name}-preview.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f'imported-{name}.blend'))
    if args.render:
        bpy.ops.render.render(write_still=True)
    print(json.dumps(report, ensure_ascii=True), flush=True)
