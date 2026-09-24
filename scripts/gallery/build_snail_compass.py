"""用 Blender 生成可编辑的电话虫和腕式记录指针，直接导出浏览器所用 GLB。"""
import bpy
import math
import json
import random
import struct
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/gallery/model'
PUBLIC = ROOT / 'web/public/gallery/artifacts'
OUT.mkdir(parents=True, exist_ok=True)
PUBLIC.mkdir(parents=True, exist_ok=True)
bpy.context.preferences.filepaths.save_version = 0
TAU = math.tau


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0


def material(name, color, metallic=0, roughness=.5, alpha=1, texture=None):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, alpha)
    mat.use_nodes = True
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, alpha)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Alpha'].default_value = alpha
    if alpha < 1:
        mat.surface_render_method = 'BLENDED'
        mat.use_transparency_overlap = False
        mat.use_backface_culling = True
    if texture:
        # 直接生成可打包的像素图，避免仅在 Blender 中生效的程序节点。
        size = 256
        img = bpy.data.images.new(name + ' pigment', width=size, height=size)
        rng = random.Random(19)
        pixels = []
        for y in range(size):
            for x in range(size):
                noise = rng.random() - .5
                if texture == 'wood':
                    grain = math.sin(x * .6 + math.sin(y * .027) * 3 + math.sin(x * .07) * 2)
                    tint = 1 + grain * .10 + noise * .06
                elif texture == 'skin':
                    tint = 1 + noise * .065 + math.sin(x * .12) * math.cos(y * .13) * .02
                else:
                    tint = 1 + noise * .20 + math.sin(y * .11) * .025
                pixels.extend([min(1, max(0, c * tint)) for c in color] + [1])
        img.pixels.foreach_set(pixels)
        img.pack()
        tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = img
        mat.node_tree.links.new(tex.outputs['Color'], p.inputs['Base Color'])
    return mat


def finish(obj, name, mat):
    obj.name = name
    obj.data.materials.append(mat)
    if obj.type == 'MESH':
        for face in obj.data.polygons:
            face.use_smooth = True
    return obj


