import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";
import type { HallLayout } from "./layout";
import { museumAsset } from "./curation";
import { buildArtifactDisplays } from "./ArtifactDisplays";
import { artifacts, posterStartZ } from "./artifacts";

/** 船长舱按真实空间构建；重复木作合批，光源仅在序厅和近侧保留。 */
export function buildMuseumRoom(hall: HallLayout, loader: THREE.TextureLoader) {
  const root = new THREE.Group();
  root.name = "CaptainsMuseum";
  const boxGeometry = new RoundedBoxGeometry(1, 1, 1, 2, .018);
  const cylinderGeometry = new THREE.CylinderGeometry(1, 1, 1, 16);
  const sphereGeometry = new THREE.SphereGeometry(1, 16, 12);
  const materialRoot = import.meta.env.BASE_URL + "gallery/flagship/materials/";
  function wood(name: string, color: number, repeat: number, roughness: number) {
    const map = loader.load(materialRoot + name + "-color.jpg");
    map.colorSpace = THREE.SRGBColorSpace;
    map.wrapS = map.wrapT = THREE.RepeatWrapping;
    map.repeat.set(repeat, repeat);
    map.anisotropy = 4;
    const normalMap = loader.load(materialRoot + name + "-normal.png");
    normalMap.wrapS = normalMap.wrapT = THREE.RepeatWrapping;
    normalMap.repeat.copy(map.repeat);
    return new THREE.MeshStandardMaterial({ color, map, normalMap, normalScale: new THREE.Vector2(.08, .08), roughness, metalness: .08 });
  }
  const walnut = wood("walnut", 0xa1815f, 1, .56);
  const darkWood = wood("walnut", 0x745238, 1, .62);
  const floorWood = new THREE.MeshStandardMaterial({ color: 0xa29982, roughness: .83, metalness: .02 });
  // 压低木材纹理反差，让彩色展品从安静的背景中显现。
  const grainCanvas = document.createElement('canvas');grainCanvas.width=128;grainCanvas.height=512;
  const grain = grainCanvas.getContext('2d')!;
  grain.fillStyle='#bcb8a8';grain.fillRect(0,0,128,512);
  for(let i=0;i<140;i++) {
    const x=(i*37)%128, y=(i*97)%512;
    grain.strokeStyle=i%3 ? '#a5a29125' : '#e1dccb25';grain.lineWidth=.5;
    grain.beginPath();grain.moveTo(x,y);grain.bezierCurveTo(x+3,y+35,x-2,y+70,x+1,y+140);grain.stroke();
  }
  const grainMap = new THREE.CanvasTexture(grainCanvas);grainMap.colorSpace=THREE.SRGBColorSpace;
  grainMap.wrapS=grainMap.wrapT=THREE.RepeatWrapping;grainMap.anisotropy=4;
  floorWood.map = grainMap;
  const wall = new THREE.MeshStandardMaterial({ color: 0x19353b, roughness: .92 });
  const ceiling = new THREE.MeshStandardMaterial({ color: 0x182b30, roughness: .95 });
  const brassMap = loader.load(materialRoot + "brass-color.jpg");
  brassMap.colorSpace = THREE.SRGBColorSpace;
  const brass = new THREE.MeshStandardMaterial({ color: 0xa88d53, map: brassMap, metalness: .78, roughness: .42 });
  const agedBrass = new THREE.MeshStandardMaterial({ color: 0x6e5330, metalness: .65, roughness: .48 });
  const flame = new THREE.MeshBasicMaterial({ color: 0xffd49a });
  const glow = new THREE.MeshBasicMaterial({ color: 0xffb65a, transparent: true, opacity: .13, depthWrite: false });
  function mesh(geometry: THREE.BufferGeometry, material: THREE.Material, x: number, y: number, z: number, sx = 1, sy = 1, sz = 1, parent: THREE.Object3D = root) {
    const object = new THREE.Mesh(geometry, material);
    object.position.set(x, y, z);
    object.scale.set(sx, sy, sz);
    object.castShadow = true;
    object.receiveShadow = true;
    parent.add(object);
    return object;
  }
  const box = (mat: THREE.Material, x: number, y: number, z: number, w: number, h: number, d: number, parent = root) => mesh(boxGeometry, mat, x, y, z, w, h, d, parent);
  const cylinder = (mat: THREE.Material, x: number, y: number, z: number, r: number, h: number, parent = root) => mesh(cylinderGeometry, mat, x, y, z, r, h, r, parent);
  function rod(a: THREE.Vector3, b: THREE.Vector3, radius: number, mat = brass, parent = root) {
    const middle = a.clone().add(b).multiplyScalar(.5);
    const rodMesh = cylinder(mat, middle.x, middle.y, middle.z, radius, a.distanceTo(b), parent);
    rodMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
    return rodMesh;
  }
  function ring(radius: number, tube: number, mat: THREE.Material, x: number, y: number, z: number, parent = root) {
    return mesh(new THREE.TorusGeometry(radius, tube, 8, 48), mat, x, y, z, 1, 1, 1, parent);
  }
  function label(text: string, w: number, h: number, x: number, y: number, z: number, background = "#312013", color = "#d2b577") {
    const canvas = document.createElement("canvas");
    canvas.width = 1024; canvas.height = 128;
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = background; ctx.fillRect(0, 0, 1024, 128);
    ctx.strokeStyle = color; ctx.strokeRect(10, 10, 1004, 108);
    ctx.fillStyle = color; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.font = '40px "Museum Serif", serif';
    ctx.fillText(text, 512, 65, 940);
    const map = new THREE.CanvasTexture(canvas); map.colorSpace = THREE.SRGBColorSpace;
    return mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map, roughness: .8 }), x, y, z);
  }
  const front = hall.cabinFront, back = hall.cabinBack, length = back - front;
  box(darkWood, 0, -.18, (front + back) / 2, 10, .35, length);
  // 独立甲板条保留缝隙、拼缝与方向性纹理。
  for (let x = -4.8; x < 4.9; x += .4) {
    for (let z = front; z < back; z += 3.4) {
      const depth = Math.min(3.4, back - z);
      box(floorWood, x, .015, z + depth / 2, .386, .04, depth - .018);
      for (const dz of [.09, depth - .09]) cylinder(agedBrass, x + .12, .04, z + dz, .009, .003);
    }
  }
  box(ceiling, 0, 5.08, (front + back) / 2, 10, .24, length);
  for (const side of [-1, 1]) {
    box(wall, side * 4.85, 2.5, (front + back) / 2, .3, 5, length);
    for (const y of [.15, 1.1, 1.22, 4.45, 4.8]) {
      box(walnut, side * 4.6, y, (front + back) / 2, .23, .12, length);
      box(brass, side * 4.46, y + .055, (front + back) / 2, .018, .014, length);
    }
    for (let z = front + .5; z < back; z += 1.15) {
      box(walnut, side * 4.67, .63, z, .16, .82, 1.05);
      box(darkWood, side * 4.56, .64, z, .09, .57, .77);
      for (const dz of [-.45, .45]) box(agedBrass, side * 4.5, .65, z + dz, .018, .69, .018);
    }
    for (let z = -2; z < back; z += 3.4) {
      box(walnut, side * 4.55, 2.5, z, .35, 5, .3);
      for (const y of [.12, 1.18, 3.8, 4.6]) box(brass, side * 4.5, y, z, .43, .07, .37);
      box(darkWood, 0, 4.77, z, 9.2, .3, .3);
      box(brass, 0, 4.59, z, 8.85, .02, .04);
    }
  }
  for (let x = -4; x <= 4; x += 2) box(walnut, x, 4.9, (front + back) / 2, .13, .16, length);
  // 弧形肋木与内嵌黄铜线建立船舱节奏，中央留出完整净空。
  for (let z = -5.4; z < back; z += 6.8) {
    const points = [];
    for (let i = 0; i <= 20; i++) {
      const x = -4.42 + i * 8.84 / 20;
      points.push(new THREE.Vector3(x, 3.83 + Math.sqrt(Math.max(0, 1 - (x / 4.5) ** 2)) * .98, z));
    }
    const curve = new THREE.CatmullRomCurve3(points);
    mesh(new THREE.TubeGeometry(curve, 28, .11, 6, false), walnut, 0, 0, 0);
    mesh(new THREE.TubeGeometry(curve, 28, .015, 5, false), brass, 0, -.115, .06);
  }
  box(wall, 0, 2.5, back, 9.6, 5, .3);
  // 实墙承载徽标，两侧高舷窗提供侧向海景，不让高对比风景穿过展品轮廓。
  box(wall, 0, 2.5, front, 4.9, 5, .36);
  box(walnut, 0, .56, front+.04, 4.9, 1.12, .4);
  for (const side of [-1, 1]) {
    box(wall, side*4.62, 2.5, front, .76, 5, .36);
    const x = side*3.34;
    box(walnut,x,.46,front,1.82,.92,.4);
    box(wall,x,4.62,front,1.82,.76,.36);
    for (const dx of [-.9,.9]) {
      box(walnut,x+dx,2.6,front+.14,.15,3.6,.2);
      box(brass,x+dx,2.6,front+.255,.018,3.6,.024);
    }
    for (const y of [.9,4.33]) box(walnut,x,y,front+.15,1.9,.12,.22);
    const archPoints = Array.from({length:25},(_,i)=> {
      const angle = Math.PI*i/24;
      return new THREE.Vector3(x+Math.cos(angle)*.88,3.56+Math.sin(angle)*.77,front+.18);
    });
    mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(archPoints),24,.055,6,false),walnut,0,0,0);
    box(walnut,x,3.55,front+.15,1.75,.05,.12);
    box(walnut,x,2.58,front+.15,.05,3.3,.12);
  }
  for (const x of [-2.4,2.4]) box(walnut,x,2.5,front+.22,.17,5,.22);
  for (const y of [1.14,4.65]) box(brass,0,y,front+.22,4.7,.025,.025);
  label("梦想从这里，驶向伟大航路", 3.4, .3, 0, 2.38, front + .22, '#19353b', '#cfb77f');
  label('ONE PIECE', 3.5, .7, 0, 3.53, front + .22, '#19353b', '#ead49a').name = 'MuseumLogoFallback';
  label("GRAND LINE · 人物档案馆", 4.5, .5, 0, 3, back - .18).rotation.y = Math.PI;
  const landscape = loader.load(museumAsset("chapters.webp"));
  landscape.colorSpace = THREE.SRGBColorSpace;
  landscape.repeat.set(.5, .5);
  landscape.offset.set(0, 0);
  const outside = mesh(new THREE.PlaneGeometry(40, 22.5), new THREE.MeshBasicMaterial({ map: landscape, color: 0xe6eef2 }), 0, 6, front - 10);
  outside.castShadow = false;
  outside.receiveShadow = false;

  function lantern(x: number, y: number, z: number, light: boolean) {
    cylinder(brass, x, y - .35, z, .18, .07);
    cylinder(brass, x, y + .35, z, .2, .08);
    const cap = mesh(new THREE.ConeGeometry(.21, .19, 8), brass, x, y + .48, z);
    cap.castShadow = false;
    cylinder(flame, x, y, z, .058, .52).castShadow = false;
    cylinder(glow, x, y, z, .17, .65).castShadow = false;
    for (let i = 0; i < 6; i++) cylinder(brass, x + Math.cos(i * Math.PI / 3) * .15, y, z + Math.sin(i * Math.PI / 3) * .15, .015, .65);
    ring(.075, .014, brass, x, y + .66, z);
    if (light) { const lamp = new THREE.PointLight(0xffc88d, 4, 6, 2); lamp.position.set(x, y, z); root.add(lamp); }
  }
  const lampStations = [-6];
  for (let z = posterStartZ + 1.7; z < back; z += 6.8) lampStations.push(z);
  for (const z of lampStations) {
    for (const side of [-1, 1]) {
      const x = side * 4.2;
      rod(new THREE.Vector3(side * 4.6, 3.8, z), new THREE.Vector3(x, 3.8, z), .035);
      lantern(x, 3.35, z, z < 8);
    }
  }
  // 无阴影聚光灯强化器物形体；轨道沿两侧布置，中央徽标保持无遮挡。
  for (const x of [-3.15, 3.15]) box(agedBrass,x,4.72,-3.65,.045,.055,7.2);
  const lightFace = new THREE.MeshBasicMaterial({ color: 0xffedcf });
  for (const item of artifacts) {
    const x = item.x, z = item.z + (item.sideDisplay ? 0 : .8);
    cylinder(agedBrass,x,4.53,z,.085,.22);
    cylinder(lightFace,x,4.413,z,.063,.008);
    const spot = new THREE.SpotLight(0xffe6c4, 16, 7, .46, .7, 2);
    spot.position.set(x,4.38,z);
    spot.target.position.set(item.x,1.35,item.z);
    root.add(spot, spot.target);
  }
  const logoLight = new THREE.PointLight(0xe0efff, 3, 6, 2);
  logoLight.position.set(0,4.25,front+1.5);root.add(logoLight);
  const rug = new THREE.MeshStandardMaterial({ color: 0x20363b, roughness: 1 });
  // 中央迎宾毯引导走向草帽，不再承托刀台。
  box(rug,0,.049,-1.65,2.0,.018,4.4);
  for(const x of [-.97,.97])box(agedBrass,x,.061,-1.65,.018,.006,4.32);
  for(const z of [-3.81,.51])box(agedBrass,0,.061,z,1.95,.006,.018);

  // 地板罗盘使用可读的嵌花纹理，落在真实地板平面上。
  const compassCanvas = document.createElement("canvas"); compassCanvas.width = compassCanvas.height = 1024;
  const ctx = compassCanvas.getContext("2d")!; ctx.translate(512, 512);
  ctx.fillStyle = "#30251b"; ctx.beginPath(); ctx.arc(0, 0, 496, 0, Math.PI * 2); ctx.fill();
  for (const radius of [492, 477, 393, 205]) { ctx.strokeStyle = "#b69759"; ctx.lineWidth = radius === 477 ? 4 : 2; ctx.beginPath(); ctx.arc(0, 0, radius, 0, Math.PI * 2); ctx.stroke(); }
  for (let i = 0; i < 16; i++) {
    ctx.save(); ctx.rotate(i * Math.PI / 8); const radius = i % 2 ? 250 : 374;
    ctx.fillStyle = i % 2 ? "#735935" : "#b79b63"; ctx.beginPath(); ctx.moveTo(0, -radius); ctx.lineTo(0, 0); ctx.lineTo(-34, -34); ctx.fill();
    ctx.fillStyle = "#4f3925"; ctx.beginPath(); ctx.moveTo(0, -radius); ctx.lineTo(0, 0); ctx.lineTo(34, -34); ctx.fill(); ctx.restore();
  }
  ctx.fillStyle = "#c8b17d"; ctx.font = "38px Georgia"; ctx.textAlign = "center";
  for (const [i, direction] of ["N", "E", "S", "W"].entries()) { ctx.save(); ctx.rotate(i * Math.PI / 2); ctx.fillText(direction, 0, -424); ctx.restore(); }
  const compassMap = new THREE.CanvasTexture(compassCanvas); compassMap.colorSpace = THREE.SRGBColorSpace;
  const medallion = mesh(new THREE.CircleGeometry(1.0, 64), new THREE.MeshStandardMaterial({ map: compassMap, roughness: .38, metalness: .2 }), 0, .046, 2.0);
  medallion.rotation.x = -Math.PI / 2; medallion.castShadow = false;
  for (const r of [.98, 1.03]) { const inlay = ring(r, .012, brass, 0, .057, 2.0); inlay.rotation.x = Math.PI / 2; }

  // 合并静态不透明网格，长展舱的抽屉、木条、铆钉不会线性增加 draw call。
  root.updateMatrixWorld(true);
  const batches = new Map<THREE.Material, THREE.Mesh[]>();
  root.traverse((object) => {
    if (!(object instanceof THREE.Mesh) || Array.isArray(object.material) || object.material.transparent) return;
    const group = batches.get(object.material) ?? [];
    group.push(object); batches.set(object.material, group);
  });
  for (const [material, objects] of batches) {
    if (objects.length < 2) continue;
    // RoundedBox 为非索引几何，圆柱/管线为索引几何；合批前统一布局。
    const parts = objects.map((object) => {
      const geometry = object.geometry.index ? object.geometry.toNonIndexed() : object.geometry.clone();
      return geometry.applyMatrix4(object.matrixWorld);
    });
    const merged = mergeGeometries(parts);
    parts.forEach((part) => part.dispose());
    if (!merged) continue;
    const combined = new THREE.Mesh(merged, material); combined.castShadow = combined.receiveShadow = true;
    root.add(combined);
    for (const object of objects) object.removeFromParent();
  }
  const retained = new Set<THREE.BufferGeometry>();
  root.traverse(o => { if (o instanceof THREE.Mesh) retained.add(o.geometry); });
  for (const objects of batches.values()) for (const object of objects) if (!retained.has(object.geometry)) object.geometry.dispose();
  boxGeometry.dispose(); cylinderGeometry.dispose(); sphereGeometry.dispose();
  root.add(buildArtifactDisplays());
  return root;
}

export function buildExhibitFrame(group: THREE.Group, trim: THREE.MeshStandardMaterial) {
  const wood = new THREE.MeshStandardMaterial({ color: 0x362416, roughness: .45 });
  function bar(w: number, h: number, d: number, x: number, y: number, z: number, material: THREE.Material) {
    const part = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
    part.position.set(x, y, z); part.castShadow = true; part.receiveShadow = true; group.add(part);
  }
  bar(1.92, 2.87, .15, 0, 0, -.07, wood);
  for (const layer of [{ w: 1.84, h: 2.8, t: .09, z: .07 }, { w: 1.69, h: 2.57, t: .025, z: .14 }]) {
    for (const y of [-layer.h / 2, layer.h / 2]) bar(layer.w, layer.t, .07, 0, y, layer.z, trim);
    for (const x of [-layer.w / 2, layer.w / 2]) bar(layer.t, layer.h, .07, x, 0, layer.z, trim);
  }
  for (const x of [-.92, .92]) for (const y of [-1.4, 1.4]) {
    const ornament = new THREE.Mesh(new THREE.SphereGeometry(.072, 12, 8), trim);
    ornament.scale.set(1, 1, .4); ornament.position.set(x, y, .13); group.add(ornament);
  }
}
