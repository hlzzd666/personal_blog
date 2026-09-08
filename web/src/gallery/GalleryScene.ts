import * as THREE from "three";
import { PointerLockControls } from "three/examples/jsm/controls/PointerLockControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { Sky } from "three/examples/jsm/objects/Sky.js";
import type { GalleryCharacter } from "../api/gallery";
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
const asset = (path: string) => `${import.meta.env.BASE_URL}gallery/${path}`;
const INTERACTION_DISTANCE = 4.5;
const MAX_POSTER_TEXTURES = 12;

export class GalleryScene {
  readonly ready: Promise<void>;
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(65, 1, 0.1, 250);
  private readonly renderer: THREE.WebGLRenderer;
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
  private readonly occluders: THREE.Object3D[] = [];
  private readonly toExhibit = new THREE.Vector3();
  private readonly forward = new THREE.Vector3();
  private readonly right = new THREE.Vector3();
  private readonly projected = new THREE.Vector3();
  private active: Exhibit | null = null;
  private water: THREE.Texture | null = null;
  private environment: THREE.WebGLRenderTarget | null = null;
  private frame = 0;
  private disposed = false;
  private loaded = false;
  private lastTime = performance.now();
  private lastNavigation = 0;
  private lastPosterRow = -1;

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
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.12;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.domElement.className = "gallery-canvas";
    this.renderer.domElement.setAttribute("aria-label", "旗舰船舱人物展馆");
    container.append(this.renderer.domElement);
    this.controls = new PointerLockControls(this.camera, this.renderer.domElement);
    this.controls.minPolarAngle = 0.25;
    this.controls.maxPolarAngle = Math.PI - 0.25;
    this.camera.position.set(0, dimensions.cameraHeight, 5.8);
    this.camera.lookAt(0, dimensions.cameraHeight, -10);
    this.scene.background = new THREE.Color(0x9acee2);
    this.scene.fog = new THREE.Fog(0xa5d4e0, 100, 230);
    this.scene.add(new THREE.HemisphereLight(0xe3f5ff, 0x736047, 1.15));
    const sun = new THREE.DirectionalLight(0xffedcd, 4.4);
    sun.position.set(-10, 20, 8);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    sun.shadow.camera.left = -18;
    sun.shadow.camera.right = 18;
    sun.shadow.camera.top = 20;
    sun.shadow.camera.bottom = -20;
    sun.shadow.camera.far = 70;
    sun.shadow.normalBias = 0.012;
    sun.shadow.bias = -0.0002;
    sun.shadow.radius = 1.5;
    sun.target.position.set(0, 0, -8);
    this.scene.add(sun.target);
    this.scene.add(sun);
    this.buildOcean();
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
      this.updatePosters();
    });
    this.animate();
  }

  lock() {
    if (this.loaded && !this.disposed) this.controls.lock();
  }
  unlock() {
    if (this.controls.isLocked) this.controls.unlock();
  }

  private async loadShip() {
    const gltf = await new GLTFLoader().loadAsync(asset("flagship/flagship.glb"));
    this.track(gltf.scene);
    if (this.disposed) {
      this.releaseResources();
      return;
    }
    const bay = gltf.scene.getObjectByName("CabinBay");
    const bow = gltf.scene.getObjectByName("BowDeck");
    const stern = gltf.scene.getObjectByName("SternDeck");
    const frame = gltf.scene.getObjectByName("ExhibitFrame");
    if (!bay || !bow || !stern || !frame) throw new Error("船舱模型缺少结构单元");
    for (let i = 0; i < this.hall.bays; i++) {
      const segment = bay.clone(true);
      segment.position.z = -i * dimensions.bayLength;
      this.scene.add(segment);
      this.occluders.push(segment);
    }
    bow.position.z = this.hall.cabinFront;
    stern.position.z = this.hall.cabinBack;
    this.scene.add(bow, stern);
    this.occluders.push(bow, stern);
    for (const exhibit of this.exhibits) {
      const shell = frame.clone(true);
      shell.traverse((object) => {
        if (!(object instanceof THREE.Mesh)) return;
        if (
          object.material instanceof THREE.MeshStandardMaterial &&
          object.material.name === "Aged brass"
        ) {
          exhibit.trim.dispose();
          this.materials.delete(exhibit.trim);
          exhibit.trim = object.material.clone();
          exhibit.trim.emissive.set(0xd9953d);
          exhibit.trim.emissiveIntensity = 0;
          object.material = exhibit.trim;
          this.materials.add(exhibit.trim);
        }
      });
      exhibit.group.add(shell);
    }
    this.scene.updateMatrixWorld(true);
  }

  private track(root: THREE.Object3D) {
    root.traverse((object) => {
      if (!(object instanceof THREE.Mesh)) return;
      object.castShadow = true;
      object.receiveShadow = true;
      this.geometries.add(object.geometry);
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      for (const mat of materials) {
        this.materials.add(mat);
        for (const value of Object.values(mat))
          if (value instanceof THREE.Texture) this.textures.add(value);
      }
    });
  }

  private buildOcean() {
    const water = new THREE.TextureLoader().load(asset("generated/calm-ocean-color-tile.png"));
    water.colorSpace = THREE.SRGBColorSpace;
    water.wrapS = water.wrapT = THREE.RepeatWrapping;
    water.repeat.set(55, 55);
    this.water = water;
    this.textures.add(water);
    const ocean = new THREE.Mesh(
      new THREE.PlaneGeometry(500, 500),
      new THREE.MeshStandardMaterial({
        map: water,
        color: 0x4da6b0,
        roughness: 0.4,
        metalness: 0.15,
      }),
    );
    ocean.rotation.x = -Math.PI / 2;
    ocean.position.y = -1.55;
    this.track(ocean);
    this.scene.add(ocean);
    const sky = new Sky();
    sky.scale.setScalar(240);
    sky.material.uniforms.turbidity!.value = 2;
    sky.material.uniforms.rayleigh!.value = 1.4;
    sky.material.uniforms.sunPosition!.value.set(-10, 20, 8).normalize();
    this.track(sky);
    this.scene.add(sky);
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.environment = pmrem.fromScene(this.scene, 0.04, 0.1, 250);
    this.scene.environment = this.environment.texture;
    this.scene.environmentIntensity = 0.2;
    pmrem.dispose();
  }

  private buildExhibits(characters: GalleryCharacter[]) {
    const backing = new THREE.BoxGeometry(1.82, 2.7, 0.1);
    const portrait = new THREE.PlaneGeometry(1.6, 2.4);
    const horizontal = new THREE.BoxGeometry(1.86, 0.085, 0.12);
    const vertical = new THREE.BoxGeometry(0.085, 2.62, 0.12);
    const plaque = new THREE.PlaneGeometry(1.8, 0.25);
    const backingMat = new THREE.MeshStandardMaterial({ color: 0x123f3b, roughness: 0.8 });
    for (const [index, character] of characters.entries()) {
      const group = new THREE.Group();
      group.name = `exhibit-${character.id}`;
      const { x, z, side } = exhibitPosition(index);
      group.position.set(x, 2.05, z);
      group.rotation.y = side < 0 ? Math.PI / 2 : -Math.PI / 2;
      const fallback = this.posterPlaceholder(character, index + 1);
      this.textures.add(fallback);
      const poster = new THREE.MeshStandardMaterial({ map: fallback, roughness: 0.84 });
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
      this.materials.add(trim);
      const canvas = document.createElement("canvas");
      canvas.width = 512;
      canvas.height = 72;
      const ctx = canvas.getContext("2d")!;
      ctx.fillStyle = "#113d39";
      ctx.fillRect(0, 0, 512, 72);
      ctx.fillStyle = "#f3d292";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = '24px "Noto Sans SC", sans-serif';
      ctx.fillText(`${String(index + 1).padStart(2, "0")}  ${character.name}`, 256, 36, 480);
      const labelTexture = new THREE.CanvasTexture(canvas);
      labelTexture.colorSpace = THREE.SRGBColorSpace;
      const label = new THREE.Mesh(plaque, new THREE.MeshBasicMaterial({ map: labelTexture }));
      label.position.set(0, -1.53, 0.08);
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
    [backing, portrait, horizontal, vertical, plaque].forEach((g) => this.geometries.add(g));
    this.materials.add(backingMat);
  }

  private posterPlaceholder(character: GalleryCharacter, slot: number) {
    const canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 384;
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = "#d6e3db";
    ctx.fillRect(0, 0, 256, 384);
    ctx.strokeStyle = "#799a8b";
    ctx.lineWidth = 2;
    ctx.strokeRect(12, 12, 232, 360);
    ctx.textAlign = "center";
    ctx.fillStyle = "#355c52";
    ctx.font = "16px sans-serif";
    ctx.fillText("GRAND LINE", 128, 52);
    ctx.font = "64px serif";
    ctx.fillText(String(slot).padStart(2, "0"), 128, 150);
    ctx.font = 'bold 23px "Noto Sans SC", sans-serif';
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
    const row = Math.max(0, Math.round(-this.camera.position.z / dimensions.bayLength));
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
          ctx.fillStyle = "#d6e3db";
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
    for (const exhibit of this.exhibits)
      if (exhibit.url === url) {
        exhibit.poster.map = texture;
        exhibit.poster.needsUpdate = true;
      }
  }

  private readonly handleLock = () => this.callbacks.onLockChange(true);
  private readonly handleUnlock = () => {
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
  private readonly lockError = () =>
    this.callbacks.onUnavailable("浏览器未能开启视角控制，已切换至人物档案。");
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
    if (this.active) this.callbacks.onOpenCharacter(this.active.character, this.active.slot);
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
    this.velocity.lerp(this.forward.multiplyScalar(4.8), 1 - Math.exp(-12 * delta));
    const x = this.camera.position.x + this.velocity.x * delta;
    if (isWalkable(x, this.camera.position.z, this.hall)) this.camera.position.x = x;
    else this.velocity.x = 0;
    const z = this.camera.position.z + this.velocity.z * delta;
    if (isWalkable(this.camera.position.x, z, this.hall)) this.camera.position.z = z;
    else this.velocity.z = 0;
  }

  private interaction() {
    let active: Exhibit | null = null;
    if (this.controls.isLocked) {
      this.raycaster.setFromCamera(new THREE.Vector2(), this.camera);
      const hit = this.raycaster.intersectObjects(
        this.exhibits.map((e) => e.group),
        true,
      )[0];
      if (hit && hit.distance <= INTERACTION_DISTANCE) {
        let object: THREE.Object3D | null = hit.object;
        while (object && !active) {
          active = this.exhibits.find((e) => e.group === object) ?? null;
          object = object.parent;
        }
      }
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
      this.projected.y = 3.65;
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
      if (this.occlusionRay.intersectObjects(this.occluders, true).length) continue;
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
      zone:
        this.camera.position.z > this.hall.cabinBack
          ? "艉甲板"
          : this.camera.position.z < this.hall.cabinFront
            ? "艏甲板"
            : "人物展舱",
    });
  }

  private readonly animate = (now = performance.now()) => {
    if (this.disposed) return;
    this.frame = requestAnimationFrame(this.animate);
    const delta = Math.min((now - this.lastTime) / 1000, 0.05);
    this.lastTime = now;
    if (document.hidden) return;
    this.move(delta);
    this.camera.updateMatrixWorld();
    if (this.loaded) {
      this.updatePosters();
      this.interaction();
    }
    if (!this.reducedMotion && this.water)
      this.water.offset.x = (this.water.offset.x + delta * 0.009) % 1;
    if (now - this.lastNavigation > 100) {
      this.navigation();
      this.lastNavigation = now;
    }
    this.renderer.render(this.scene, this.camera);
  };
  private readonly resize = () => {
    const width = Math.max(this.container.clientWidth, 1),
      height = Math.max(this.container.clientHeight, 1);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
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
    this.scene.clear();
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
