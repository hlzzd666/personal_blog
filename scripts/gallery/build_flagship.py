"""Run with Blender --background --python scripts/gallery/build_flagship.py."""
import bpy
import bmesh
import math
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/gallery/model'
PUBLIC = ROOT / 'web/public/gallery/flagship'
CFG = json.loads((ROOT / 'web/src/gallery/layout.json').read_text())
assert CFG['bayLength']==3.4 and CFG['width']==10, 'Re-author the module geometry before changing structural dimensions'
OUT.mkdir(parents=True, exist_ok=True)
PUBLIC.mkdir(parents=True, exist_ok=True)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def material(name, color, metallic=0, roughness=.6):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    return mat

woods = [material('Teak_' + str(i), (.36+i*.027, .21+i*.019, .105+i*.013)) for i in range(3)]
walnut = material('Walnut ribs', (.16, .075, .035))
teal = material('Teal painted hull', (.025, .24, .23), .05)
cream = material('Ivory canvas', (.82, .81, .70))
brass = material('Aged brass', (.62, .39, .12), .86, .34)
rope = material('Hemp rigging', (.48, .42, .28))
coral = material('Coral navigation', (.65, .1, .065))
glass = material('Lantern lens', (.93, .76, .37), .2, .25)
bsdf = glass.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Emission Color'].default_value = (1, .65, .22, 1)
bsdf.inputs['Emission Strength'].default_value = .3

def pbr(mat,name):
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    bsdf=nodes.get('Principled BSDF')
    for kind,socket in [('color','Base Color'),('roughness','Roughness'),('normal','Normal')]:
        path=PUBLIC/'materials'/(name+'-'+kind+('.jpg' if kind=='color' else '.png'))
        image=bpy.data.images.load(str(path),check_existing=True)
        if kind!='color': image.colorspace_settings.name='Non-Color'
        image.pack()
        tex=nodes.new('ShaderNodeTexImage'); tex.image=image
        if kind=='normal':
            normal=nodes.new('ShaderNodeNormalMap')
            normal.inputs['Strength'].default_value=.5
            links.new(tex.outputs['Color'],normal.inputs['Color'])
            links.new(normal.outputs['Normal'],bsdf.inputs[socket])
        else: links.new(tex.outputs['Color'],bsdf.inputs[socket])
for mat in woods: pbr(mat,'teak')
pbr(walnut,'walnut'); pbr(brass,'brass'); pbr(cream,'canvas')

def xyz(p):
    return Vector((p[0], -p[2], p[1]))

