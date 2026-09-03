import * as THREE from "three";
import { PointerLockControls } from "three/examples/jsm/controls/PointerLockControls.js";

import type { GalleryCharacter } from "../api/gallery";

type GallerySceneCallbacks = {
  onActiveCharacter: (character: GalleryCharacter | null, slot: number | null) => void;
  onLockChange: (locked: boolean) => void;
  onOpenCharacter: (character: GalleryCharacter, slot: number | null) => void;
};

type ExhibitTarget = THREE.Object3D & { userData: { character?: GalleryCharacter; slot?: number } };
type HallLayout = { length: number; cameraZ: number; cameraTargetZ: number; exhibitStartZ: number };
type PosterFrame = {
  material: THREE.MeshStandardMaterial;
  row: number;
  url: string | null;
  usesLegacySource: boolean;
};

const CAMERA_HEIGHT = 1.7;
const MAX_INTERACTION_DISTANCE = 4.5;
const WALK_SPEED = 4.8;
const MIN_HALL_LENGTH = 34;
const EXHIBIT_ROW_SPACING = 3.6;
const EXHIBIT_ENTRY_CLEARANCE = 8;
const EXHIBIT_EXIT_CLEARANCE = 8;
const NAV_MARKER_SPACING = 5.85;
const WALKWAY_TILE_LENGTH = 3.2;
const WALKWAY_TILE_COLUMNS = 4;
const POSTER_TEXTURE_WIDTH = 512;
const POSTER_TEXTURE_HEIGHT = 768;
const MAX_POSTER_TEXTURES = 12;
const WATER_MAP_URL = "/gallery/generated/calm-ocean-color-tile.png";
const STONE_MAP_URL = "/gallery/generated/light-travertine-color-tile.png";
const FRAME_BRASS_MAP_URL = "/gallery/generated/frame-relief-champagne-brass-tile.png";
const COMPASS_ROSE_URL = "/gallery/generated/compass-rose-inlay.png";
const PANORAMA_URL = "/gallery/generated/sunrise-ocean-panorama-seamless.png";

export class GalleryScene {
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(66, 1, 0.1, 240);
  private readonly renderer: THREE.WebGLRenderer;
  private readonly controls: PointerLockControls;
  private readonly raycaster = new THREE.Raycaster();
  private readonly keys = new Set<string>();
  private readonly interactables: ExhibitTarget[] = [];
  private readonly geometries = new Set<THREE.BufferGeometry>();
  private readonly materials = new Set<THREE.Material>();
  private readonly textures = new Set<THREE.Texture>();
  private readonly posterFrames: PosterFrame[] = [];
  private readonly posterTextures = new Map<string, THREE.Texture>();
  private readonly posterTextureLoads = new Map<string, Promise<THREE.Texture | null>>();
  private readonly velocity = new THREE.Vector3();
  private readonly resizeObserver: ResizeObserver;
  private readonly hall: HallLayout;
  private portraitFrameShellGeometry: THREE.ExtrudeGeometry | null = null;
  private portraitFrameBackingGeometry: THREE.ExtrudeGeometry | null = null;
  private portraitFrameMatGeometry: THREE.PlaneGeometry | null = null;
  private portraitGeometry: THREE.PlaneGeometry | null = null;
  private portraitFrameRivetGeometry: THREE.SphereGeometry | null = null;
  private portraitFrameRivetInsetGeometry: THREE.SphereGeometry | null = null;
  private portraitFramePlaqueGeometry: THREE.BoxGeometry | null = null;
  private portraitFramePlaqueInsetGeometry: THREE.BoxGeometry | null = null;
  private oceanColorMap: THREE.Texture | null = null;
  private environmentTarget: THREE.WebGLRenderTarget | null = null;
  private animationFrame = 0;
  private disposed = false;
  private activeExhibit: ExhibitTarget | null = null;
  private posterWindowKey = "";
  private posterWindowUrls = new Set<string>();
  private lastFrameAt = performance.now();

