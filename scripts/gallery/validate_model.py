"""Independently reopen/render the saved scene, then import and inspect the GLB."""
import bpy
import hashlib
import json
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/gallery/model'
blend=OUT/'旗舰船舱展馆.blend'
glb=ROOT/'web/public/gallery/flagship/flagship.glb'
bpy.ops.wm.open_mainfile(filepath=str(blend))
scene=bpy.context.scene
assert scene.camera is not None
assert len([obj for obj in scene.objects if obj.type=='MESH'])>20
missing=[image.name for image in bpy.data.images if image.source=='FILE' and not image.packed_file and not Path(bpy.path.abspath(image.filepath)).is_file()]
assert not missing,missing
packed=len([image for image in bpy.data.images if image.packed_file])
scene.render.resolution_x=640;scene.render.resolution_y=640;scene.cycles.samples=24
scene.render.filepath=str(OUT/'reopen-validation.png')
bpy.ops.render.render(write_still=True)
raw=glb.read_bytes()
magic,version,length=struct.unpack('<III',raw[:12])
assert magic==0x46546C67 and version==2 and length==len(raw)
chunk_size,chunk_type=struct.unpack('<II',raw[12:20])
assert chunk_type==0x4E4F534A
document=json.loads(raw[20:20+chunk_size])
names={node.get('name') for node in document['nodes']}
assert {'CabinBay','BowDeck','SternDeck','ExhibitFrame'}<=names
assert all('uri' not in image for image in document.get('images',[]))
assert any('normalTexture' in material for material in document['materials'])
assert any('metallicRoughnessTexture' in material.get('pbrMetallicRoughness',{}) for material in document['materials'])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(glb))
meshes=[obj for obj in bpy.context.scene.objects if obj.type=='MESH']
assert meshes
triangles=sum(sum(len(poly.vertices)-2 for poly in obj.data.polygons) for obj in meshes)
report={'blender':bpy.app.version_string,'blend_reopened':True,'rendered':'reopen-validation.png','missing_images':missing,'packed_images':packed,'glb_imported':True,'modules':['CabinBay','BowDeck','SternDeck','ExhibitFrame'],'mesh_count':len(meshes),'source_triangles':triangles,'embedded_glb_images':len(document.get('images',[])),'bytes':len(raw),'files':{path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in [blend,glb,OUT/'preview.png',OUT/'reopen-validation.png']}}
(OUT/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False),flush=True)