def box(name, loc, scale, mat, parent=None, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz(loc))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = (scale[0], scale[2], scale[1])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    # Model-space UVs keep floor fibers longitudinal and avoid stretched cube UVs.
    uv=obj.data.uv_layers.active
    for poly in obj.data.polygons:
        for loop_index in poly.loop_indices:
            v=obj.data.vertices[obj.data.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv=(v.x*.55+loc[0]*.13, v.y*.32+loc[2]*.17) if abs(poly.normal.z)>.5 else (v.x*.5+v.y*.5,v.z*.3)
    if bevel:
        mod = obj.modifiers.new('Soft edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.parent = parent
    return obj

def rod(name, a, b, radius, mat, parent=None, vertices=10):
    a, b = xyz(a), xyz(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=(b-a).length, location=(a+b)/2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    obj.data.materials.append(mat)
    obj.parent = parent
    return obj

def ring(name, loc, radius, tube, mat, parent, axis='z'):
    bpy.ops.mesh.primitive_torus_add(major_segments=32, minor_segments=6, location=xyz(loc), major_radius=radius, minor_radius=tube)
    obj = bpy.context.object
    obj.name = name
    if axis == 'z': obj.rotation_euler.x = math.pi/2
    if axis == 'x': obj.rotation_euler.y = math.pi/2
    obj.data.materials.append(mat)
    obj.parent = parent
    return obj

def root(name):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    return obj

def deck(parent, z0, z1, width=10):
    for i in range(28):
        box('Deck plank', (-width/2+(i+.5)*width/28, -.1, (z0+z1)/2), (width/28-.009, .2, z1-z0-.009), woods[i%3], parent, .004)
    for side in [-1, 1]:
        box('Teal hull', (side*(width/2-.13), -.72, (z0+z1)/2), (.25, 1.35, z1-z0), teal, parent)
        box('Brass waterline', (side*(width/2+.006), -.35, (z0+z1)/2), (.028, .075, z1-z0), brass, parent)

def lantern(parent, x, z):
    rod('Lantern bracket', (x, 3.9, z), (x, 3.35, z), .035, brass, parent)
    box('Lantern lens', (x, 3.2, z), (.22, .32, .22), glass, parent, .02)
    for y in [3.0, 3.4]: box('Lantern cap', (x, y, z), (.33, .055, .33), brass, parent)

bay = root('CabinBay')
deck(bay, -1.7, 1.7)
for side in [-1, 1]:
    wall=box('Walnut sidewall', (side*3.6,2.3,0),(.22,2.75,3.4),walnut,bay)
    cutter=rod('Porthole cutter',(side*3.1,2.25,1.20),(side*4.1,2.25,1.20),.31,brass,None,48)
    cutter.scale.x=2.1
    bpy.context.view_layer.objects.active=wall
    mod=wall.modifiers.new('Oval window','BOOLEAN'); mod.operation='DIFFERENCE'; mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
    rim=ring('Oval brass porthole',(side*3.45,2.25,1.20),.32,.037,brass,bay,'x')
    rim.scale.x=2.1
    box('Wainscot', (side*3.6, .48, 0), (.18, .95, 3.4), teal, bay)
    box('Wainscot cap', (side*3.4,.96,0),(.24,.13,3.4),walnut,bay,.025)
    for y in [.14,.85]: box('Wainscot brass line',(side*3.40,y,0),(.035,.025,3.4),brass,bay)
    for dz in [-1.60,0,1.60]: box('Wainscot mullion',(side*3.39,.5,dz),(.07,.65,.065),walnut,bay,.009)
    box('Upper cornice',(side*3.45,3.59,0),(.3,.24,3.4),walnut,bay,.025)
    box('Exhibit backing wall', (side*3.55, 2.25, 0), (.16, 2.55, 2.02), teal, bay)
    for dz in [-.95, .95]: box('Panel molding', (side*3.43, 2.23, dz), (.075, 2.60, .06), brass, bay)
    box('Rib post',(side*3.33,1.74,1.56),(.26,3.48,.26),walnut,bay,.025)
    for y in [.20,3.25]:
        box('Rib brass bracket',(side*3.18,y,1.56),(.035,.28,.32),brass,bay,.01)
        for dz in [-.1,.1]: rod('Bracket bolt',(side*3.14,y,1.56+dz),(side*3.11,y,1.56+dz),.025,brass,bay,8)
    rod('Ceiling stringer', (side*2.15, 4.97, -1.7), (side*2.15, 4.97, 1.7), .065, walnut, bay)
    rod('Skylight edge', (side*.82, 5.50, -1.7), (side*.82, 5.50, 1.7), .08, walnut, bay)
for i in range(32):
    t0, t1 = i*math.pi/32, (i+1)*math.pi/32
    p0 = (3.45*math.cos(t0), 3.4+2.2*math.sin(t0), 1.56)
    p1 = (3.45*math.cos(t1), 3.4+2.2*math.sin(t1), 1.56)
    vertices=[]
    for z in [1.43,1.70]:
        for thickness in [0,.20]:
            for t in [t0,t1]: vertices.append(xyz(((3.45-thickness)*math.cos(t),3.4+(2.2-thickness)*math.sin(t),z)))
    mesh=bpy.data.meshes.new('Solid arch segment')
    mesh.from_pydata(vertices,[],[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)])
    arch=bpy.data.objects.new('Walnut arch rib',mesh); bpy.context.collection.objects.link(arch)
    arch.parent=bay; mesh.materials.append(walnut)
    secondary=arch.copy(); secondary.data=arch.data; bpy.context.collection.objects.link(secondary)
    secondary.location.y=1.7; secondary.parent=bay
    uv=mesh.uv_layers.new()
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vertex=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=(vertex.y*1.4, (i+(mesh.loops[li].vertex_index%2))*.15)
    if abs((p0[0]+p1[0])/2) < .85: continue
    verts = [xyz((p0[0],p0[1]+.04,-1.7)),xyz((p1[0],p1[1]+.04,-1.7)),xyz((p1[0],p1[1]+.04,1.7)),xyz((p0[0],p0[1]+.04,1.7))]
    mesh = bpy.data.meshes.new('Canopy')
    mesh.from_pydata(verts, [], [(0,1,2,3)])
    uv=mesh.uv_layers.new()
    for li,coord in enumerate([(0,0),(1,0),(1,1),(0,1)]): uv.data[li].uv=coord
    obj = bpy.data.objects.new('Canvas roof', mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(cream)
    obj.parent = bay
for side in [-1,1]:
    ring('Recessed brass ceiling light',(side*.80,5.28,.75),.12,.032,brass,bay,'y')
    lamp=box('Ceiling light diffuser',(side*.80,5.28,.75),(.17,.02,.17),glass,bay,.02)

stern = root('SternDeck')
deck(stern, 0, 7)
for side in [-1,1]:
    for z in range(8): rod('Rail post', (side*4.75,0,z), (side*4.75,1.15,z), .065, brass, stern)
    for y in [.5,1.15]: rod('Aft rail', (side*4.75,y,0),(side*4.75,y,7), .045, rope if y<1 else brass, stern)
for y in [.5,1.15]: rod('Stern rail', (-4.75,y,6.8),(4.75,y,6.8), .05, brass, stern)
ring('Deck compass rim',(0,.022,-2.4),1.35,.038,brass,stern,'y')
ring('Deck compass inner rim',(0,.022,-2.4),1.22,.018,brass,stern,'y')
for i in range(16):
    a = i*math.pi/8
    radius=1.13 if i%2==0 else .77
    tip=(math.sin(a)*radius,.022,-2.4+math.cos(a)*radius)
    rod('Compass inlay',(0,.022,-2.4),tip,.018,brass,stern)
    for flank in [-1,1]:
        edge=(math.sin(a+flank*.30)*.32,.022,-2.4+math.cos(a+flank*.30)*.32)
        mesh=bpy.data.meshes.new('Compass wedge');mesh.from_pydata([xyz((0,.022,-2.4)),xyz(tip),xyz(edge)],[],[(0,1,2)])
        obj=bpy.data.objects.new('Compass star inlay',mesh);bpy.context.collection.objects.link(obj);obj.parent=stern;mesh.materials.append(brass if flank<0 else walnut)
for side in [-1,1]:
    rod('Aft mast',(side*4.1,0,4.6),(side*4.1,7.5,4.6),.13,walnut,stern)
    rod('Rigging',(side*4.1,7.2,4.6),(side*4.7,1,0),.024,rope,stern)
    rod('Rigging',(side*4.1,7.2,4.6),(side*4.7,1,6.7),.024,rope,stern)

bow = root('BowDeck')
# Bow width narrows linearly after the first three meters; collisions use the same rule.
for i in range(36):
    z = -(i+.5)*.25
    half = 5 if z >= -3 else 5-(abs(z)-3)*.65
    box('Bow planks',(0,-.1,z),(half*2,.2,.242),woods[i%3],bow,.004)
    for side in [-1,1]:
        box('Bow hull',(side*(half-.12),-.65,z),(.24,1.3,.26),teal,bow)
for side in [-1,1]:
    points=[(side*4.75,0,0),(side*4.75,0,-3),(side*1.0,0,-8.7)]
    for j in range(9):
        z=-j
        half=4.75 if j<=3 else 4.75-(j-3)*.65
        rod('Bow post',(side*half,0,z),(side*half,1.15,z),.055,brass,bow)
    for a,b in zip(points,points[1:]):
        for y in [.5,1.15]: rod('Bow rail',(a[0],y,a[2]),(b[0],y,b[2]),.045,brass,bow)
rod('Bow tip rail',(-1,1.15,-8.7),(1,1.15,-8.7),.05,brass,bow)
box('Helm base',(0,.55,-5.8),(.5,1.1,.6),teal,bow,.06)
ring('Helm wheel',(0,1.4,-5.65),.62,.06,walnut,bow)
for i in range(10):
    a=i*math.tau/10
    rod('Wheel spoke',(0,1.4,-5.65),(math.cos(a)*.78,1.4+math.sin(a)*.78,-5.65),.035,brass,bow)

def consolidate(parent):
    # Merge by material within each reusable module to bound WebGL draw calls.
    groups={}
    for obj in list(parent.children):
        if obj.type=='MESH': groups.setdefault(obj.data.materials[0].name,[]).append(obj)
    for name, objects in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects: obj.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]
        if len(objects)>1: bpy.ops.object.join()
        objects[0].name=parent.name+'_'+name.replace(' ','_')
        if name=='Ivory canvas':
            mesh=objects[0].data; bm=bmesh.new(); bm.from_mesh(mesh)
            bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=.001)
            bm.to_mesh(mesh);bm.free()
            for poly in mesh.polygons: poly.use_smooth=True

frame=root('ExhibitFrame')
box('Frame walnut backing',(0,0,-.065),(1.89,2.78,.12),walnut,frame,.018)
for x in [-.875,.875]:
    box('Brass frame molding',(x,0,.04),(.10,2.67,.14),brass,frame,.023)
    box('Frame inner bead',(x*.937,0,.12),(.022,2.52,.023),brass,frame,.01)
for y in [-1.30,1.30]:
    box('Brass frame molding',(0,y,.04),(1.84,.10,.14),brass,frame,.023)
    box('Frame inner bead',(0,y*.95,.12),(1.67,.022,.023),brass,frame,.01)
for x in [-.871,.871]:
    for y in [-1.29,1.29]:
        rod('Frame corner rivet',(x,y,.105),(x,y,.14),.027,brass,frame,12)
ring('Frame medallion',(0,1.57,.02),.145,.025,brass,frame)
rod('Number medallion face',(0,1.57,.025),(0,1.57,.055),.134,brass,frame,32)
for module in [bay,bow,stern,frame]: consolidate(module)
bpy.ops.object.select_all(action='DESELECT')
for module in [bay,bow,stern,frame]:
    module.select_set(True)
    for child in module.children: child.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(PUBLIC/'flagship.glb'),export_format='GLB',use_selection=True,export_yup=True,export_cameras=False,export_lights=False)
