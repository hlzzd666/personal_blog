import * as THREE from "three";
import { PointerLockControls } from "three/examples/jsm/controls/PointerLockControls.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { SSAOPass } from "three/examples/jsm/postprocessing/SSAOPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import { buildMuseumRoom, buildExhibitFrame } from "./MuseumRoom";
import { museumAsset, portraitIndex, portraitRegion } from "./curation";
import type { GalleryCharacter } from "../api/gallery";
import { artifacts, posterStartZ, type MuseumArtifact } from "./artifacts";
import { createLayout, dimensions, exhibitPosition, isWalkable, type HallLayout } from "./layout";

export type NavigationMarker = {
  slot: number;
  name: string;
  distance: number;
  x: number;
  z: number;
  screenX: number;
  screenY: number;
  near: boolean;
};
export type NavigationState = {
  x: number;
  z: number;
  heading: number;
  hall: HallLayout;
  markers: NavigationMarker[];
  zone: string;
};
type Callbacks = {
  onActiveArtifact?: (artifact: MuseumArtifact | null) => void;
  onOpenArtifact?: (artifact: MuseumArtifact) => void;
  onActiveCharacter: (character: GalleryCharacter | null, slot: number | null) => void;
  onLockChange: (locked: boolean) => void;
  onOpenCharacter: (character: GalleryCharacter, slot: number) => void;
  onNavigation: (state: NavigationState) => void;
  onUnavailable: (reason: string) => void;
};
type Exhibit = {
  group: THREE.Group;
  character: GalleryCharacter;
  slot: number;
  poster: THREE.MeshStandardMaterial;
  fallback: THREE.Texture;
  trim: THREE.MeshStandardMaterial;
  url: string | null;
};
const INTERACTION_DISTANCE = 4.5;
const MAX_POSTER_TEXTURES = 12;

// 接触阴影半分辨率采样，最终画面仍按画布分辨率输出。
class MuseumAmbientOcclusion extends SSAOPass {
  override setSize(width: number, height: number) {
    super.setSize(Math.max(1, Math.ceil(width / 2)), Math.max(1, Math.ceil(height / 2)));
  }
}

export class GalleryScene {
  readonly ready: Promise<void>;
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(58, 1, 0.08, 180);
  private readonly renderer: THREE.WebGLRenderer;
  private readonly composer: EffectComposer;
  private readonly ambientOcclusion: SSAOPass;
  private readonly controls: PointerLockControls;
  private readonly resizeObserver: ResizeObserver;
  private readonly keys = new Set<string>();
  private readonly geometries = new Set<THREE.BufferGeometry>();
  private readonly materials = new Set<THREE.Material>();
  private readonly textures = new Set<THREE.Texture>();
  private readonly exhibits: Exhibit[] = [];
  private readonly posterCache = new Map<string, THREE.Texture>();
  private readonly pending = new Set<string>();
  private readonly failed = new Set<string>();
  private posterUrls = new Set<string>();
  private readonly hall: HallLayout;
  private readonly velocity = new THREE.Vector3();
  private readonly raycaster = new THREE.Raycaster();
  private readonly occlusionRay = new THREE.Raycaster();
  private readonly occlusionBoxes: THREE.Box3[] = [];
  private readonly occlusionHit = new THREE.Vector3();
  private readonly toExhibit = new THREE.Vector3();
  private readonly forward = new THREE.Vector3();
  private readonly right = new THREE.Vector3();
  private readonly projected = new THREE.Vector3();
  private readonly rotatingDisplays = new Map<string, { pivot: THREE.Group; sphere: THREE.Sphere }>();
  private readonly displayFrustum = new THREE.Frustum();
  private readonly viewProjection = new THREE.Matrix4();
  private rotationShadowTime = 0;
  private active: Exhibit | null = null;
  private activeArtifact: MuseumArtifact | null = null;
  private readonly artifactBoxes = artifacts.map(item => new THREE.Box3(
    new THREE.Vector3(item.x - item.width / 2, .15, item.z - item.depth / 2),
    new THREE.Vector3(item.x + item.width / 2, item.height, item.z + item.depth / 2),
  ));
  private running = true;
  private environment: THREE.WebGLRenderTarget | null = null;
  private frame = 0;
  private disposed = false;
  private loaded = false;
  private lastTime = performance.now();
  private lastNavigation = 0;
  private lastPosterRow = -1;
  private needsRender = true;
  private lockPending = false;