  constructor(
    private readonly container: HTMLElement,
    characters: GalleryCharacter[],
    private readonly reducedMotion: boolean,
    private readonly callbacks: GallerySceneCallbacks,
  ) {
    const orderedCharacters = [...characters]
      .sort((left, right) => left.sort_order - right.sort_order || left.id - right.id)
      .slice(0, 40);
    this.hall = createHallLayout(orderedCharacters.length);
    this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.6));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.12;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFShadowMap;
    this.renderer.domElement.className = "gallery-canvas";
    this.renderer.domElement.setAttribute("aria-label", "可漫游的 3D 海上航海主题展馆");
    this.container.appendChild(this.renderer.domElement);

    this.controls = new PointerLockControls(this.camera, this.renderer.domElement);
    this.camera.position.set(0, CAMERA_HEIGHT, this.hall.cameraZ);
    this.camera.lookAt(0, CAMERA_HEIGHT, this.hall.cameraTargetZ);
    this.scene.add(this.camera);
    this.scene.background = new THREE.Color(0x87cde5);
    this.scene.fog = new THREE.Fog(0xb8dce5, 80, 190);

    this.buildHall();
    this.buildExhibits(orderedCharacters);
    this.bindEvents();
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(this.container);
    this.resize();
    this.animate();
  }

  lock() {
    if (this.disposed) return;
    this.controls.lock();
    this.updatePosterTextures(true);
  }
  unlock() { if (this.controls.isLocked) this.controls.unlock(); }

  dispose() {
    if (this.disposed) return;
    this.disposed = true;
    cancelAnimationFrame(this.animationFrame);
    this.resizeObserver.disconnect();
    this.unlock();
    this.controls.disconnect();
    window.removeEventListener("keydown", this.handleKeyDown);
    window.removeEventListener("keyup", this.handleKeyUp);
    this.renderer.domElement.removeEventListener("click", this.handleClick);
    for (const geometry of this.geometries) geometry.dispose();
    for (const material of this.materials) material.dispose();
    for (const texture of this.textures) texture.dispose();
    this.posterTextures.clear();
    this.posterTextureLoads.clear();
    this.posterWindowUrls.clear();
    this.environmentTarget?.dispose();
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }

  private buildHall() {
    const { length } = this.hall;
    this.buildEnvironment();
    const oceanMaterial = this.textureMaterial(WATER_MAP_URL, { color: 0x4e9eb0, roughness: 0.2, metalness: 0.02, clearcoat: 0.85, bumpScale: 0.04, repeat: [32, 32] });
    const ocean = new THREE.Mesh(this.geometry(new THREE.PlaneGeometry(220, 220, 48, 48)), oceanMaterial);
    ocean.rotation.x = -Math.PI / 2;
    // 海面紧贴步道边缘铺开，移除旧的局部玻璃/水槽层后仍保持连续海面。
    ocean.position.y = -0.04;
    ocean.receiveShadow = true;
    this.scene.add(ocean);
    this.oceanColorMap = oceanMaterial.map;

    const stone = this.textureMaterial(STONE_MAP_URL, { color: 0xf0d8b2, roughness: 0.88, metalness: 0.03, repeat: [8, 24] });
    const walkway = new THREE.Mesh(this.geometry(new THREE.BoxGeometry(4.4, 0.28, length)), stone);
    walkway.position.y = 0.14;
    walkway.receiveShadow = true;
    this.scene.add(walkway);
    const grout = this.material(new THREE.MeshStandardMaterial({ color: 0x957c62, roughness: 0.86, metalness: 0.02 }));
    for (const x of [-2.02, 2.02]) {
      const joint = new THREE.Mesh(this.geometry(new THREE.BoxGeometry(0.025, 0.012, length - 0.5)), grout);
      joint.position.set(x, 0.286, 0);
      this.scene.add(joint);
    }
    for (let column = 1; column < WALKWAY_TILE_COLUMNS; column += 1) {
      const x = -2.01 + (4.02 / WALKWAY_TILE_COLUMNS) * column;
      const joint = new THREE.Mesh(this.geometry(new THREE.BoxGeometry(0.022, 0.012, length - 0.5)), grout);
      joint.position.set(x, 0.286, 0);
      this.scene.add(joint);
    }
    for (let z = -length / 2 + WALKWAY_TILE_LENGTH; z < length / 2; z += WALKWAY_TILE_LENGTH) {
      const joint = new THREE.Mesh(this.geometry(new THREE.BoxGeometry(4.02, 0.012, 0.026)), grout);
      joint.position.set(0, 0.286, z);
      this.scene.add(joint);
    }
    for (let z = -length / 2 + WALKWAY_TILE_LENGTH / 2; z < length / 2; z += WALKWAY_TILE_LENGTH) {
      const joint = new THREE.Mesh(this.geometry(new THREE.BoxGeometry(4.02, 0.012, 0.022)), grout);
      joint.position.set(0, 0.286, z);
      this.scene.add(joint);
    }

    this.addCompassInlay(length);

    this.scene.add(new THREE.HemisphereLight(0xd8f3fa, 0x2e6672, 1.65));
    this.scene.add(new THREE.AmbientLight(0xf4e2c4, 0.36));
    const sun = new THREE.DirectionalLight(0xffd69a, 3.2);
    sun.position.set(-28, 19, 25);
    sun.castShadow = true;
    sun.shadow.mapSize.set(1024, 1024);
    sun.shadow.camera.left = -28;
    sun.shadow.camera.right = 28;
    sun.shadow.camera.top = 28;
    sun.shadow.camera.bottom = -28;
    sun.shadow.camera.far = 95;
    this.scene.add(sun);
  }

  private addCompassInlay(length: number) {
    const texture = this.assetTexture(COMPASS_ROSE_URL, 1, 1, true);
    const material = this.material(new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      depthWrite: false,
      color: 0xffffff,
    }));
    const compass = new THREE.Mesh(this.geometry(new THREE.PlaneGeometry(3.3, 3.3)), material);
    compass.rotation.x = -Math.PI / 2;
    compass.position.set(0, 0.305, length / 2 - EXHIBIT_ENTRY_CLEARANCE - 2.2);
    this.scene.add(compass);

    const ringMaterial = this.material(new THREE.MeshStandardMaterial({
      color: 0xb88a4b,
      roughness: 0.36,
      metalness: 0.82,
    }));
    const ringGeometry = this.geometry(new THREE.TorusGeometry(0.36, 0.022, 8, 32));
    const centerMaterial = this.material(new THREE.MeshPhysicalMaterial({
      color: 0x2aaec0,
      roughness: 0.2,
      metalness: 0.22,
      clearcoat: 0.85,
      clearcoatRoughness: 0.08,
      envMapIntensity: 1.2,
    }));
    const centerGeometry = this.geometry(new THREE.CylinderGeometry(0.19, 0.19, 0.035, 24));
    const firstMarker = -length / 2 + NAV_MARKER_SPACING;
    for (let index = 0; index < 5; index += 1) {
      const z = firstMarker + index * NAV_MARKER_SPACING * 2;
      if (z >= length / 2 - 1) break;
      const ring = new THREE.Mesh(ringGeometry, ringMaterial);
      ring.rotation.x = Math.PI / 2;
      ring.position.set(0, 0.315, z);
      this.scene.add(ring);
      const center = new THREE.Mesh(centerGeometry, centerMaterial);
      center.position.set(0, 0.315, z);
      this.scene.add(center);
    }
  }

  private buildExhibits(characters: GalleryCharacter[]) {
    const stone = this.textureMaterial(STONE_MAP_URL, { color: 0xe8cda7, roughness: 0.84, metalness: 0.02, repeat: [2, 1] });
    const brass = this.textureMaterial(FRAME_BRASS_MAP_URL, { color: 0xffffff, roughness: 0.38, metalness: 0.82, repeat: [1, 1] });
    const frameAccent = this.material(new THREE.MeshStandardMaterial({ color: 0x103c52, roughness: 0.48, metalness: 0.24 }));
    const plaqueMaterial = this.material(new THREE.MeshStandardMaterial({ color: 0xb98b4f, roughness: 0.34, metalness: 0.82 }));
    const plinthShadow = this.material(new THREE.MeshStandardMaterial({ color: 0x103b4d, roughness: 0.6, metalness: 0.28 }));
    const plinthEdge = this.material(new THREE.MeshPhysicalMaterial({
      color: 0x38c6d1,
      emissive: 0x0b6874,
      emissiveIntensity: 0.28,
      roughness: 0.24,
      metalness: 0.34,
      clearcoat: 0.72,
      clearcoatRoughness: 0.08,
    }));
    const positions = createExhibitPositions(characters.length, this.hall.exhibitStartZ);
    characters.forEach((character, index) => {
      const { x, z, side } = positions[index];
      const footing = new THREE.Mesh(this.geometry(new THREE.BoxGeometry(3.16, 0.11, 2.56)), plinthShadow);
      footing.position.set(x, 0.12, z);
      footing.receiveShadow = true;
      this.scene.add(footing);
      for (const [lightWidth, lightDepth, offsetX, offsetZ] of [
        [3.18, 0.055, 0, -1.29],
        [3.18, 0.055, 0, 1.29],
        [0.055, 2.48, -1.59, 0],
        [0.055, 2.48, 1.59, 0],
      ]) {
        const edge = new THREE.Mesh(this.geometry(new THREE.BoxGeometry(lightWidth, 0.035, lightDepth)), plinthEdge);
        edge.position.set(x + offsetX, 0.215, z + offsetZ);
        this.scene.add(edge);
      }
      const plinth = new THREE.Mesh(this.geometry(new THREE.BoxGeometry(3.35, 0.72, 2.75)), stone);
      plinth.position.set(x, 0.7, z);
      plinth.castShadow = true;
      plinth.receiveShadow = true;
      this.scene.add(plinth);
      const frame = this.createPortraitFrame(character, index, stone, brass, frameAccent, plaqueMaterial);
      frame.position.set(x, 2.24, z);
      frame.rotation.y = side < 0 ? Math.PI / 2 : -Math.PI / 2;
      frame.userData.character = character;
      frame.userData.slot = index + 1;
      this.scene.add(frame);
      this.interactables.push(frame as ExhibitTarget);
    });
  }

  private createPortraitFrame(
    character: GalleryCharacter,
    index: number,
    stone: THREE.Material,
    brass: THREE.Material,
    frameAccent: THREE.Material,
    plaqueMaterial: THREE.Material,
  ) {
    const group = new THREE.Group();
    group.scale.setScalar(0.9);
    const width = 1.55;
    const height = 2.32;
    const trim = 0.14;
    const depth = 0.16;
    const add = <T extends THREE.Object3D>(object: T) => { group.add(object); return object; };
    const backing = add(new THREE.Mesh(
      this.portraitFrameBackingGeometry ??= this.geometry(createPortraitFrameBackingGeometry(width + trim * 2 - 0.05, height + trim * 2 - 0.05)),
      stone,
    ));
    backing.position.z = -0.13;
    backing.castShadow = true;
    backing.receiveShadow = true;

    const shell = add(new THREE.Mesh(
      this.portraitFrameShellGeometry ??= this.geometry(createPortraitFrameShellGeometry(width + trim * 2, height + trim * 2, depth)),
      brass,
    ));
    shell.position.z = -depth / 2;
    shell.castShadow = true;
    shell.receiveShadow = true;

    const mat = add(new THREE.Mesh(
      this.portraitFrameMatGeometry ??= this.geometry(new THREE.PlaneGeometry(width + 0.08, height + 0.08)),
      frameAccent,
    ));
    mat.position.z = 0.01;

    const posterMaterial = this.material(new THREE.MeshStandardMaterial({
      color: 0xe3c79a,
      roughness: 0.68,
      metalness: 0.02,
      side: THREE.FrontSide,
    }));
    const portrait = add(new THREE.Mesh(
      this.portraitGeometry ??= this.geometry(new THREE.PlaneGeometry(width, height)),
      posterMaterial,
    ));
    portrait.position.z = depth / 2 + 0.012;

    const rivetMaterial = frameAccent;
    const rivetGeometry = this.portraitFrameRivetGeometry ??= this.geometry(new THREE.SphereGeometry(0.043, 12, 8));
    const rivetInsetGeometry = this.portraitFrameRivetInsetGeometry ??= this.geometry(new THREE.SphereGeometry(0.022, 10, 8));
    const rivetPositions = [
      [-(width + trim) / 2 + 0.13, (height + trim) / 2 - 0.13],
      [(width + trim) / 2 - 0.13, (height + trim) / 2 - 0.13],
      [-(width + trim) / 2 + 0.13, -(height + trim) / 2 + 0.13],
      [(width + trim) / 2 - 0.13, -(height + trim) / 2 + 0.13],
    ] as const;
    const highlightMeshes: THREE.Object3D[] = [shell];
    for (const [x, y] of rivetPositions) {
      const rivet = add(new THREE.Mesh(rivetGeometry, brass));
      rivet.position.set(x, y, depth / 2 + 0.035);
      rivet.castShadow = true;
      highlightMeshes.push(rivet);
      const inset = add(new THREE.Mesh(rivetInsetGeometry, rivetMaterial));
      inset.position.set(x, y, depth / 2 + 0.07);
    }

    const plaque = add(new THREE.Mesh(
      this.portraitFramePlaqueGeometry ??= this.geometry(new THREE.BoxGeometry(width * 0.82, 0.16, 0.08)),
      plaqueMaterial,
    ));
    plaque.position.set(0, -(height + trim) / 2 - 0.15, depth / 2);
    plaque.castShadow = true;
    highlightMeshes.push(plaque);

    const plaqueInset = add(new THREE.Mesh(
      this.portraitFramePlaqueInsetGeometry ??= this.geometry(new THREE.BoxGeometry(width * 0.68, 0.055, 0.012)),
      frameAccent,
    ));
    plaqueInset.position.set(0, plaque.position.y, depth / 2 + 0.045);

    const labelTexture = createFrameLabelTexture(character.name, index + 1);
    this.textures.add(labelTexture);
    const label = add(new THREE.Mesh(
      this.geometry(new THREE.PlaneGeometry(width * 0.66, 0.09)),
      this.material(new THREE.MeshBasicMaterial({ map: labelTexture, transparent: true, depthWrite: false })),
    ));
    label.position.set(0, plaque.position.y, depth / 2 + 0.052);

    this.posterFrames.push({
      material: posterMaterial,
      row: Math.floor(index / 2),
      url: character.poster_frame_url || character.poster_url,
      usesLegacySource: !character.poster_frame_url,
    });
    group.userData.highlightMeshes = highlightMeshes;
    return group;
  }

  private updatePosterTextures(force = false) {
    if (this.disposed || !this.controls.isLocked || !this.posterFrames.length) return;
    const rowCount = Math.ceil(this.posterFrames.length / 2);
    const currentRow = this.closestPosterRow();
    const forward = new THREE.Vector3();
    this.camera.getWorldDirection(forward);
    const walkingTowardExit = forward.z <= 0;
    const windowRows = Math.min(rowCount, MAX_POSTER_TEXTURES / 2);
    const idealStart = walkingTowardExit ? currentRow - 2 : currentRow - (windowRows - 3);
    const firstRow = Math.max(0, Math.min(idealStart, rowCount - windowRows));
    const lastRow = firstRow + windowRows - 1;
    const targetFrames = this.posterFrames.filter((frame) => frame.row >= firstRow && frame.row <= lastRow && frame.url);
    const targetUrls = new Set(targetFrames.map((frame) => this.localPosterUrl(frame.url as string)));
    const windowKey = `${firstRow}:${lastRow}:${[...targetUrls].sort().join("|")}`;
    if (!force && windowKey === this.posterWindowKey) return;
    this.posterWindowKey = windowKey;
    this.posterWindowUrls = targetUrls;

    for (const frame of this.posterFrames) {
      const url = frame.url ? this.localPosterUrl(frame.url) : null;
      if (!url || !targetUrls.has(url)) this.clearPosterMaterial(frame.material);
    }
    for (const [url, texture] of this.posterTextures) {
      if (targetUrls.has(url)) continue;
      texture.dispose();
      this.textures.delete(texture);
      this.posterTextures.delete(url);
    }
    for (const frame of targetFrames) this.loadPosterFrame(frame);
  }

  private closestPosterRow() {
    let closestRow = 0;
    let closestDistance = Number.POSITIVE_INFINITY;
    for (const frame of this.posterFrames) {
      const exhibitZ = this.hall.exhibitStartZ - frame.row * EXHIBIT_ROW_SPACING;
      const distance = Math.abs(exhibitZ - this.camera.position.z);
      if (distance < closestDistance) {
        closestDistance = distance;
        closestRow = frame.row;
      }
    }
    return closestRow;
  }

  private loadPosterFrame(frame: PosterFrame) {
    if (!frame.url) return;
    const url = this.localPosterUrl(frame.url);
    const cached = this.posterTextures.get(url);
    if (cached) {
      this.applyPosterTexture(url, cached);
      return;
    }
    if (this.posterTextureLoads.has(url)) return;
    const load = this.posterTexture(url, frame.usesLegacySource).then((texture) => {
      this.posterTextureLoads.delete(url);
      if (!texture) return null;
      if (this.disposed || !this.posterWindowUrls.has(url)) {
        texture.dispose();
        return null;
      }
      this.posterTextures.set(url, texture);
      this.textures.add(texture);
      this.applyPosterTexture(url, texture);
      return texture;
    });
    this.posterTextureLoads.set(url, load);
  }

  private applyPosterTexture(url: string, texture: THREE.Texture) {
    for (const frame of this.posterFrames) {
      if (!frame.url || this.localPosterUrl(frame.url) !== url || !this.posterWindowUrls.has(url)) continue;
      frame.material.map = texture;
      frame.material.color.set(0xffffff);
      frame.material.needsUpdate = true;
    }
  }

  private clearPosterMaterial(material: THREE.MeshStandardMaterial) {
    if (!material.map) return;
    material.map = null;
    material.color.set(0xe3c79a);
    material.needsUpdate = true;
  }

  private localPosterUrl(url: string) {
    try {
      const source = new URL(url, window.location.href);
      return source.pathname.startsWith("/uploads/") ? `${source.pathname}${source.search}${source.hash}` : url;
    } catch {
      return url;
    }
  }

  private posterTexture(url: string, usesLegacySource: boolean) {
    return new Promise<THREE.Texture | null>((resolve) => {
      const loader = new THREE.ImageLoader();
      loader.setCrossOrigin("anonymous");
      loader.load(url, (image) => {
        const sourceWidth = image.naturalWidth || image.width;
        const sourceHeight = image.naturalHeight || image.height;
        if (sourceWidth <= 0 || sourceHeight <= 0) {
          resolve(null);
          return;
        }
        let texture: THREE.Texture;
        if (usesLegacySource && (sourceWidth > POSTER_TEXTURE_WIDTH || sourceHeight > POSTER_TEXTURE_HEIGHT)) {
          const canvas = document.createElement("canvas");
          const context = canvas.getContext("2d");
          if (!context) {
            resolve(null);
            return;
          }
          canvas.width = POSTER_TEXTURE_WIDTH;
          canvas.height = POSTER_TEXTURE_HEIGHT;
          const scale = Math.max(canvas.width / sourceWidth, canvas.height / sourceHeight);
          const drawWidth = sourceWidth * scale;
          const drawHeight = sourceHeight * scale;
          context.drawImage(image, (canvas.width - drawWidth) / 2, (canvas.height - drawHeight) / 2, drawWidth, drawHeight);
          texture = new THREE.CanvasTexture(canvas);
        } else {
          texture = new THREE.Texture(image);
          texture.needsUpdate = true;
        }
        texture.colorSpace = THREE.SRGBColorSpace;
        texture.wrapS = THREE.ClampToEdgeWrapping;
        texture.wrapT = THREE.ClampToEdgeWrapping;
        texture.minFilter = THREE.LinearFilter;
        texture.magFilter = THREE.LinearFilter;
        texture.generateMipmaps = false;
        texture.anisotropy = Math.min(4, this.renderer.capabilities.getMaxAnisotropy());
        resolve(texture);
      }, undefined, () => resolve(null));
    });
  }

  private buildEnvironment() {
    new THREE.TextureLoader().load(PANORAMA_URL, (texture) => {
      if (this.disposed) { texture.dispose(); return; }
      texture.mapping = THREE.EquirectangularReflectionMapping;
      texture.colorSpace = THREE.SRGBColorSpace;
      this.scene.background = texture;
      this.scene.environment = texture;
      this.scene.backgroundRotation.y = Math.PI;
      this.scene.environmentRotation.y = Math.PI;
      this.textures.add(texture);
    }, undefined, () => undefined);
  }

  private bindEvents() {
    this.controls.addEventListener("lock", () => this.callbacks.onLockChange(true));
    this.controls.addEventListener("unlock", () => {
      this.keys.clear();
      this.velocity.set(0, 0, 0);
      this.callbacks.onLockChange(false);
    });
    window.addEventListener("keydown", this.handleKeyDown);
    window.addEventListener("keyup", this.handleKeyUp);
    this.renderer.domElement.addEventListener("click", this.handleClick);
  }

  private readonly handleKeyDown = (event: KeyboardEvent) => {
    if (!this.controls.isLocked) return;
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "KeyW", "KeyA", "KeyS", "KeyD", "KeyE"].includes(event.code)) event.preventDefault();
    this.keys.add(event.code);
    if (event.code === "KeyE") this.openActiveExhibit();
  };
  private readonly handleKeyUp = (event: KeyboardEvent) => this.keys.delete(event.code);
  private readonly handleClick = () => { if (this.controls.isLocked) this.openActiveExhibit(); };

  private openActiveExhibit() {
    const character = this.activeExhibit?.userData.character;
    if (character) this.callbacks.onOpenCharacter(character, this.activeExhibit?.userData.slot ?? null);
  }

  private animate = (now = performance.now()) => {
    if (this.disposed) return;
    this.animationFrame = requestAnimationFrame(this.animate);
    const delta = Math.min((now - this.lastFrameAt) / 1000, 0.05);
    this.lastFrameAt = now;
    if (this.oceanColorMap && !this.reducedMotion) {
      this.oceanColorMap.offset.x = (this.oceanColorMap.offset.x + delta * 0.012) % 1;
      this.oceanColorMap.offset.y = (this.oceanColorMap.offset.y + delta * 0.006) % 1;
    }
    this.updateMovement(delta);
    this.updatePosterTextures();
    this.updateInteraction();
    this.renderer.render(this.scene, this.camera);
  };

  private updateMovement(delta: number) {
    if (!this.controls.isLocked) return;
    const forwardInput = Number(this.keys.has("KeyW") || this.keys.has("ArrowUp")) - Number(this.keys.has("KeyS") || this.keys.has("ArrowDown"));
    const sideInput = Number(this.keys.has("KeyD") || this.keys.has("ArrowRight")) - Number(this.keys.has("KeyA") || this.keys.has("ArrowLeft"));
    const forward = new THREE.Vector3();
    this.camera.getWorldDirection(forward);
    forward.y = 0;
    forward.normalize();
    const right = new THREE.Vector3().crossVectors(forward, this.camera.up).normalize();
    const target = forward.multiplyScalar(forwardInput).add(right.multiplyScalar(sideInput));
    if (target.lengthSq() > 1) target.normalize();
    target.multiplyScalar(WALK_SPEED);
    this.velocity.lerp(target, 1 - Math.exp(-10 * delta));
    const nextX = this.camera.position.x + this.velocity.x * delta;
    if (isWalkable(nextX, this.camera.position.z, this.hall.length)) this.camera.position.x = nextX; else this.velocity.x = 0;
    const nextZ = this.camera.position.z + this.velocity.z * delta;
    if (isWalkable(this.camera.position.x, nextZ, this.hall.length)) this.camera.position.z = nextZ; else this.velocity.z = 0;
    this.camera.position.y = CAMERA_HEIGHT;
  }

  private updateInteraction() {
    if (!this.controls.isLocked) { this.setActiveExhibit(null); return; }
    this.raycaster.setFromCamera(new THREE.Vector2(0, 0), this.camera);
    const hit = this.raycaster.intersectObjects(this.interactables, true).find((item) => item.distance <= MAX_INTERACTION_DISTANCE);
    let target = hit?.object as ExhibitTarget | undefined;
    while (target && !target.userData.character) target = target.parent as ExhibitTarget | undefined;
    this.setActiveExhibit(target ?? null);
  }

  private setActiveExhibit(target: ExhibitTarget | null) {
    if (target === this.activeExhibit) return;
    if (this.activeExhibit) setHighlight(this.activeExhibit, false);
    this.activeExhibit = target;
    if (target) {
      setHighlight(target, true);
      this.callbacks.onActiveCharacter(target.userData.character ?? null, target.userData.slot ?? null);
    } else this.callbacks.onActiveCharacter(null, null);
  }

  private resize() {
    const width = Math.max(1, this.container.clientWidth);
    const height = Math.max(1, this.container.clientHeight);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
  }

  private geometry<T extends THREE.BufferGeometry>(geometry: T): T {
    this.geometries.add(geometry);
    return geometry;
  }

  private material<T extends THREE.Material>(material: T): T {
    this.materials.add(material);
    return material;
  }

  private textureMaterial(url: string, options: { color: number; roughness: number; metalness: number; repeat: [number, number]; transparent?: boolean; opacity?: number; clearcoat?: number; bumpScale?: number }) {
    const map = this.assetTexture(url, options.repeat[0], options.repeat[1], true);
    return this.material(new THREE.MeshPhysicalMaterial({
      map,
      color: options.color,
      roughness: options.roughness,
      metalness: options.metalness,
      ...(options.transparent === undefined ? {} : { transparent: options.transparent }),
      ...(options.opacity === undefined ? {} : { opacity: options.opacity }),
      clearcoat: options.clearcoat ?? 0,
      bumpMap: map,
      bumpScale: options.bumpScale ?? 0.01,
    }));
  }

  private assetTexture(url: string, repeatX: number, repeatY: number, colorTexture = false) {
    const texture = new THREE.TextureLoader().load(url);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.RepeatWrapping;
    texture.repeat.set(repeatX, repeatY);
    texture.anisotropy = Math.min(8, this.renderer.capabilities.getMaxAnisotropy());
    if (colorTexture) texture.colorSpace = THREE.SRGBColorSpace;
    this.textures.add(texture);
    return texture;
  }

}

