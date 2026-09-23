"""导入和道一文字并制作双层展架：blender -b -t 4 --python 本文件。"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/gallery/model'
PUBLIC = ROOT / 'web/public/gallery/artifacts/wado.glb'


def read_glb(path):
    raw = path.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    return raw, json.loads(raw[20:20 + size])


def texture_hashes(raw, document):
    binary = raw[28 + struct.unpack_from('<I', raw, 12)[0]:]
    hashes = []
    for image in document['images']:
        view = document['bufferViews'][image['bufferView']]
        start = view.get('byteOffset', 0)
        hashes.append(hashlib.sha256(binary[start:start + view['byteLength']]).hexdigest())
    return sorted(hashes)


def bounds(objects):
    points = [o.matrix_world @ v.co for o in objects for v in o.data.vertices]
    low = Vector([min(p[i] for p in points) for i in range(3)])
    high = Vector([max(p[i] for p in points) for i in range(3)])
    return low, high


def material(name, color, roughness):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    return mat


def box(name, location, dimensions, mat, bevel=.003):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new('柔化木架边缘', 'BEVEL')
        mod.width, mod.segments = bevel, 3
        bpy.ops.object.modifier_apply(modifier=mod.name)
        mod = obj.modifiers.new('加权法线', 'WEIGHTED_NORMAL')
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def section_bottom(objects, x):
    """在支架所在截面取真实网格底面，避免依据包围盒造成悬空。"""
    intersections = []
    for obj in objects:
        vertices = [obj.matrix_world @ v.co for v in obj.data.vertices]
        for edge in obj.data.edges:
            a, b = (vertices[i] for i in edge.vertices)
            if min(a.x, b.x) <= x <= max(a.x, b.x) and abs(b.x - a.x) > 1e-8:
                intersections.append(a.lerp(b, (x - a.x) / (b.x - a.x)))
    assert intersections, f'支架截面没有模型：{x}'
    return min(p.z for p in intersections)


def join_materials():
    groups = {}
    for obj in list(bpy.context.scene.objects):
        if obj.type == 'MESH':
            groups.setdefault(obj.data.materials[0], []).append(obj)
    result = []
    for mat, objects in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()
        objects[0].name = mat.name
        result.append(objects[0])
    return result


def preview(objects):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.world = bpy.data.worlds.new('仅预览使用的摄影棚')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.19, .22, .25, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .55
    ground_mat = material('preview-only-ground', (.075, .09, .095), .8)
    box('preview-only-ground', (0, 0, -.025), (200, 200, .05), ground_mat, 0)
    for name, loc, power, size in [('Key', (-1.5, -2, 3), 320, 3), ('Fill', (1, -3, 1), 140, 2), ('Rim', (0, 2, 2), 260, 2)]:
        data = bpy.data.lights.new(name, 'AREA')
        data.energy, data.size = power, size
        obj = bpy.data.objects.new(name, data)
        scene.collection.objects.link(obj)
        obj.location = loc
        obj.rotation_euler = (Vector((0, 0, .2)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    data = bpy.data.cameras.new('PreviewCamera')
    camera = bpy.data.objects.new('PreviewCamera', data)
    scene.collection.objects.link(camera)
    data.type = 'ORTHO'
    data.ortho_scale = 1.65
    camera.location = (.38, -3.1, 1.2)
    camera.rotation_euler = (Vector((0, 0, .23)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = camera
    scene.view_settings.view_transform = 'AgX'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(OUT / 'imported-wado-preview.png')
    bpy.ops.render.render(write_still=True)
    # 正面验证上下间距、刀架接触及总体长轴方向。
    camera.location = (0, -3, .25)
    camera.rotation_euler = (Vector((0, 0, .25)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(OUT / 'imported-wado-front-preview.png')
    bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=OUT / 'downloads/katana_-_wado_ichimonji.glb')
    parser.add_argument('--skip-preview', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    original, document = read_glb(args.source)
    assert document['asset']['extras']['title'] == 'Katana - Wado Ichimonji', '请使用本次确认的源模型'
    original_sha = hashlib.sha256(original).hexdigest()
    original_triangles = sum(document['accessors'][p['indices']]['count'] // 3 for m in document['meshes'] for p in m['primitives'])
    OUT.mkdir(parents=True, exist_ok=True)
    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.import_scene.gltf(filepath=str(args.source))
    imported = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    original_low, original_high = bounds(imported)
    textures = [{'name': i.name, 'width': i.size[0], 'height': i.size[1]} for i in bpy.data.images]
    # 原文件已是 2048 图集和低面数模型；直接保留，不做有损降面或重烘焙。
    for obj in imported:
        obj.data.transform(obj.matrix_world)
        obj.parent = None
        obj.matrix_world = Matrix.Identity(4)
        for layer in list(obj.data.uv_layers)[1:]:
            obj.data.uv_layers.remove(layer)
    for obj in list(bpy.context.scene.objects):
        if obj.type != 'MESH':
            bpy.data.objects.remove(obj, do_unlink=True)
    sword = [o for o in imported if not o.name.startswith('scabbard')]
    scabbard = [o for o in imported if o.name.startswith('scabbard')]
    assert len(sword) == 18 and len(scabbard) == 4, '源模型结构变化，需要重新确认展示安排'
    for obj in sword:
        obj.data.transform(Matrix.Translation((0, 0, .34)))
    for obj in scabbard:
        obj.data.transform(Matrix.Translation((-.035, 0, .255)))
    wood = material('ebonized-wood-display-stand', (.017, .010, .006), .36)
    felt = material('warm-brown-protective-felt', (.085, .041, .018), .94)
    box('continuous-low-stand-base', (.045, .023, .019), (1.10, .22, .038), wood, .009)
    box('rear-stand-crossbar', (.105, .063, .090), (.69, .027, .025), wood, .004)
    contacts = []
    for x in [-.22, .43]:
        upper = section_bottom(sword, x)
        lower = section_bottom(scabbard, x)
        box('rear-upright', (x, .054, (upper + .038) / 2), (.036, .033, upper - .038), wood, .005)
        for label, bottom in [('blade', upper), ('saya', lower)]:
            box(label + '-support-arm', (x, .011, bottom - .013), (.032, .116, .018), wood, .003)
            box(label + '-protective-pad', (x, 0, bottom - .0038), (.033, .034, .008), felt, .001)
            box(label + '-front-retaining-tip', (x, -.043, bottom + .001), (.032, .012, .026), wood, .004)
            contacts.append({'part': label, 'x': x, 'surface_z_blender': round(bottom, 6), 'pad_overlap_m': .0002})
    objects = join_materials()
    low, high = bounds(objects)
    center = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    for obj in objects:
        obj.location -= center
    bpy.context.view_layer.update()
    low, high = bounds(objects)
    for obj in objects:
        obj['source_author'] = 'NRiza'
        obj['source_license'] = 'CC-BY-4.0'
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(PUBLIC), export_format='GLB', use_selection=True,
        export_yup=True, export_apply=True, export_texcoords=True, export_normals=True,
        export_materials='EXPORT', export_image_format='AUTO', export_cameras=False,
        export_lights=False, export_extras=True)
    exported, result = read_glb(PUBLIC)
    # glTF 的 asset 元数据不会从导入场景自动保留，显式写回来源与改编说明。
    result['asset']['extras'] = {**document['asset']['extras'], 'modifications': 'Retained original sword and scabbard meshes and 2048 PBR textures. Rearranged as a two-tier display, added an original wood stand with felt supports, removed unused UV channels, joined by material, grounded and centered.'}
    result['asset']['copyright'] = 'Katana - Wado Ichimonji by NRiza; CC BY 4.0'
    old_json_size = struct.unpack_from('<I', exported, 12)[0]
    binary_chunks = exported[20 + old_json_size:]
    json_bytes = json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    json_bytes += b' ' * (-len(json_bytes) % 4)
    exported = struct.pack('<III', 0x46546C67, 2, 20 + len(json_bytes) + len(binary_chunks)) + struct.pack('<II', len(json_bytes), 0x4E4F534A) + json_bytes + binary_chunks
    PUBLIC.write_bytes(exported)
    triangles = sum(result['accessors'][p['indices']]['count'] // 3 for m in result['meshes'] for p in m['primitives'])
    dimensions = high - low
    glb_dimensions = [dimensions.x, dimensions.z, dimensions.y]
    fit = min(2.09 / dimensions.x, .86 / dimensions.y, .82 / dimensions.z)
    report = {'asset': 'wado', 'blender': bpy.app.version_string,
        'source': {'file': str(args.source), 'sha256': original_sha, 'bytes': len(original), 'triangles': original_triangles,
            'dimensions_xyz_glb': [round((original_high - original_low)[i], 6) for i in [0, 2, 1]], **document['asset']['extras']},
        'result': {'file': str(PUBLIC.relative_to(ROOT)), 'sha256': hashlib.sha256(exported).hexdigest(), 'bytes': len(exported),
            'triangles': triangles, 'materials': len(result['materials']), 'draw_calls': sum(len(m['primitives']) for m in result['meshes']),
            'embedded_images': len(result['images']), 'dimensions_xyz_glb': [round(d, 6) for d in glb_dimensions],
            'min_y_glb': round(low.z, 8), 'max_y_glb': round(high.z, 6),
            'fit_scale': round(fit, 6), 'runtime_dimensions_xyz': [round(d * fit, 6) for d in glb_dimensions]},
        'texture_policy': '保留原始三张 2048 × 2048 PBR 图集；不降采样、不替换材质，导出前后贴图字节哈希完全一致。',
        'textures': textures, 'texture_sha256': texture_hashes(exported, result),
        'changes': ['保留原始刀、鞘网格、法线及所有可见纹理细节。', '刀在上、鞘在下，刀柄朝左，正面朝 GLB +Z。', '新增深色木质双层支架及四处毡垫，按网格截面计算接触高度。', '删除两个未使用 UV 通道并按材质合并为三个绘制调用。', '底面落在 GLB Y=0，X/Z 居中；所有贴图内嵌。'],
        'support_contacts_before_centering': contacts,
        'limitations': '用户提供的第三方同人模型；并非官方影视制作资产。保留作者原有刀身纹理和金属外观。'}
    assert triangles <= 100000 and len(exported) <= 8_000_000, report['result']
    assert abs(low.z) < 1e-6 and dimensions.x > dimensions.z > dimensions.y, report['result']
    assert all('bufferView' in i and 'uri' not in i for i in result['images'])
    assert all('uri' not in b for b in result['buffers'])
    assert 'KHR_materials_transmission' not in result.get('extensionsUsed', [])
    assert texture_hashes(original, document) == texture_hashes(exported, result), '原始贴图必须无损保留'
    assert hashlib.sha256(args.source.read_bytes()).hexdigest() == original_sha, '源文件不应变化'
    (OUT / 'imported-wado-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'imported-wado.blend'))
    if not args.skip_preview:
        preview(objects)
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