def sphere(name, loc, scale, mat, segments=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    obj = finish(bpy.context.object, name, mat)
    obj.scale = scale
    return obj


def box(name, loc, size, mat, bevel=.015):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = finish(bpy.context.object, name, mat)
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        modifier = obj.modifiers.new('柔和边缘', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 3
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj


def curve(name, points, radius, mat, cyclic=False, resolution=8):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 2
    data.bevel_depth = radius
    data.bevel_resolution = 2
    data.use_fill_caps = True
    spline = data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (*co, 1)
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(mat)
    return obj


def torus(name, loc, radius, tube, mat, normal=(0, 0, 1), major=48):
    bpy.ops.mesh.primitive_torus_add(major_segments=major, minor_segments=8,
        major_radius=radius, minor_radius=tube, location=loc)
    obj = finish(bpy.context.object, name, mat)
    obj.rotation_euler = Vector(normal).to_track_quat('Z', 'Y').to_euler()
    return obj


def rod(name, a, b, radius, mat, vertices=32, radius_top=None):
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
        radius2=radius if radius_top is None else radius_top,
        depth=(b-a).length, location=(a+b)/2)
    obj = finish(bpy.context.object, name, mat)
    obj.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    return obj


def mesh(name, vertices, faces, mat, uv=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    finish(obj, name, mat)
    if uv:
        layer = data.uv_layers.new(name='UVMap')
        for polygon in data.polygons:
            for loop in polygon.loop_indices:
                layer.data[loop].uv = uv[data.loops[loop].vertex_index]
    return obj


def lathe(name, profile, mat, location=(0, 0, 0), count=64):
    verts, faces, uv = [], [], []
    for j, (r, z) in enumerate(profile):
        for i in range(count):
            a = TAU * i / count
            verts.append((location[0]+r*math.cos(a), location[1]+r*math.sin(a), location[2]+z))
            uv.append((i/count, j/(len(profile)-1)))
    for j in range(len(profile)-1):
        for i in range(count):
            a, b = j*count+i, j*count+(i+1)%count
            faces.append((a,b,b+count,a+count))
    faces += [tuple(reversed(range(count))), tuple(range((len(profile)-1)*count, len(profile)*count))]
    return mesh(name, verts, faces, mat, uv)


def organic_join(objects, name, mat):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    obj = bpy.context.object
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    remesh = obj.modifiers.new('连贯软体轮廓', 'REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = .010
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    smooth = obj.modifiers.new('皮肤平滑', 'SMOOTH')
    smooth.factor = 1.3
    smooth.iterations = 6
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    decimate = obj.modifiers.new('浏览器面数预算', 'DECIMATE')
    decimate.ratio = .40
    bpy.ops.object.modifier_apply(modifier=decimate.name)
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    obj.name = name
    for poly in obj.data.polygons:
        poly.use_smooth = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=.025)
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj


def snail():
    skin = material('Telephone snail · muted jade skin', (.39,.57,.25), roughness=.62, texture='skin')
    lip = material('Telephone snail · dark olive folds', (.17,.28,.075), roughness=.63)
    shell = material('Telephone snail · warm ochre shell', (.52,.255,.07), roughness=.34, texture='wood')
    seam = material('Telephone snail · shell whorl crease', (.255,.104,.035), roughness=.47)
    black = material('Telephone snail · black bakelite', (.018,.022,.021), roughness=.27)
    eye = material('Telephone snail · ivory eye', (.95,.93,.79), roughness=.26)
    brass = material('Telephone snail · dial brass', (.59,.36,.10), .65, .32)
    pupil = material('Telephone snail · pupils and mouth', (.015,.024,.012), roughness=.44)

    pieces = [sphere('Soft foot', (0,.02,.104), (.335,.52,.10), skin),
        sphere('Tapered tail', (0,.34,.096), (.25,.285,.088), skin),
        sphere('Soft body', (0,-.10,.21), (.245,.31,.18), skin),
        sphere('Rising neck', (0,-.34,.35), (.18,.20,.265), skin),
        sphere('Snail face', (0,-.405,.54), (.205,.17,.165), skin)]
    pieces[3].rotation_euler.x = -.24
    for side in [-1, 1]:
        stalk = sphere('Organic eye stalk', (side*.165,-.412,.746), (.041,.043,.153), skin)
        stalk.rotation_euler.y = side*.29
        pieces.append(stalk)
        pieces.append(sphere('Stalk transition', (side*.12,-.405,.625), (.061,.075,.10), skin))
    organic_join(pieces, 'Sculpted continuous snail foot neck and eyestalks', skin)
    # 足缘皱褶连续绕身体一周，降低球体拼接感。
    curve('Soft sole seam', [(.31*math.cos(a),.035+.49*math.sin(a),.065+.009*math.sin(3*a))
        for a in [TAU*i/100 for i in range(100)]], .006, lip, True)
    sphere('Rounded coiled shell volume', (0,.16,.44), (.315,.335,.326), shell, 48, 28)
    # 螺线沿双凸壳体表面上升，壳纹属于完整壳体，非附着圆片。
    for side in [-1,1]:
        pts = []
        for i in range(220):
            t=i/219
            theta=-.4+TAU*1.75*t
            r=.022+.271*t
            x=side*(.315*math.sqrt(max(.01,1-(r/.34)**2))+.003)
            pts.append((x,.16+r*math.sin(theta),.44+r*math.cos(theta)))
        curve('Embedded continuous shell spiral', pts, .009, seam)
        curve('Shell spiral lip', [(x+side*.003,y+.009,z+.005) for x,y,z in pts], .005, shell)
    for side in [-1,1]:
        cx, cy, cz = side*.195, -.425, .865
        sphere('Raised ivory eye', (cx,cy,cz), (.094,.079,.10), eye)
        sphere('Sleepy dark pupil', (cx-side*.006,cy-.072,cz-.022), (.026,.012,.039), pupil, 24, 16)
        sphere('Small reflected light', (cx-side*.011,cy-.084,cz-.010), (.006,.004,.008), eye, 12,8)
        # 眼睑覆盖上半眼球，保留原作普通电话虫的慵懒表情。
        vertices, faces = [], []
        for j in range(9):
            phi=(math.pi/2+.16)*j/8
            for i in range(33):
                theta=TAU*i/32
                vertices.append((cx+.098*math.sin(phi)*math.cos(theta),
                    cy+.083*math.sin(phi)*math.sin(theta),cz+.103*math.cos(phi)))
        for j in range(8):
            for i in range(32):
                a=j*33+i
                faces.append((a,a+1,a+34,a+33))
        mesh('Drooping upper eyelid', vertices, faces, skin)
        curve('Drooping eyelid edge', [(cx+.098*math.cos(t),cy-.082*math.sin(t),cz-.016+.009*math.cos(t))
            for t in [math.pi*i/32 for i in range(33)]], .006, lip)
    curve('Mouth crease', [(-.105+.21*t,-.568-.014*math.sin(t*math.pi),.476-.015*math.sin(t*math.pi))
        for t in [i/40 for i in range(41)]], .009, pupil)
    curve('Soft lower lip', [(-.095+.19*t,-.579-.010*math.sin(t*math.pi),.455-.012*math.sin(t*math.pi))
        for t in [i/40 for i in range(41)]], .012, skin)

    box('Telephone cradle bed', (0,.16,.75), (.45,.22,.055), black, .025)
    for side in [-1,1]:
        box('Receiver cradle fork', (side*.19,.16,.792), (.075,.17,.052), black, .017)
    # 圆润弯曲的听筒和扩口耳罩，避免方块拼接的轮廓。
    handle = [(x,.16,.900+.055*(abs(x)/.225)**2) for x in [-.225+.45*i/64 for i in range(65)]]
    curve('Curved telephone handset', handle, .038, black)
    for side in [-1,1]:
        sphere('Rounded handset shoulder',(side*.225,.16,.950),(.043,.040,.042),black,24,12)
        lathe('Flared receiver earpiece', [(.063,.805),(.079,.813),(.083,.835),(.075,.88),(.045,.915),(.035,.956)], black,
            location=(side*.235,.16,0), count=40)
        torus('Receiver earpiece seam', (side*.235,.16,.824), .079,.004, seam, major=40)
        for j in range(7):
            theta=TAU*j/7
            sphere('Receiver speaker aperture', (side*.235+.045*math.cos(theta),.16+.045*math.sin(theta),.806), (.006,.006,.003), pupil,12,8)
    # 拨号盘嵌在壳体的前侧斜面中，黑色底座大半沉入壳内。
    normal=Vector((.76,-.59,.27)).normalized()
    center=Vector((.256,-.052,.48))
    u=Vector((0,0,1)).cross(normal).normalized()
    v=normal.cross(u)
    rod('Inset dial black housing', center-normal*.025, center+normal*.024, .157, black, 64)
    rod('Brass rotary dial plate', center+normal*.025, center+normal*.034, .138, brass, 64)
    torus('Dial edge trim', center+normal*.036,.141,.005,black,normal,64)
    for i in range(10):
        a=TAU*i/10
        p=center+normal*.040+.105*(u*math.cos(a)+v*math.sin(a))
        rod('Rotary finger well',p-normal*.003,p+normal*.002,.021,pupil,16)
        torus('Finger hole bevel',p+normal*.003,.020,.0025,brass,normal,20)
    rod('Dial centre label',center+normal*.036,center+normal*.041,.053,eye,40)
    torus('Dial centre label rim',center+normal*.043,.054,.004,black,normal,40)
    for j in [-1,0,1]:
        a=center+normal*.045+v*(j*.013)-u*.03
        b=center+normal*.045+v*(j*.013)+u*.03
        curve('Dial label inscription',[a,b],.0015,pupil)
    curve('Handset cord leader',[(.25,.18,.9),(.325,.18,.85),(.38,.14,.75)],.009,black)
    pts=[]
    for i in range(300):
        t=i/299
        pts.append((.366+.024*math.cos(t*TAU*17),.14-.25*t+.024*math.sin(t*TAU*17),.755-.31*t))
    curve('Coiled telephone cord',pts,.0065,black)
    curve('Cord to dial',[(.366,-.11,.445),(.345,-.18,.415),(.306,-.14,.45)],.009,black)


def log_pose():
    wood=material('Log Pose · warm carved cherrywood',(.39,.16,.055),roughness=.40,texture='wood')
    leather=material('Log Pose · aged cognac leather',(.21,.074,.028),roughness=.78,texture='leather')
    edge=material('Log Pose · dark leather edge paint',(.063,.025,.015),roughness=.65)
    brass=material('Log Pose · aged brass fittings',(.61,.40,.14),metallic=.76,roughness=.31)
    dark=material('Log Pose · dark steel needle tail',(.045,.065,.07),metallic=.58,roughness=.29)
    red=material('Log Pose · vermilion magnetic pointer',(.69,.035,.018),metallic=.15,roughness=.32)
    stitch=material('Log Pose · waxed linen stitches',(.71,.55,.34),roughness=.87)
    glass=material('Log Pose · clear spherical glass',(.60,.85,.94),roughness=.12,alpha=.105)
    gleam=material('Log Pose · subtle glass highlights',(.91,.98,1),roughness=.15,alpha=.32)

    # 厚度明确的闭合皮革腕带，弧线贴合手腕；底座跨接腕带顶部。
    vertices,faces,uv=[],[],[]
    n=96
    for i in range(n):
        a=TAU*i/n
        for x,offset in [(-.10,-.012),(.10,-.012),(.10,.012),(-.10,.012)]:
            vertices.append((x,(.272+offset)*math.cos(a),.18+(.163+offset)*math.sin(a)))
            uv.append((x/.20+.5,i/n))
    for i in range(n):
        for k in range(4):
            faces.append((i*4+k,i*4+(k+1)%4,((i+1)%n)*4+(k+1)%4,((i+1)%n)*4+k))
    band=mesh('Closed curved leather wristband',vertices,faces,leather,uv)
    bevel=band.modifiers.new('Rounded strap cut edges','BEVEL');bevel.width=.005;bevel.segments=2
    bpy.context.view_layer.objects.active=band
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    for side in [-1,1]:
        curve('Leather edge piping',[(side*.098,.286*math.cos(a),.18+.177*math.sin(a))
            for a in [TAU*i/96 for i in range(96)]],.003,edge,True)
        for i in range(48):
            a=TAU*i/48
            curve('Individual saddle stitch',[(side*.079,.287*math.cos(t),.18+.178*math.sin(t))
                for t in [a,a+.04,a+.08]],.0023,stitch)
    for side in [-1,1]:
        rod('Strap attachment pin',(side*.093,-.13,.335),(side*.093,.13,.335),.012,brass,20)
    # 闭合表扣和活动扣针，尺寸与腕带相符。
    for x in [-.117,.117]:
        curve('Buckle long rail',[(x,-.285,.118),(x,-.294,.235)],.010,brass)
    for z in [.118,.235]:
        curve('Buckle curved end',[(-.117,-.288,z),(-.105,-.30,z),(0,-.304,z),(.105,-.30,z),(.117,-.288,z)],.010,brass)
    rod('Buckle central spindle',(-.11,-.299,.172),(.11,-.299,.172),.006,brass,16)
    curve('Buckle tongue',[(0,-.301,.172),(0,-.313,.216),(0,-.306,.237)],.005,brass)
    for z in [.10,.13,.16]:
        sphere('Strap punched hole',(0,-.289,z),(.007,.003,.010),edge,16,8)
    lathe('Sculpted wooden instrument base',[(.205,.317),(.237,.329),(.251,.346),(.253,.370),(.242,.395),(.224,.408),(.018,.408)],wood)
    torus('Bottom brass binding',(0,0,.335),.239,.010,brass)
    torus('Upper brass glass seat',(0,0,.405),.220,.009,brass)
    torus('Glass mounting inner gasket',(0,0,.410),.203,.006,edge)
    for i in range(8):
        a=TAU*i/8
        sphere('Recessed mounting screw',(.233*math.cos(a),.233*math.sin(a),.395),(.010,.010,.004),brass,16,8)
        curve('Screw slot',[(.233*math.cos(a)-.006,.233*math.sin(a),.399),(.233*math.cos(a)+.006,.233*math.sin(a),.399)],.0014,edge)

    # 完整透明球体中的悬浮双尖磁针，无普通指南针刻度盘。
    center=Vector((0,0,.596))
    sphere('Complete transparent glass orb',center,(.247,.247,.247),glass,64,40)
    direction=Vector((.51,.10,.85)).normalized()
    u=direction.cross(Vector((0,1,0))).normalized()
    v=direction.cross(u)
    for sign,mat in [(1,red),(-1,dark)]:
        tip=center+direction*(.194*sign)
        base=center+direction*(.010*sign)
        vertices=[tuple(tip)]+[tuple(base+u*.024*math.cos(TAU*i/4)+v*.017*math.sin(TAU*i/4)) for i in range(4)]
        mesh('Floating red pole' if sign==1 else 'Floating dark pole',vertices,[(0,1,2),(0,2,3),(0,3,4),(0,4,1),(4,3,2,1)],mat)
    sphere('Needle centre bearing',center,(.033,.021,.024),brass,24,16)
    torus('Suspension bearing loop',center,.028,.004,brass,(0,1,0),32)
    # 透明球本身保持低覆盖，仅用两段细弧补足展馆灯光下的玻璃轮廓。
    for angle,phi0,phi1 in [(-2.25,.32,1.25),(-1.12,.43,.75)]:
        points=[]
        for i in range(42):
            phi=phi0+(phi1-phi0)*i/41
            points.append((.249*math.sin(phi)*math.cos(angle),.249*math.sin(phi)*math.sin(angle),.596+.249*math.cos(phi)))
        curve('Curved glass reflection',points,.0035,gleam)


def export_asset(asset_id):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.convert(target='MESH')
    meshes=[obj for obj in bpy.context.scene.objects if obj.type=='MESH']
    for obj in meshes:
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    # 按材质合并后，数百个细节不会变成数百次绘制调用。
    groups={}
    for obj in meshes:
        groups.setdefault(obj.data.materials[0].name,[]).append(obj)
    for name,objects in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects: obj.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]
        if len(objects)>1:
            bpy.ops.object.join()
        bpy.context.object.name=asset_id+' | '+name
    meshes=[obj for obj in bpy.context.scene.objects if obj.type=='MESH']
    coords=[obj.matrix_world@Vector(corner) for obj in meshes for corner in obj.bound_box]
    low=Vector(tuple(min(v[i] for v in coords) for i in range(3)))
    high=Vector(tuple(max(v[i] for v in coords) for i in range(3)))
    offset=Vector((-(low.x+high.x)/2,-(low.y+high.y)/2,-low.z))
    for obj in meshes: obj.location+=offset
    bpy.ops.object.select_all(action='SELECT')
    path=PUBLIC/(asset_id+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,
        export_apply=True,export_yup=True,export_image_format='AUTO',export_extras=False)
    raw=path.read_bytes()
    magic,version,length=struct.unpack('<III',raw[:12])
    assert magic==0x46546C67 and version==2 and length==len(raw)
    chunk_size,chunk_type=struct.unpack('<II',raw[12:20])
    assert chunk_type==0x4E4F534A
    document=json.loads(raw[20:20+chunk_size])
    assert len(document.get('images',[]))==2
    assert all('bufferView' in image and 'uri' not in image for image in document['images'])
    assert 'KHR_materials_transmission' not in document.get('extensionsUsed',[])
    if asset_id=='log-pose':
        assert any(m.get('alphaMode')=='BLEND' for m in document['materials'])
    triangles=sum(sum(len(p.vertices)-2 for p in obj.data.polygons) for obj in meshes)
    report={'asset':asset_id,'triangles':triangles,'materials':len(groups),'mesh_draw_calls':len(meshes),
        'dimensions_m':[round(x,4) for x in high-low],'bytes':path.stat().st_size,
        'embedded_textures':len(document['images']),'glb_container_valid':True,
        'front':'Blender -Y / glTF +Z','grounded':True,'source':'Original Blender modelling; anime-inspired fan reconstruction',
        'glass':'Alpha blend only, no transmission render pass' if asset_id=='log-pose' else None}
    assert triangles<70000,report
    assert path.stat().st_size<2_000_000,report
    (OUT/(asset_id+'-report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)
    studio(asset_id,high-low)


def studio(asset_id,dimensions):
    floor=material('Studio only · neutral ivory',(.32,.34,.33),roughness=.91)
    box('STUDIO floor',(0,0,-.026),(200,200,.05),floor,0)
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.samples=32
    scene.cycles.use_denoising=True
    scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('Studio world')
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.40,.47,.56,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    for name,loc,power,size,color in [('Key',(2,-3,4),370,3,(1,.90,.76)),('Fill',(-3,-1,2.4),260,3,(.80,.90,1)),('Rim',(1,3,3.1),440,2,(1,.95,.86))]:
        bpy.ops.object.light_add(type='AREA',location=loc)
        light=bpy.context.object;light.name='STUDIO '+name
        light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.data.color=color
        light.rotation_euler=(Vector((0,0,.4))-light.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(1.6,-2.5,1.5))
    camera=bpy.context.object;camera.name='STUDIO camera'
    camera.rotation_euler=(Vector((0,0,dimensions.z*.49))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=max(dimensions)*1.42
    scene.camera=camera
    scene.view_settings.view_transform='AgX'
    scene.render.image_settings.file_format='PNG'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(asset_id+'.blend')))
    scene.render.filepath=str(OUT/(asset_id+'-preview.png'))
    bpy.ops.render.render(write_still=True)


if __name__=='__main__':
    reset();snail();export_asset('den-den-mushi')
    reset();log_pose();export_asset('log-pose')