function createHallLayout(characterCount: number): HallLayout {
  const rows = Math.ceil(characterCount / 2);
  const length = Math.max(
    MIN_HALL_LENGTH,
    EXHIBIT_ENTRY_CLEARANCE + EXHIBIT_EXIT_CLEARANCE + Math.max(0, rows - 1) * EXHIBIT_ROW_SPACING,
  );
  const exhibitStartZ = length / 2 - EXHIBIT_ENTRY_CLEARANCE;
  return {
    length,
    exhibitStartZ,
    cameraZ: length / 2 - 3.5,
    cameraTargetZ: exhibitStartZ - 5.5,
  };
}

function createPortraitFrameShellGeometry(width: number, height: number, depth: number) {
  const radius = Math.min(0.2, Math.min(width, height) * 0.18);
  const shell = roundedRectShape(width, height, radius);
  shell.holes.push(roundedRectHole(width - 0.22, height - 0.22, Math.max(0.06, radius - 0.045)));
  return new THREE.ExtrudeGeometry(shell, {
    depth,
    bevelEnabled: true,
    bevelThickness: 0.025,
    bevelSize: 0.026,
    bevelSegments: 2,
    curveSegments: 4,
  });
}

function createPortraitFrameBackingGeometry(width: number, height: number) {
  const radius = Math.min(0.15, Math.min(width, height) * 0.15);
  return new THREE.ExtrudeGeometry(roundedRectShape(width, height, radius), {
    depth: 0.09,
    bevelEnabled: false,
    curveSegments: 4,
  });
}

