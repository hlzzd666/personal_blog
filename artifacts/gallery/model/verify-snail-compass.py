import bpy, json, struct
from pathlib import Path
from mathutils import Vector
root=Path(r'D:\codex-test\personal_blog')
for name in ['den-den-mushi','log-pose']:
    file=root/'web/public/gallery/artifacts'/(name+'.glb')
    raw=file.read_bytes()
    magic,version,length=struct.unpack('<III',raw[:12]);assert (magic,version,length)==(0x46546C67,2,len(raw))
    chunk_size,chunk_type=struct.unpack('<II',raw[12:20]);assert chunk_type==0x4E4F534A
    doc=json.loads(raw[20:20+chunk_size]);assert len(doc['images'])==2
    assert all('bufferView' in image and 'uri' not in image for image in doc['images'])
    assert 'KHR_materials_transmission' not in doc.get('extensionsUsed',[])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(file))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    coords=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    low=[min(v[i] for v in coords) for i in range(3)]; high=[max(v[i] for v in coords) for i in range(3)]
    assert abs(low[2])<.0001,low
    assert abs(low[0]+high[0])<.0001 and abs(low[1]+high[1])<.0001,(low,high)
    triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
    assert triangles<70000 and len(raw)<2000000
    report_path=root/'artifacts/gallery/model'/(name+'-report.json')
    report=json.loads(report_path.read_text('utf-8'))
    report.update({'glb_container_valid':True,'glb_reimport_verified':True,'imported_triangles':triangles,'imported_mesh_count':len(meshes),'embedded_textures':len(doc['images']),'imported_floor_z':round(low[2],7)})
    report_path.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print('VALIDATED',name,triangles,len(meshes),low,high)