frame.hide_render=True
for child in frame.children: child.hide_render=True

# Assemble a six-bay editable preview after exporting the reusable source modules.
for row in range(1,6):
    module=root('CabinBay_'+str(row))
    module.location=xyz((0,0,-row*3.4))
    for child in bay.children:
        copy=child.copy()
        copy.data=child.data
        bpy.context.collection.objects.link(copy)
        copy.parent=module
bow.location=xyz((0,0,-18.7))
stern.location=xyz((0,0,1.7))
for row in range(6):
    for side in [-1,1]:
        x,z=side*CFG['frameX'],-row*3.4
        box('Preview blank display',(x-side*.085,2.05,z),(.01,2.4,1.6),teal)
        mount=root('Preview exhibit')
        mount.location=xyz((x,2.05,z)); mount.rotation_euler.z=math.pi/2 if side<0 else -math.pi/2
        for child in frame.children:
            copy=child.copy(); copy.data=child.data; copy.hide_render=False
            bpy.context.collection.objects.link(copy); copy.parent=mount
sea=material('Preview sea',(.055,.38,.46),.2,.28)
water_image=bpy.data.images.load(str(ROOT/'web/public/gallery/generated/calm-ocean-color-tile.png'))
water_image.pack()
nodes,links=sea.node_tree.nodes,sea.node_tree.links
tex=nodes.new('ShaderNodeTexImage');tex.image=water_image
mapping=nodes.new('ShaderNodeMapping');mapping.inputs['Scale'].default_value=(60,60,60)
coords=nodes.new('ShaderNodeTexCoord');links.new(coords.outputs['Generated'],mapping.inputs['Vector']);links.new(mapping.outputs['Vector'],tex.inputs['Vector'])
links.new(tex.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color'])
noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=160
bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.08
links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])
box('Preview ocean',(0,-1.6,-8),(500,.1,500),sea)
world=bpy.data.worlds.new('Daylight')
bpy.context.scene.world=world
world.use_nodes=True
env=world.node_tree.nodes.new('ShaderNodeTexSky')
env.sky_type='NISHITA'; env.sun_elevation=math.radians(42); env.sun_rotation=math.radians(130)
env.altitude=.1; env.air_density=1.0; env.dust_density=.4; env.ozone_density=1.0
world.node_tree.links.new(env.outputs['Color'],world.node_tree.nodes['Background'].inputs[0])
world.node_tree.nodes['Background'].inputs[1].default_value=.28
bpy.ops.object.light_add(type='SUN',location=(0,0,12))
bpy.context.object.rotation_euler=(.65,-.65,-.3)
bpy.context.object.data.energy=3.0
for z in [3,-5,-13,-22]:
    bpy.ops.object.light_add(type='AREA',location=xyz((0,4.8,z)))
    bpy.context.object.data.energy=180
    bpy.context.object.data.shape='DISK'
    bpy.context.object.data.size=7
bpy.ops.object.camera_add(location=xyz((.45,1.7,3.3)))
camera=bpy.context.object
camera.rotation_euler=(xyz((-.15,2.2,-13))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.lens=25
scene=bpy.context.scene
scene.camera=camera
scene.render.engine='CYCLES'
scene.cycles.samples=64
scene.cycles.use_denoising=True
scene.render.resolution_x=1254
scene.render.resolution_y=1254
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(OUT/'preview.png')
scene.view_settings.view_transform='AgX'
scene.view_settings.exposure=-.25
# Start the native Blender app in camera view with textures ready for inspection.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'旗舰船舱展馆.blend'))
bpy.ops.render.render(write_still=True)
print('FLAGSHIP_BUILD_COMPLETE',flush=True)