function roundedRectShape(width: number, height: number, radius: number) {
  return roundedRectPath(new THREE.Shape(), width, height, radius);
}

function roundedRectHole(width: number, height: number, radius: number) {
  return roundedRectPath(new THREE.Path(), width, height, radius);
}

function roundedRectPath<T extends THREE.Path>(path: T, width: number, height: number, radius: number) {
  const left = -width / 2;
  const right = width / 2;
  const top = height / 2;
  const bottom = -height / 2;
  path.moveTo(left + radius, bottom);
  path.lineTo(right - radius, bottom);
  path.quadraticCurveTo(right, bottom, right, bottom + radius);
  path.lineTo(right, top - radius);
  path.quadraticCurveTo(right, top, right - radius, top);
  path.lineTo(left + radius, top);
  path.quadraticCurveTo(left, top, left, top - radius);
  path.lineTo(left, bottom + radius);
  path.quadraticCurveTo(left, bottom, left + radius, bottom);
  return path;
}

function createFrameLabelTexture(name: string, slot: number) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 72;
  const context = canvas.getContext("2d")!;
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.textBaseline = "middle";
  context.textAlign = "center";
  context.fillStyle = "#f4d897";
  context.font = '700 18px "IBM Plex Mono", monospace';
  context.fillText(`${String(slot).padStart(2, "0")}  ·  ${name}`, canvas.width / 2, canvas.height / 2);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function createExhibitPositions(count: number, startZ: number) {
  const positions: Array<{ x: number; z: number; side: number }> = [];
  const perSide = Math.ceil(count / 2);
  for (let index = 0; index < perSide; index += 1) {
    const z = startZ - index * EXHIBIT_ROW_SPACING;
    positions.push({ x: -5.5, z, side: -1 });
    if (positions.length < count) positions.push({ x: 5.5, z, side: 1 });
  }
  return positions;
}

function setHighlight(target: THREE.Object3D, active: boolean) {
  const meshes = (target.userData.highlightMeshes as THREE.Object3D[] | undefined) ?? [];
  meshes.forEach((mesh) => {
    mesh.scale.setScalar(active ? 1.06 : 1);
  });
}

function isWalkable(x: number, z: number, hallLength: number) {
  const radius = 0.35;
  const walkwayHalfWidth = 2.2;
  const walkwayHalfLength = hallLength / 2 - 1.2;
  return Math.abs(x) <= walkwayHalfWidth - radius && Math.abs(z) <= walkwayHalfLength - radius;
}
