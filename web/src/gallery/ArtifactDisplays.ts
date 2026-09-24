import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { artifacts } from './artifacts';

/** 展台与加载失败时的轻量备用造型；正式展品由独立 GLB 替换。 */
export function buildArtifactDisplays() {
  const root = new THREE.Group(); root.name = 'ArtifactCollection';
  const gradient = new THREE.DataTexture(new Uint8Array([85, 165, 230, 255]), 4, 1, THREE.RedFormat);
  gradient.minFilter = gradient.magFilter = THREE.NearestFilter; gradient.needsUpdate = true;
  const toon = (color: number) => new THREE.MeshToonMaterial({ color, gradientMap: gradient });
  const straw = toon(0xe6bc67), red = toon(0xbd3034), cream = toon(0xf9edcf), black = toon(0x22252b);
  const green = toon(0xa9c56c), shell = toon(0xd8a76f), purple = toon(0x8e58c1), swirl = toon(0x54257a);
  const brass = new THREE.MeshStandardMaterial({ color: 0xbda16b, metalness: .65, roughness: .45 });
  const base = new THREE.MeshStandardMaterial({ color: 0xc4bca9, roughness: .82 });
  const foot = new THREE.MeshStandardMaterial({ color: 0x172528, roughness: .5, metalness: .3 });
  const top = new THREE.MeshStandardMaterial({ color: 0xd8d0bc, roughness: .75 });
  const belt = toon(0x8b5833);
  const glass = new THREE.MeshStandardMaterial({ color: 0xd8f5ff, transparent: true, opacity: .13, roughness: .15, metalness: .12, depthWrite: false });
  const sphere = new THREE.SphereGeometry(1, 24, 16), box = new THREE.BoxGeometry(1, 1, 1);
  function mesh(parent: THREE.Object3D, geometry: THREE.BufferGeometry, material: THREE.Material, x=0, y=0, z=0, sx=1, sy=1, sz=1) {
    const object = new THREE.Mesh(geometry, material); object.position.set(x,y,z); object.scale.set(sx,sy,sz);
    object.castShadow = !material.transparent; object.receiveShadow = true; parent.add(object); return object;
  }
  const ball = (p: THREE.Object3D, m: THREE.Material, x: number,y: number,z: number,sx: number,sy=sx,sz=sx) => mesh(p,sphere,m,x,y,z,sx,sy,sz);
  const slab = (p: THREE.Object3D,m: THREE.Material,x: number,y: number,z: number,w: number,h: number,d: number) => mesh(p,box,m,x,y,z,w,h,d);
  const cylinder = (p: THREE.Object3D,m: THREE.Material,x: number,y: number,z: number,r: number,h: number) => mesh(p,new THREE.CylinderGeometry(r,r,h,40),m,x,y,z);
  function tube(p: THREE.Object3D,m: THREE.Material,points: THREE.Vector3[],radius: number,segments=32) {
    return mesh(p,new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points),segments,radius,6,false),m);
  }
  const v = (x: number,y: number,z: number) => new THREE.Vector3(x,y,z);
  for (const [index, artifact] of artifacts.entries()) {
    const display = new THREE.Group(); display.name = 'artifact-' + artifact.id;
    display.position.set(artifact.x,0,artifact.z); root.add(display);
    const width = artifact.width;
    const depth = artifact.depth;
    const lift = (artifact.plinthHeight ?? 1.05) - 1.05;
    const height = artifact.plinthHeight ?? 1.05;
    // 圆形信物台与横向刀台区分器物尺度；缩进的暗色踢脚减轻体量。
    if (artifact.id === 'straw-hat') {
      const radius = Math.min(width, depth) / 2;
      cylinder(display,foot,0,.075,0,radius-.06,.15);
      cylinder(display,base,0,(height+.14)/2,0,radius,height-.14);
      cylinder(display,brass,0,height-.015,0,radius+.012,.018);
      cylinder(display,top,0,height+.014,0,radius,.025);
      cylinder(display,brass,0,.16,0,radius+.006,.025);
    } else {
      slab(display,foot,0,.075,0,width-.12,.15,depth-.12);
      slab(display,base,0,(height+.15)/2,0,width,height-.15,depth);
      slab(display,brass,0,height-.015,0,width+.018,.018,depth+.018);
      slab(display,top,0,height+.014,0,width,.025,depth);
      slab(display,brass,0,.16,0,width+.008,.022,depth+.008);
    }
    const canvas = document.createElement('canvas'); canvas.width=768;canvas.height=256;
    const ctx=canvas.getContext('2d')!; ctx.fillStyle='#15272b';ctx.fillRect(0,0,768,256);
    ctx.strokeStyle='#ad915d';ctx.lineWidth=3;ctx.strokeRect(8,8,752,240);
    ctx.fillStyle='#f0dfb7';ctx.textAlign='center';ctx.font='600 55px "Museum Serif", serif';ctx.fillText(artifact.title,384,106,700);
    ctx.fillStyle='#cbbb98';ctx.font='27px "Museum Sans", sans-serif';ctx.fillText(artifact.subtitle,384,164,700);
    ctx.font='22px sans-serif';ctx.fillText(`${String(index+1).padStart(2,'0')}    E 查看展签`,384,217);
    const map=new THREE.CanvasTexture(canvas);map.colorSpace=THREE.SRGBColorSpace;map.anisotropy=4;
    // 低台上的长刀铭牌抬到台沿上方，入口近景不会落入视口底边或 HUD。
    const plaqueY = artifact.sideDisplay ? height + .12 : height - .27;
    const plaqueWidth = artifact.sideDisplay ? Math.min(width - .26, .76) : Math.min(width - .26, 1.05);
    const plaqueX = artifact.sideDisplay ? .2 : 0;
    mesh(display,new THREE.PlaneGeometry(plaqueWidth,.34),new THREE.MeshBasicMaterial({map}),plaqueX,plaqueY,depth/2+.014);
    const item=new THREE.Group(); item.name='artifact-fallback-'+artifact.id; item.position.y=1.1 + lift;
    if (artifact.sideDisplay) item.rotation.y = artifact.displayYaw ?? Math.PI / 2;
    display.add(item);
    if (artifact.id==='straw-hat') {
      const hat=new THREE.Group();hat.position.y=.3;hat.rotation.x=.23;item.add(hat);
      const brim=new THREE.CylinderGeometry(.73,.73,.055,64,1);
      const pos=brim.attributes.position!;
      for(let i=0;i<pos.count;i++)pos.setY(i,pos.getY(i)+.025*Math.sin(Math.atan2(pos.getZ(i),pos.getX(i))*3));
      brim.computeVertexNormals();mesh(hat,brim,straw);
      const profile=[v(0,0,0),v(.39,0,0),v(.39,.21,0),v(.33,.34,0),v(.18,.39,0),v(0,.4,0)];
      mesh(hat,new THREE.LatheGeometry(profile.map(p=>new THREE.Vector2(p.x,p.y)),48),straw);
      cylinder(hat,red,0,.115,0,.395,.11);
      for(let r=.43;r<.71;r+=.038){const ring=mesh(hat,new THREE.TorusGeometry(r,.003,4,64),belt);ring.rotation.x=Math.PI/2;ring.position.y=.033;}
      for(let i=0;i<32;i++){const a=i*Math.PI/16; tube(hat,belt,[v(Math.cos(a)*.44,.034,Math.sin(a)*.44),v(Math.cos(a)*.7,.034,Math.sin(a)*.7)],.002,1);}
    } else if(artifact.id==='den-den-mushi') {
      ball(item,green,0,.17,.15,.54,.16,.48);
      ball(item,green,0,.37,.33,.31,.34,.31);
      ball(item,shell,0,.48,-.13,.45,.47,.32);
      for (const side of [-1, 1]) {
        const spiral=[];
        for(let i=0;i<95;i++){
          const a=i*.17,r=.015+i*.0038;
          const dy=Math.sin(a)*r/.47,dz=Math.cos(a)*r/.47;
          spiral.push(v(side*(.45*Math.sqrt(Math.max(0,1-dy*dy-dz*dz))+.009),.48+dy*.47,-.13+dz*.32));
        }
        tube(item,belt,spiral,.017,95);
      }
      for(const x of [-.19,.19]) {
        tube(item,green,[v(x,.58,.36),v(x*1.3,.84,.38),v(x*1.38,1.02,.35)],.055,12);
        ball(item,cream,x*1.38,1.05,.36,.095);ball(item,black,x*1.38,1.05,.441,.041,.05,.016);
      }
      tube(item,black,[v(-.32,.79,-.15),v(-.26,.99,-.16),v(.26,.99,-.16),v(.32,.79,-.15)],.07,18);
      for(const x of [-.33,.33])ball(item,black,x,.79,-.15,.12,.1,.12);
      const dial=cylinder(item,brass,0,.22,.665,.15,.04);dial.rotation.x=Math.PI/2;
      for(let i=0;i<8;i++){const a=i*Math.PI/4;ball(item,black,Math.cos(a)*.105,.22+Math.sin(a)*.105,.691,.022,.022,.012);}
      tube(item,black,[v(-.09,.48,.616),v(0,.455,.636),v(.09,.48,.616)],.012,12);
    } else if(artifact.id==='log-pose') {
      const instrument=new THREE.Group();instrument.rotation.x=.4;instrument.position.y=.43;item.add(instrument);
      slab(instrument,belt,0,-.07,0,.39,.07,1.15);
      const buckle=mesh(instrument,new THREE.TorusGeometry(.14,.025,6,4),brass,0,-.018,.44);buckle.rotation.x=Math.PI/2;
      cylinder(instrument,brass,0,0,0,.36,.09);
      cylinder(instrument,cream,0,.049,0,.3,.012);
      mesh(instrument,new THREE.SphereGeometry(.34,32,20),glass,0,.34,0);
      tube(instrument,black,[v(0,.07,0),v(0,.33,0)],.009,1);
      const needle=mesh(instrument,new THREE.ConeGeometry(.048,.39,4),red,0,.33,0);needle.rotation.z=-Math.PI/2;needle.rotation.y=.45;
      for(const x of [-.29,.29])tube(instrument,brass,[v(x,.05,0),v(x*1.23,.26,0),v(x*1.16,.4,0)],.012,12);
    } else if(artifact.id==='gum-gum') {
      ball(item,purple,0,.51,0,.47,.48,.46);
      // 每条旋涡贴合球面，不使用普通水果的随机斑点。
      for(const [lat,number] of [[-.65,5],[0,7],[.65,5]])for(let j=0;j<number;j++){
        const lon=j*Math.PI*2/number+(lat===0?.2:0),center=v(Math.cos(lat)*Math.sin(lon),Math.sin(lat),Math.cos(lat)*Math.cos(lon));
        const tangent=v(Math.cos(lon),0,-Math.sin(lon)),bitangent=new THREE.Vector3().crossVectors(center,tangent); const points=[];
        for(let k=0;k<=52;k++){const a=k*.2,r=.009+k*.0039;const p=center.clone().addScaledVector(tangent,Math.cos(a)*r).addScaledVector(bitangent,Math.sin(a)*r).normalize();points.push(v(p.x*.478,.51+p.y*.488,p.z*.468));}
        tube(item,swirl,points,.014,52);
      }
      tube(item,green,[v(0,.97,0),v(.05,1.15,0),v(.23,1.18,0),v(.3,1.06,0),v(.2,1.02,0),v(.17,1.1,0)],.035,30);
    } else if(artifact.id==='wado') {
      for(const x of [-.55,.6]) {slab(item,black,x,.07,0,.28,.13,.42);tube(item,black,[v(x,.1,0),v(x,.46,0),v(x-.09,.52,0)],.045,8);}
      tube(item,cream,[v(-1,.51,0),v(-.6,.48,0),v(0,.47,0),v(.5,.51,0)],.051,40);
      tube(item,cream,[v(.55,.52,0),v(.95,.57,0)],.052,1);
      const guard=cylinder(item,brass,.52,.515,0,.12,.032);guard.rotation.z=-Math.PI/2;
      for(let i=0;i<7;i++) {const diamond=slab(item,belt,.6+i*.047,.531+i*.006,.049,.03,.03,.006);diamond.rotation.z=Math.PI/4;}
      for(const x of [-1,.98]) {const cap=cylinder(item,brass,x,x<0?.51:.575,0,.054,.025);cap.rotation.z=-Math.PI/2;}
    }
  }
  // 船模尚未加载或请求失败时保留羊首帆船；独立分组便于加载后替换。
  const stand = artifacts.find(artifact => artifact.id === 'going-merry')!;
  const fallback = new THREE.Group(); fallback.name = 'DisplayShipFallback';
  fallback.position.set(stand.x, 1.1, stand.z);
  ball(fallback, belt, 0, .22, 0, .38, .23, .72);
  slab(fallback, straw, 0, .32, 0, .66, .07, 1.1);
  slab(fallback, cream, 0, .49, -.4, .5, .3, .4);
  slab(fallback, red, 0, .66, -.4, .58, .06, .46);
  cylinder(fallback, belt, 0, .85, -.03, .025, 1.08);
  const sail = new THREE.PlaneGeometry(.78, .62, 10, 10);
  const sailPositions = sail.attributes.position!;
  for (let i = 0; i < sailPositions.count; i++) sailPositions.setZ(i, .09 * Math.cos(sailPositions.getX(i) * Math.PI / .78));
  sail.computeVertexNormals();
  mesh(fallback, sail, new THREE.MeshToonMaterial({ color: 0xf9edcf, gradientMap: gradient, side: THREE.DoubleSide }), 0, 1.02, .03);
  tube(fallback, belt, [v(-.42, 1.35, 0), v(.42, 1.35, 0)], .018, 1);
  // 小帆上的草帽骷髅与船首卷角保留梅利号的识别特征。
  ball(fallback, black, 0, 1.05, .132, .11, .1, .008);
  for (const x of [-.038, .038]) ball(fallback, cream, x, 1.06, .143, .025, .027, .004);
  slab(fallback, black, 0, .955, .134, .1, .07, .012);
  slab(fallback, straw, 0, 1.14, .147, .26, .03, .012);
  slab(fallback, straw, 0, 1.18, .14, .15, .065, .012);
  slab(fallback, red, 0, 1.155, .154, .15, .018, .009);
  tube(fallback, cream, [v(0, .25, .62), v(0, .52, .73)], .095, 6);
  ball(fallback, cream, 0, .59, .73, .16, .16, .18);
  ball(fallback, cream, 0, .54, .85, .1, .08, .07);
  for (const side of [-1, 1]) {
    ball(fallback, black, side * .07, .63, .874, .018);
    const horn = [];
    for (let i = 0; i < 26; i++) { const a = i * .22, r = .085 - i * .0024; horn.push(v(side * .155, .61 + Math.sin(a) * r, .72 + Math.cos(a) * r)); }
    tube(fallback, brass, horn, .024, 26);
  }
  // 每种材质合并一次，增添物件不会恢复为上千次绘制。
  root.updateMatrixWorld(true);
  const batches=new Map<THREE.Material,THREE.Mesh[]>();
  root.traverse(o=>{
    if (!(o instanceof THREE.Mesh) || Array.isArray(o.material) || o.material.transparent) return;
    // 保留每件备用展品的独立层级，正式模型加载后可以完整替换。
    for (let parent=o.parent; parent && parent!==root; parent=parent.parent) {
      if(parent.name.startsWith('artifact-fallback-')) return;
    }
    const list=batches.get(o.material)??[];list.push(o);batches.set(o.material,list);
  });
  const used=new Set<THREE.BufferGeometry>();
  for(const [material,meshes] of batches){
    if(meshes.length<2)continue;
    const parts=meshes.map(m=>(m.geometry.index?m.geometry.toNonIndexed():m.geometry.clone()).applyMatrix4(m.matrixWorld));
    const geometry=mergeGeometries(parts);parts.forEach(p=>p.dispose());if(!geometry)continue;
    const combined=mesh(root,geometry,material);combined.name='artifact-batch';
    for(const original of meshes){used.add(original.geometry);original.removeFromParent();}
  }
  root.add(fallback);
  const retained=new Set<THREE.BufferGeometry>();root.traverse(o=>{if(o instanceof THREE.Mesh)retained.add(o.geometry);});
  used.forEach(g=>{if(!retained.has(g))g.dispose();});
  return root;
}