  constructor(
    private readonly container: HTMLElement,
    characters: GalleryCharacter[],
    private readonly reducedMotion: boolean,
    private readonly callbacks: Callbacks,
  ) {
    const ordered = characters
      .filter((item) => item.is_visible)
      .sort((a, b) => a.sort_order - b.sort_order || a.id - b.id)
      .slice(0, dimensions.maximumCharacters);
    this.hall = createLayout(ordered.length);
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: "high-performance",
    });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 1.25));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFShadowMap;
    this.renderer.shadowMap.autoUpdate = false;
    this.renderer.shadowMap.needsUpdate = true;
    this.renderer.domElement.className = "gallery-canvas";
    this.renderer.domElement.setAttribute("aria-label", "旗舰船舱人物展馆");
    container.append(this.renderer.domElement);
    this.controls = new PointerLockControls(this.camera, this.renderer.domElement);
    this.controls.minPolarAngle = 0.25;
    this.controls.maxPolarAngle = Math.PI - 0.25;
    this.camera.position.set(-.35, dimensions.cameraHeight, 2.8);
    this.camera.lookAt(0, 2.05, -5);
    this.scene.background = new THREE.Color(0x151a1c);
    this.scene.fog = new THREE.Fog(0x151a1c, 35, 110);
    this.scene.add(new THREE.HemisphereLight(0xdde8ef, 0x716c5e, 1.3));
    const sun = new THREE.DirectionalLight(0xffebd2, 1.3);
    sun.position.set(-3, 7, -14);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    sun.shadow.camera.left = -12;
    sun.shadow.camera.right = 12;
    sun.shadow.camera.top = 12;
    sun.shadow.camera.bottom = -12;
    sun.shadow.camera.far = 70;
    sun.shadow.normalBias = 0.012;
    sun.shadow.bias = -0.0002;
    sun.shadow.radius = 1.5;
    sun.target.position.set(1.5, 0, 3);
    this.scene.add(sun.target);
    this.scene.add(sun);
    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    this.ambientOcclusion = new MuseumAmbientOcclusion(this.scene, this.camera, 1, 1, 12);
    this.ambientOcclusion.kernelRadius = .4;
    this.ambientOcclusion.minDistance = .001;
    this.ambientOcclusion.maxDistance = .12;
    this.composer.addPass(this.ambientOcclusion);
    this.composer.addPass(new OutputPass());
    const environmentScene = new RoomEnvironment();
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.environment = pmrem.fromScene(environmentScene, .04);
    this.scene.environment = this.environment.texture;
    this.scene.environmentIntensity = .65;
    environmentScene.dispose();
    pmrem.dispose();
    this.buildExhibits(ordered);
    this.controls.addEventListener("lock", this.handleLock);
    this.controls.addEventListener("unlock", this.handleUnlock);
    window.addEventListener("keydown", this.keyDown);
    window.addEventListener("keyup", this.keyUp);
    window.addEventListener("blur", this.pause);
    document.addEventListener("visibilitychange", this.visibilityChange);
    document.addEventListener("pointerlockerror", this.lockError);
    this.renderer.domElement.addEventListener("click", this.click);
    this.renderer.domElement.addEventListener("webglcontextlost", this.contextLost);
    this.resizeObserver = new ResizeObserver(this.resize);
    this.resizeObserver.observe(container);
    this.resize();
    this.ready = this.loadShip().then(() => {
      if (this.disposed) return;
      this.loaded = true;
      this.renderer.shadowMap.needsUpdate = true;
      this.needsRender = true;
      this.updatePosters();
    });
    this.animate();
  }

  lock() {
    if (!this.loaded || this.disposed) return;
    this.lockPending = true;
    // 部分浏览器仅拒绝 Promise，未同步发出 pointerlockerror。
    try {
      const request = this.renderer.domElement.requestPointerLock();
      void Promise.resolve(request).catch(this.lockError);
    } catch { this.lockError(); }
  }
  unlock() {
    this.lockPending = false;
    if (this.controls.isLocked) this.controls.unlock();
  }

  setRunning(value: boolean) {
    this.running = value;
    this.needsRender = true;
    this.lastTime = performance.now();
    if (!value) this.unlock();
  }

  private async loadShip() {
    const manager = new THREE.LoadingManager();
    const complete = new Promise<void>((resolve) => { manager.onLoad = resolve; });
    const loader = new THREE.TextureLoader(manager);
    const room = buildMuseumRoom(this.hall, loader);
    this.track(room);
    this.scene.add(room);
    for (const id of ['gum-gum', 'going-merry']) {
      const fallback = room.getObjectByName(id === 'going-merry' ? 'DisplayShipFallback' : `artifact-fallback-${id}`);
      if (fallback) this.addRotatingDisplay(fallback, artifacts.find(item => item.id === id)!);
    }
    // 单层船舱仅家具和侧墙立柱会遮挡展签，避免对整舱三角面反复求交。
    const block = (x1: number, y1: number, z1: number, x2: number, y2: number, z2: number) =>
      this.occlusionBoxes.push(new THREE.Box3(new THREE.Vector3(x1, y1, z1), new THREE.Vector3(x2, y2, z2)));
    for (const item of artifacts) block(item.x - item.width / 2, 0, item.z - item.depth / 2,
      item.x + item.width / 2, item.height, item.z + item.depth / 2);
    for (let z = -2; z < this.hall.cabinBack; z += 3.4) {
      block(-4.8, 0, z - .2, -4.33, 5, z + .2);
      block(4.33, 0, z - .2, 4.8, 5, z + .2);
    }
    const atlas = loader.load(museumAsset("portraits.webp"), (texture) => {
      if (this.disposed) { texture.dispose(); return; }
      texture.colorSpace = THREE.SRGBColorSpace;
      for (const exhibit of this.exhibits) {
        const index = portraitIndex(exhibit.character.name);
        if (index < 0) continue;
        const portrait = texture.clone();
        const region = portraitRegion(index);
        portrait.repeat.set(region.width, region.height);
        portrait.offset.set(region.x, 1 - region.y - region.height);
        portrait.needsUpdate = true;
        this.textures.add(portrait);
        if (exhibit.poster.map === exhibit.fallback) exhibit.poster.map = portrait;
        this.textures.delete(exhibit.fallback);
        exhibit.fallback.dispose();
        exhibit.fallback = portrait;
        exhibit.poster.needsUpdate = true;
      }
    });
    this.textures.add(atlas);
    await complete;
    if (this.disposed) return;
    await Promise.all([this.loadArtifacts(), this.loadMuseumLogo()]);
    if (this.disposed) return;
    // 船模沿用站内已署名资产；独立加载，失败时保留柜内程序化模型。
    void new GLTFLoader().loadAsync(import.meta.env.BASE_URL + "models/one_piece_-going_merry.glb").then((gltf) => {
      if (this.disposed) {
        const geometries = new Set<THREE.BufferGeometry>(), materials = new Set<THREE.Material>(), textures = new Set<THREE.Texture>();
        gltf.scene.traverse(object => {
          if (!(object instanceof THREE.Mesh)) return;
          geometries.add(object.geometry);
          for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
            materials.add(material);
            Object.values(material).forEach(value => { if (value instanceof THREE.Texture) textures.add(value); });
          }
        });
        geometries.forEach(g => g.dispose()); materials.forEach(m => m.dispose()); textures.forEach(t => t.dispose());
        return;
      }
      const bounds = new THREE.Box3().setFromObject(gltf.scene), size = bounds.getSize(new THREE.Vector3());
      const scale = Math.min(1.5 / size.x, 1.45 / size.y, 1.85 / size.z);
      gltf.scene.scale.setScalar(scale);
      const center = bounds.getCenter(new THREE.Vector3()).multiplyScalar(scale);
      const stand = artifacts.find(item => item.id === 'going-merry')!;
      gltf.scene.position.set(stand.x - center.x, 1.1 - bounds.min.y * scale, stand.z - center.z);
      gltf.scene.updateMatrixWorld(true);
      // 原船模由大量重复节点组成；先按材质合批，再整体绕展台中心旋转。
      const batches = new Map<THREE.Material, THREE.Mesh[]>();
      gltf.scene.traverse(object => {
        if (!(object instanceof THREE.Mesh) || Array.isArray(object.material)) return;
        const meshes = batches.get(object.material) ?? [];
        meshes.push(object); batches.set(object.material, meshes);
      });
      this.track(gltf.scene);
      const model = new THREE.Group();
      model.name = "DisplayShip";
      for (const [material, meshes] of batches) {
        const parts = meshes.map(mesh => {
          const geometry = mesh.geometry.index ? mesh.geometry.toNonIndexed() : mesh.geometry.clone();
          return geometry.applyMatrix4(mesh.matrixWorld);
        });
        const geometry = mergeGeometries(parts);
        parts.forEach(part => part.dispose());
        if (geometry) {
          const mesh = new THREE.Mesh(geometry, material);
          mesh.castShadow = mesh.receiveShadow = true;
          model.add(mesh);
        } else {
          for (const original of meshes) { original.removeFromParent(); original.matrix.copy(original.matrixWorld); original.matrixAutoUpdate = false; model.add(original); }
        }
      }
      this.scene.getObjectByName("DisplayShipFallback")?.removeFromParent();
      this.track(model);
      this.scene.add(model);
      this.addRotatingDisplay(model, stand);
      this.renderer.shadowMap.needsUpdate = true;
      this.needsRender = true;
    }).catch(() => { /* 柜内原有船模仍然可见，不阻断漫游。 */ });
    this.scene.updateMatrixWorld(true);
  }

  private track(root: THREE.Object3D) {
    root.traverse((object) => {
      if (!(object instanceof THREE.Mesh)) return;
      this.geometries.add(object.geometry);
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      for (const mat of materials) {
        this.materials.add(mat);
        for (const value of Object.values(mat))
          if (value instanceof THREE.Texture) this.textures.add(value);
      }
    });
  }

  private addRotatingDisplay(model: THREE.Object3D, stand: MuseumArtifact) {
    this.rotatingDisplays.get(stand.id)?.pivot.removeFromParent();
    const pivot = new THREE.Group();
    pivot.name = `rotating-display-${stand.id}`;
    pivot.position.set(stand.x, stand.plinthHeight ?? 1.05, stand.z);
    this.scene.add(pivot);
    pivot.attach(model);
    // 按真实顶点计算水平旋转半径，整圈都留在展台内，避免长船模扫入通道。
    let radius = 0;
    const point = new THREE.Vector3();
    model.updateWorldMatrix(true, true);
    model.traverse(object => {
      if (!(object instanceof THREE.Mesh)) return;
      const positions = object.geometry.getAttribute('position');
      for (let i = 0; i < positions.count; i++) {
        point.fromBufferAttribute(positions, i).applyMatrix4(object.matrixWorld);
        radius = Math.max(radius, Math.hypot(point.x - stand.x, point.z - stand.z));
      }
    });
    if (radius > 0) pivot.scale.setScalar(Math.min(1, (Math.min(stand.width, stand.depth) - .15) / (2 * radius)));
    const sphere = new THREE.Box3().setFromObject(pivot).getBoundingSphere(new THREE.Sphere());
    this.rotatingDisplays.set(stand.id, { pivot, sphere });
  }

  private rotateDisplays(delta: number) {
    if (this.reducedMotion || !this.controls.isLocked) return;
    this.displayFrustum.setFromProjectionMatrix(this.viewProjection.multiplyMatrices(this.camera.projectionMatrix, this.camera.matrixWorldInverse));
    let changed = false;
    for (const { pivot, sphere } of this.rotatingDisplays.values()) {
      if (!this.displayFrustum.intersectsSphere(sphere)) continue;
      pivot.rotation.y = (pivot.rotation.y + delta * Math.PI / 24) % (Math.PI * 2);
      changed = true;
    }
    // 48 秒转一圈；慢速展示的阴影限频更新，保留舱室静态阴影的性能收益。
    if (changed) {
      this.rotationShadowTime += delta;
      if (this.rotationShadowTime >= 1 / 15) {
        this.renderer.shadowMap.needsUpdate = true;
        this.rotationShadowTime = 0;
      }
    }
  }

  private async loadMuseumLogo() {
    try {
      const { scene: model } = await new GLTFLoader().loadAsync(import.meta.env.BASE_URL + 'gallery/artifacts/one-piece-logo.glb');
      this.track(model);
      if (this.disposed) { this.releaseResources(); return; }
      const bounds = new THREE.Box3().setFromObject(model), size = bounds.getSize(new THREE.Vector3());
      const scale = Math.min(3.5 / size.x, 1.22 / size.y);
      const center = bounds.getCenter(new THREE.Vector3());
      model.scale.setScalar(scale);
      model.position.set(-center.x * scale, 3.53 - center.y * scale, this.hall.cabinFront + .36 - bounds.min.z * scale);
      model.name = 'MuseumLogo';
      model.traverse(object => {
        if (object instanceof THREE.Mesh) object.receiveShadow = true;
      });
      this.scene.getObjectByName('MuseumLogoFallback')?.removeFromParent();
      this.scene.add(model);
    } catch {
      // 装饰素材失败时仍显示文字铭牌，参观和展品交互保持可用。
    }
  }

  private async loadArtifacts() {
    const loader = new GLTFLoader();
    await Promise.all(artifacts.filter(item => item.id !== 'going-merry').map(async item => {
      try {
        const { scene: model } = await loader.loadAsync(import.meta.env.BASE_URL + `gallery/artifacts/${item.id}.glb`);
        if (this.disposed) {
          // 路由离开后才完成的资源不能重新进入场景，也需要释放 GPU 资源。
          this.track(model);
          this.releaseResources();
          return;
        }
        if (item.sideDisplay) model.rotation.y = item.displayYaw ?? Math.PI / 2;
        const bounds = new THREE.Box3().setFromObject(model), size = bounds.getSize(new THREE.Vector3());
        const plinthHeight = item.plinthHeight ?? 1.05;
        const scale = Math.min((item.width - .15) / size.x, (item.height - plinthHeight - .05) / size.y, (item.depth - .15) / size.z);
        const center = bounds.getCenter(new THREE.Vector3());
        model.scale.setScalar(scale);
        model.position.set(item.x - center.x * scale, plinthHeight + .035 - bounds.min.y * scale, item.z - center.z * scale);
        model.name = `artifact-model-${item.id}`;
        model.traverse(object => {
          if (!(object instanceof THREE.Mesh)) return;
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          object.castShadow = materials.every(material => !material.transparent);
          object.receiveShadow = true;
          for (const material of materials) {
            if (material.transparent) material.depthWrite = false;
            for (const value of Object.values(material)) {
              if (value instanceof THREE.Texture) value.anisotropy = Math.min(4, this.renderer.capabilities.getMaxAnisotropy());
            }
          }
        });
        this.track(model);
        this.scene.getObjectByName(`artifact-fallback-${item.id}`)?.removeFromParent();
        this.scene.add(model);
        if (item.id === 'gum-gum') this.addRotatingDisplay(model, item);
      } catch {
        // 单件文件失效不阻断展馆；保留该物件的备用造型和展签。
      }
    }));
  }

  private buildExhibits(characters: GalleryCharacter[]) {
    const portrait = new THREE.PlaneGeometry(1.6, 2.4);
    const plaque = new THREE.PlaneGeometry(1.8, 0.25);
    for (const [index, character] of characters.entries()) {
      const group = new THREE.Group();
      group.name = `exhibit-${character.id}`;
      const { x, z, side } = exhibitPosition(index);
      group.position.set(x, 2.7, z);
      group.rotation.y = side < 0 ? Math.PI / 2 : -Math.PI / 2;
      const fallback = this.posterPlaceholder(character, index + 1);
      this.textures.add(fallback);
      const poster = new THREE.MeshStandardMaterial({ map: fallback, roughness: .82, emissive: 0xa8874f, emissiveIntensity: .08 });
      const trim = new THREE.MeshStandardMaterial({
        color: 0xbd9654,
        roughness: 0.38,
        metalness: 0.65,
        emissive: 0xd9953d,
        emissiveIntensity: 0,
      });
      const image = new THREE.Mesh(portrait, poster);
      image.position.z = 0.085;
      group.add(image);
      buildExhibitFrame(group, trim);
      this.materials.add(trim);
      const canvas = document.createElement("canvas");
      canvas.width = 512;
      canvas.height = 72;
      const ctx = canvas.getContext("2d")!;
      ctx.fillStyle = "#cbbb97";
      ctx.fillRect(0, 0, 512, 72);
      ctx.fillStyle = "#30281e";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = '24px "Museum Sans", sans-serif';
      ctx.fillText(`${String(index + 1).padStart(2, "0")}  ${character.name}`, 256, 36, 480);
      const labelTexture = new THREE.CanvasTexture(canvas);
      labelTexture.colorSpace = THREE.SRGBColorSpace;
      const label = new THREE.Mesh(plaque, new THREE.MeshBasicMaterial({ map: labelTexture }));
      label.position.set(0, -1.6, 0.08);
      group.add(label);
      const numberCanvas = document.createElement("canvas");
      numberCanvas.width = numberCanvas.height = 96;
      const numberContext = numberCanvas.getContext("2d")!;
      numberContext.font = "56px serif";
      numberContext.textAlign = "center";
      numberContext.textBaseline = "middle";
      numberContext.fillStyle = "#26342c";
      numberContext.fillText(String(index + 1), 48, 49);
      const numberMap = new THREE.CanvasTexture(numberCanvas);
      numberMap.colorSpace = THREE.SRGBColorSpace;
      const number = new THREE.Mesh(
        new THREE.PlaneGeometry(0.22, 0.22),
        new THREE.MeshBasicMaterial({ map: numberMap, transparent: true, depthWrite: false }),
      );
      number.position.set(0, 1.57, 0.062);
      group.add(number);
      this.track(group);
      this.scene.add(group);
      this.exhibits.push({
        group,
        character,
        slot: index + 1,
        poster,
        trim,
        fallback,
        url: character.poster_url ? localPosterUrl(character.poster_url) : null,
      });
    }
    // 空展馆没有对象引用这些几何体，仍统一登记以确保释放。
    [portrait, plaque].forEach((g) => this.geometries.add(g));
  }

  private posterPlaceholder(character: GalleryCharacter, slot: number) {
    const canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 384;
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = "#382a1c";
    ctx.fillRect(0, 0, 256, 384);
    ctx.strokeStyle = "#ad8b52";
    ctx.lineWidth = 2;
    ctx.strokeRect(12, 12, 232, 360);
    ctx.textAlign = "center";
    ctx.fillStyle = "#d6be8a";
    ctx.font = "16px sans-serif";
    ctx.fillText("GRAND LINE", 128, 52);
    ctx.font = "64px serif";
    ctx.fillText(String(slot).padStart(2, "0"), 128, 150);
    ctx.font = 'bold 23px "Museum Sans", sans-serif';
    const letters = Array.from(character.name);
    for (let i = 0; i < letters.length; i += 8)
      ctx.fillText(letters.slice(i, i + 8).join(""), 128, 212 + (i / 8) * 29, 216);
    ctx.font = "14px sans-serif";
    ctx.fillText(character.epithet, 128, 304, 212);
    ctx.fillText(character.bounty, 128, 343, 212);
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    return texture;
  }

  private updatePosters() {
    const row = Math.max(0, Math.round(this.camera.position.z / dimensions.bayLength));
    if (row === this.lastPosterRow) return;
    this.lastPosterRow = row;
    const nearby = [...this.exhibits]
      .sort(
        (a, b) =>
          Math.abs(a.group.position.z - this.camera.position.z) -
          Math.abs(b.group.position.z - this.camera.position.z),
      )
      .slice(0, MAX_POSTER_TEXTURES);
    this.posterUrls = new Set(nearby.flatMap((e) => (e.url ? [e.url] : [])));
    for (const exhibit of this.exhibits) {
      if (!exhibit.url || !this.posterUrls.has(exhibit.url)) {
        exhibit.poster.map = exhibit.fallback;
        exhibit.poster.needsUpdate = true;
      }
    }
    for (const [url, texture] of this.posterCache) {
      if (!this.posterUrls.has(url)) {
        texture.dispose();
        this.textures.delete(texture);
        this.posterCache.delete(url);
      }
    }
    for (const url of this.posterUrls) {
      const cached = this.posterCache.get(url);
      if (cached) {
        this.applyPoster(url, cached);
        continue;
      }
      if (this.pending.has(url) || this.failed.has(url)) continue;
      this.pending.add(url);
      new THREE.ImageLoader().setCrossOrigin("anonymous").load(
        url,
        (image) => {
          this.pending.delete(url);
          if (this.disposed || !this.posterUrls.has(url)) return;
          const canvas = document.createElement("canvas");
          canvas.width = 512;
          canvas.height = 768;
          const ctx = canvas.getContext("2d")!;
          ctx.fillStyle = "#382a1c";
          ctx.fillRect(0, 0, 512, 768);
          const scale = Math.min(512 / image.width, 768 / image.height);
          ctx.drawImage(
            image,
            (512 - image.width * scale) / 2,
            (768 - image.height * scale) / 2,
            image.width * scale,
            image.height * scale,
          );
          const texture = new THREE.CanvasTexture(canvas);
          texture.colorSpace = THREE.SRGBColorSpace;
          texture.anisotropy = Math.min(4, this.renderer.capabilities.getMaxAnisotropy());
          this.textures.add(texture);
          this.posterCache.set(url, texture);
          this.applyPoster(url, texture);
        },
        undefined,
        () => {
          this.pending.delete(url);
          this.failed.add(url);
        },
      );
    }
  }
  private applyPoster(url: string, texture: THREE.Texture) {
    this.needsRender = true;
    for (const exhibit of this.exhibits)
      if (exhibit.url === url) {
        exhibit.poster.map = texture;
        exhibit.poster.needsUpdate = true;
      }
  }

  private readonly handleLock = () => {
    this.lockPending = false;
    this.callbacks.onLockChange(true);
  };
  private readonly handleUnlock = () => {
    this.lockPending = false;
    this.needsRender = true;
    this.keys.clear();
    this.velocity.set(0, 0, 0);
    this.callbacks.onLockChange(false);
  };
  private readonly pause = () => {
    this.keys.clear();
    this.velocity.set(0, 0, 0);
    this.unlock();
  };
  private readonly visibilityChange = () => {
    if (document.hidden) this.pause();
  };
  private readonly lockError = () => {
    // 成功锁定后立即按 Esc，迟到的 Promise 拒绝不应把正常暂停当作设备故障。
    if (!this.lockPending) return;
    this.lockPending = false;
    // 浏览器已产生错误事件时，先退出当前回调栈再销毁控制器。
    queueMicrotask(() => { if (!this.disposed) this.callbacks.onUnavailable("浏览器未能开启视角控制，已切换至人物档案。"); });
  };
  private readonly contextLost = (event: Event) => {
    event.preventDefault();
    this.callbacks.onUnavailable("图形连接已中断，已切换至人物档案。");
  };
  private readonly keyDown = (event: KeyboardEvent) => {
    if (!this.controls.isLocked) return;
    if (event.code === "Escape") {
      this.unlock();
      return;
    }
    if (
      [
        "KeyW",
        "KeyA",
        "KeyS",
        "KeyD",
        "ArrowUp",
        "ArrowDown",
        "ArrowLeft",
        "ArrowRight",
        "KeyE",
      ].includes(event.code)
    )
      event.preventDefault();
    this.keys.add(event.code);
    if (event.code === "KeyE" && !event.repeat) this.openActive();
  };
  private readonly keyUp = (event: KeyboardEvent) => {
    this.keys.delete(event.code);
  };
  private readonly click = () => {
    if (this.controls.isLocked) this.openActive();
  };
  private openActive() {
    if (this.activeArtifact) this.callbacks.onOpenArtifact?.(this.activeArtifact);
    else if (this.active) this.callbacks.onOpenCharacter(this.active.character, this.active.slot);
  }

  private move(delta: number) {
    if (!this.controls.isLocked) return;
    this.camera.getWorldDirection(this.forward);
    this.forward.y = 0;
    this.forward.normalize();
    this.right.crossVectors(this.forward, this.camera.up).normalize();
    const f =
      Number(this.keys.has("KeyW") || this.keys.has("ArrowUp")) -
      Number(this.keys.has("KeyS") || this.keys.has("ArrowDown"));
    const s =
      Number(this.keys.has("KeyD") || this.keys.has("ArrowRight")) -
      Number(this.keys.has("KeyA") || this.keys.has("ArrowLeft"));
    this.forward.multiplyScalar(f).addScaledVector(this.right, s);
    if (this.forward.lengthSq() > 1) this.forward.normalize();
    this.velocity.lerp(this.forward.multiplyScalar(3.2), this.reducedMotion ? 1 : 1 - Math.exp(-12 * delta));
    const x = this.camera.position.x + this.velocity.x * delta;
    if (isWalkable(x, this.camera.position.z, this.hall)) this.camera.position.x = x;
    else this.velocity.x = 0;
    const z = this.camera.position.z + this.velocity.z * delta;
    if (isWalkable(this.camera.position.x, z, this.hall)) this.camera.position.z = z;
    else this.velocity.z = 0;
  }

  private interaction() {
    let active: Exhibit | null = null;
    let activeArtifact: MuseumArtifact | null = null;
    let artifactDistance = INTERACTION_DISTANCE;
    if (this.controls.isLocked) {
      this.raycaster.setFromCamera(new THREE.Vector2(), this.camera);
      this.raycaster.far = INTERACTION_DISTANCE;
      const hit = this.raycaster.intersectObjects(
        this.exhibits.filter(e => e.group.position.distanceTo(this.camera.position) < INTERACTION_DISTANCE + 2).map((e) => e.group),
        true,
      )[0];
      for (const [index, box] of this.artifactBoxes.entries()) {
        if (!this.raycaster.ray.intersectBox(box, this.occlusionHit)) continue;
        const distance = this.occlusionHit.distanceTo(this.camera.position);
        if (distance < artifactDistance && (!hit || distance < hit.distance)) {
          artifactDistance = distance; activeArtifact = artifacts[index]!;
        }
      }
      if (hit && hit.distance <= INTERACTION_DISTANCE) {
        let object: THREE.Object3D | null = hit.object;
        while (object && !active) {
          active = this.exhibits.find((e) => e.group === object) ?? null;
          object = object.parent;
        }
      }
    }
    if (activeArtifact) active = null;
    if (this.activeArtifact !== activeArtifact) {
      this.activeArtifact = activeArtifact;
      this.callbacks.onActiveArtifact?.(activeArtifact);
    }
    for (const exhibit of this.exhibits) {
      const near =
        this.controls.isLocked &&
        exhibit.group.position.distanceTo(this.camera.position) <= INTERACTION_DISTANCE;
      exhibit.trim.emissiveIntensity = exhibit === active ? 0.65 : near ? 0.22 : 0;
    }
    if (this.active !== active) {
      this.active = active;
      this.callbacks.onActiveCharacter(active?.character ?? null, active?.slot ?? null);
    }
  }

  private navigation() {
    this.camera.getWorldDirection(this.forward);
    const markers: NavigationMarker[] = [];
    for (const exhibit of this.exhibits) {
      const distance = exhibit.group.position.distanceTo(this.camera.position);
      if (distance > 18) continue;
      this.projected.copy(exhibit.group.position);
      // 导航数字放在画框上沿之外，避免覆盖人物面部与海报文字。
      this.projected.y = 4.35;
      this.projected.project(this.camera);
      if (
        this.projected.z < -1 ||
        this.projected.z > 1 ||
        Math.abs(this.projected.x) > 0.94 ||
        Math.abs(this.projected.y) > 0.9
      )
        continue;
      this.toExhibit.copy(exhibit.group.position).sub(this.camera.position).normalize();
      this.occlusionRay.set(this.camera.position, this.toExhibit);
      this.occlusionRay.far = distance - 0.15;
      if (this.occlusionBoxes.some(box => this.occlusionRay.ray.intersectBox(box, this.occlusionHit) &&
        this.occlusionHit.distanceTo(this.camera.position) < distance - .15)) continue;
      markers.push({
        slot: exhibit.slot,
        name: exhibit.character.name,
        distance: Math.round(distance * 10) / 10,
        x: exhibit.group.position.x,
        z: exhibit.group.position.z,
        screenX: (this.projected.x + 1) * 50,
        screenY: (1 - this.projected.y) * 50,
        near: distance <= INTERACTION_DISTANCE,
      });
    }
    this.callbacks.onNavigation({
      x: this.camera.position.x,
      z: this.camera.position.z,
      heading: Math.atan2(this.forward.x, -this.forward.z),
      hall: this.hall,
      markers,
      zone: this.camera.position.z < posterStartZ ? "道具典藏舱" : "人物长廊",
    });
  }

  private readonly animate = (now = performance.now()) => {
    if (this.disposed) return;
    this.frame = requestAnimationFrame(this.animate);
    const delta = Math.min((now - this.lastTime) / 1000, 0.05);
    this.lastTime = now;
    if (document.hidden || !this.running) return;
    if (!this.controls.isLocked && !this.needsRender) return;
    this.needsRender = false;
    this.move(delta);
    this.camera.updateMatrixWorld();
    this.rotateDisplays(delta);
    if (this.loaded) {
      this.updatePosters();
      this.interaction();
    }
    if (now - this.lastNavigation > 100) {
      this.navigation();
      this.lastNavigation = now;
    }
    this.composer.render();
  };
  private readonly resize = () => {
    const width = Math.max(this.container.clientWidth, 1),
      height = Math.max(this.container.clientHeight, 1);
    const aspect = width / height;
    // 窄桌面仍要同时容纳左舷刀架与右舷船模；用平滑的视场补偿横向视锥收窄。
    const aspectDeficit = Math.max(0, 1.9 - aspect);
    this.camera.fov = Math.min(78, 58 + aspectDeficit * 25 + aspectDeficit * aspectDeficit * 20);
    this.camera.aspect = aspect;
    this.camera.updateProjectionMatrix();
    // 高 DPI/超宽窗口限制实际像素总量，文字与 HUD 保持原生分辨率。
    const ratio = Math.min(devicePixelRatio, 1.25, Math.sqrt(2_100_000 / (width * height)));
    this.renderer.setPixelRatio(ratio);
    this.renderer.setSize(width, height, false);
    this.composer.setPixelRatio(ratio);
    this.composer.setSize(width, height);
    this.needsRender = true;
  };
  private releaseResources() {
    this.geometries.forEach((g) => g.dispose());
    this.materials.forEach((m) => m.dispose());
    this.textures.forEach((t) => {
      t.dispose();
      if (t.image instanceof ImageBitmap) t.image.close();
    });
    this.geometries.clear();
    this.materials.clear();
    this.textures.clear();
    this.posterCache.clear();
  }
  dispose() {
    if (this.disposed) return;
    this.disposed = true;
    cancelAnimationFrame(this.frame);
    this.resizeObserver.disconnect();
    this.unlock();
    this.controls.removeEventListener("lock", this.handleLock);
    this.controls.removeEventListener("unlock", this.handleUnlock);
    this.controls.dispose();
    window.removeEventListener("keydown", this.keyDown);
    window.removeEventListener("keyup", this.keyUp);
    window.removeEventListener("blur", this.pause);
    document.removeEventListener("visibilitychange", this.visibilityChange);
    document.removeEventListener("pointerlockerror", this.lockError);
    this.renderer.domElement.removeEventListener("click", this.click);
    this.renderer.domElement.removeEventListener("webglcontextlost", this.contextLost);
    this.releaseResources();
    this.scene.traverse(object => {
      if (object instanceof THREE.Light && 'shadow' in object) {
        (object as THREE.DirectionalLight).shadow?.dispose();
      }
    });
    this.scene.clear();
    this.rotatingDisplays.clear();
    this.ambientOcclusion.dispose();
    for (const pass of this.composer.passes) if (pass !== this.ambientOcclusion) pass.dispose();
    this.composer.dispose();
    this.environment?.dispose();
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }
}

export function localPosterUrl(url: string) {
  try {
    const source = new URL(url, window.location.href);
    return source.pathname.startsWith("/uploads/") ? `${source.pathname}${source.search}` : url;
  } catch {
    return url;
  }
}
