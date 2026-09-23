"""校验展品 GLB 完整性、贴图封装、容量与可编辑源文件。无需 Blender。"""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'web/public/gallery/artifacts'
SOURCE = ROOT / 'artifacts/gallery/model'
report = []
budgets = {
    'straw-hat': (100_000, 2_000, 'imported-straw-hat'),
    'den-den-mushi': (2_200_000, 75_000, 'den-den-mushi'),
    'log-pose': (1_000_000, 30_000, 'log-pose'),
    'gum-gum': (250_000, 7_000, 'imported-gum-gum'),
    'wado': (8_000_000, 20_000, 'imported-wado'),
    'one-piece-logo': (5_500_000, 90_000, 'imported-one-piece-logo'),
}
for name, (byte_budget, triangle_budget, source_name) in budgets.items():
    path = ASSETS / f'{name}.glb'
    raw = path.read_bytes()
    magic, version, length = struct.unpack_from('<III', raw)
    assert magic == 0x46546C67 and version == 2 and length == len(raw), name
    size, chunk_type = struct.unpack_from('<II', raw, 12)
    assert chunk_type == 0x4E4F534A
    document = json.loads(raw[20:20+size])
    assert document.get('meshes') and document.get('materials'), name
    images = document.get('images', [])
    assert (images or name == 'one-piece-logo') and all('bufferView' in image and 'uri' not in image for image in images), name
    assert all('uri' not in buffer for buffer in document['buffers']), name
    assert 'KHR_materials_transmission' not in document.get('extensionsUsed', []), name
    assert (SOURCE / f'{source_name}.blend').is_file(), name
    if source_name.startswith('imported-'):
        credit = document['asset'].get('extras', {})
        assert all(credit.get(key) for key in ['author', 'license', 'source']), name
        if name == 'straw-hat':
            assert 'BY-NC' in credit['license'], '草帽的非商业限制必须保留'
    primitives = [primitive for mesh in document['meshes'] for primitive in mesh['primitives']]
    triangles = sum(document['accessors'][primitive['indices']]['count'] // 3 for primitive in primitives)
    assert triangles < triangle_budget and len(primitives) <= 12 and len(raw) < byte_budget, name
    report.append({'id': name, 'bytes': len(raw), 'triangles': triangles, 'drawCalls': len(primitives),
                   'embeddedImages': len(images), 'sha256': hashlib.sha256(raw).hexdigest()})
assert sum(asset['bytes'] for asset in report) < 17_000_000
(SOURCE / 'artifact-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
