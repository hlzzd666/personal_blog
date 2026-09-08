<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import OceanIcon from "./OceanIcon.vue";

const root = ref<HTMLElement | null>(null);
const canvas = ref<HTMLCanvasElement | null>(null);
const loading = ref(true);
const failed = ref(false);
const dragging = ref(false);
const rotating = ref(!window.matchMedia("(prefers-reduced-motion: reduce)").matches);
let renderer: THREE.WebGLRenderer | null = null;
let scene: THREE.Scene | null = null;
let camera: THREE.PerspectiveCamera | null = null;
let controls: OrbitControls | null = null;
let resizeObserver: ResizeObserver | null = null;
let visibilityObserver: IntersectionObserver | null = null;
let animationFrame = 0;
let visible = false;
let started = false;
let session = 0;
let modelRadius = 2;
let lastFrameAt = 0;

function disposeModel(model: THREE.Object3D) {
  const resources = new Set<THREE.BufferGeometry | THREE.Material | THREE.Texture>();
  model.traverse((object) => {
    if (!(object instanceof THREE.Mesh)) return;
    resources.add(object.geometry);
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    materials.forEach((material) => {
      resources.add(material);
      Object.values(material).forEach((value) => {
        if (value instanceof THREE.Texture) resources.add(value);
      });
    });
  });
  resources.forEach((resource) => resource.dispose());
}

function dispose() {
  session += 1;
  window.cancelAnimationFrame(animationFrame);
  resizeObserver?.disconnect();
  controls?.dispose();
  if (scene) disposeModel(scene);
  renderer?.dispose();
  renderer = null;
  scene = null;
  camera = null;
  controls = null;
}

function fitCamera() {
  if (!camera || !controls) return;
  const verticalFov = THREE.MathUtils.degToRad(camera.fov) / 2;
  const horizontalFov = Math.atan(Math.tan(verticalFov) * camera.aspect);
  const distance = modelRadius / Math.sin(Math.min(verticalFov, horizontalFov)) * 1.12;
  camera.position.sub(controls.target).normalize().multiplyScalar(distance).add(controls.target);
  controls.minDistance = distance * 0.7;
  controls.maxDistance = distance * 2;
  controls.update();
}

function resize() {
  if (!root.value || !renderer || !camera) return;
  const width = Math.max(1, root.value.clientWidth);
  const height = Math.max(1, root.value.clientHeight);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, width < 640 ? 1.25 : 1.75));
  renderer.setSize(width, height, false);
  fitCamera();
}

function render(now: number) {
  if (!renderer || !scene || !camera || !controls || !visible || document.hidden) return;
  controls.autoRotate = rotating.value;
  controls.update(Math.min((now - lastFrameAt) / 1000, 0.05));
  lastFrameAt = now;
  renderer.render(scene, camera);
  animationFrame = window.requestAnimationFrame(render);
}

function updateRendering() {
  window.cancelAnimationFrame(animationFrame);
  if (visible && !document.hidden && !loading.value && !failed.value) {
    lastFrameAt = performance.now();
    animationFrame = window.requestAnimationFrame(render);
  }
}

function pauseRotation() {
  rotating.value = false;
  dragging.value = true;
}

function rotateWithKeyboard(event: KeyboardEvent) {
  if (!camera || !controls || !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) return;
  event.preventDefault();
  rotating.value = false;
  const spherical = new THREE.Spherical().setFromVector3(camera.position.clone().sub(controls.target));
  if (event.key === "ArrowLeft") spherical.theta -= 0.12;
  if (event.key === "ArrowRight") spherical.theta += 0.12;
  if (event.key === "ArrowUp") spherical.phi -= 0.12;
  if (event.key === "ArrowDown") spherical.phi += 0.12;
  spherical.phi = THREE.MathUtils.clamp(spherical.phi, controls.minPolarAngle, controls.maxPolarAngle);
  camera.position.setFromSpherical(spherical).add(controls.target);
  controls.update();
}

async function loadModel() {
  if (!root.value || !canvas.value) return;
  dispose();
  const currentSession = session;
  loading.value = true;
  failed.value = false;
  try {
    // 画布由 Vue 创建，使 scoped 层级样式和 OrbitControls 命中同一个元素。
    renderer = new THREE.WebGLRenderer({ canvas: canvas.value, alpha: true, antialias: true });
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.08;
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(28, 1, 0.01, 100);
    camera.position.set(-0.9, 0.42, 1);
    controls = new OrbitControls(camera, canvas.value);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = false;
    controls.autoRotateSpeed = 0.72;
    controls.minPolarAngle = 0.25;
    controls.maxPolarAngle = Math.PI * 0.8;
    controls.addEventListener("start", pauseRotation);
    controls.addEventListener("end", () => { dragging.value = false; });
    scene.add(new THREE.HemisphereLight(0xfff0d0, 0x082333, 2.2));
    const keyLight = new THREE.DirectionalLight(0xffdf9b, 3.8);
    keyLight.position.set(4, 6, 5);
    scene.add(keyLight);
    const rimLight = new THREE.DirectionalLight(0x6ed8d1, 2.5);
    rimLight.position.set(-4, 2, -5);
    scene.add(rimLight);
    resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(root.value);
    resize();

    const gltf = await new GLTFLoader().loadAsync(import.meta.env.BASE_URL + "models/one_piece_-going_merry.glb");
    if (currentSession !== session) {
      disposeModel(gltf.scene);
      return;
    }
    const model = gltf.scene;
    const bounds = new THREE.Box3().setFromObject(model);
    const size = bounds.getSize(new THREE.Vector3());
    const scale = 3.25 / Math.max(size.x, size.y, size.z, 0.01);
    model.scale.setScalar(scale);
    model.position.sub(bounds.getCenter(new THREE.Vector3()).multiplyScalar(scale));
    modelRadius = new THREE.Box3().setFromObject(model).getBoundingSphere(new THREE.Sphere()).radius;
    scene.add(model);
    fitCamera();
    loading.value = false;
    updateRendering();
  } catch (error) {
    if (currentSession !== session) return;
    console.error("梅利号模型加载失败", error);
    failed.value = true;
    loading.value = false;
    dispose();
  }
}

onMounted(() => {
  if (!root.value) return;
  visibilityObserver = new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    if (visible && !started) {
      started = true;
      void loadModel();
    }
    updateRendering();
  }, { rootMargin: "120px 0px" });
  visibilityObserver.observe(root.value);
  document.addEventListener("visibilitychange", updateRendering);
});

onBeforeUnmount(() => {
  visibilityObserver?.disconnect();
  document.removeEventListener("visibilitychange", updateRendering);
  dispose();
});
</script>

<template>
  <div class="going-merry-viewer">
    <div ref="root" class="going-merry-stage" :aria-busy="loading">
      <canvas
        ref="canvas"
        class="going-merry-canvas"
        :class="{ dragging }"
        :tabindex="loading || failed ? -1 : 0"
        aria-label="梅利号三维模型，可拖动或使用方向键旋转"
        @keydown="rotateWithKeyboard"
      ></canvas>
      <p v-if="loading" class="going-merry-status" role="status">梅利号加载中…</p>
      <div v-else-if="failed" class="going-merry-error" role="status">
        <p>模型加载失败</p>
        <button type="button" @click="loadModel"><OceanIcon name="previous" :size="20" />重新加载</button>
      </div>
    </div>
    <div class="going-merry-toolbar">
      <small>Going Merry · <a href="https://sketchfab.com/3d-models/one-piece-going-merry-0e1f16189e8b4b4d9d9c3c60893d692b" target="_blank" rel="noreferrer">Anex</a> · <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noreferrer">CC BY 4.0</a></small>
      <label><input v-model="rotating" type="checkbox" :disabled="loading || failed" />自动旋转</label>
    </div>
  </div>
</template>

<style scoped>
.going-merry-viewer {
  width: 100%;
  min-width: 0;
  color: #f6ebd4;
  font-family: "Noto Sans SC", sans-serif;
  letter-spacing: 0;
}
.going-merry-stage {
  position: relative;
  width: 100%;
  height: 32rem;
  isolation: isolate;
}
.going-merry-canvas {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: block;
  width: 100%;
  height: 100%;
  cursor: grab;
  touch-action: none;
  user-select: none;
}
.going-merry-canvas.dragging { cursor: grabbing; }
.going-merry-status,
.going-merry-error {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 0;
}
.going-merry-status { pointer-events: none; }
.going-merry-error button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  min-height: 44px;
  padding: 0.5rem 1rem;
  border: 1px solid #87d2c7;
  border-radius: 4px;
  color: #f6ebd4;
  background: #071c29;
  font: inherit;
  cursor: pointer;
}
.going-merry-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem 1.25rem;
  min-height: 44px;
  font-size: 0.82rem;
}
.going-merry-toolbar small {
  color: #b8c9c7;
  font-size: 0.72rem;
  line-height: 1.6;
}
.going-merry-toolbar a { color: inherit; text-underline-offset: 3px; }
.going-merry-toolbar a:hover { color: #f0c162; }
.going-merry-toolbar label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-height: 44px;
  cursor: pointer;
}
.going-merry-toolbar input { accent-color: #f0c162; }
.going-merry-toolbar label:has(input:disabled) { opacity: 0.5; cursor: default; }
.going-merry-viewer :focus-visible { outline: 2px solid #ffd36f; outline-offset: 3px; }
@media (max-width: 640px) {
  .going-merry-stage { height: 25rem; }
}
</style>
