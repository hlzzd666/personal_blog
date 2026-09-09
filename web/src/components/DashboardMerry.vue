<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from "vue";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { RotateCcw, Minus, Plus, LoaderCircle, RefreshCw } from "lucide-vue-next";

const root = ref<HTMLElement>();
const canvas = ref<HTMLCanvasElement>();
const loading = ref(true);
const failed = ref(false);
const rotating = ref(!window.matchMedia("(prefers-reduced-motion: reduce)").matches);
const base = import.meta.env.BASE_URL;
let renderer: THREE.WebGLRenderer | undefined;
let scene: THREE.Scene | undefined;
let camera: THREE.PerspectiveCamera | undefined;
let controls: OrbitControls | undefined;
let resizeObserver: ResizeObserver | undefined;
let visibilityObserver: IntersectionObserver | undefined;
let visible = true;
let animationFrame = 0;
let session = 0;
let radius = 2;
let initialDistance = 8;
let lastTime = 0;
const motion = window.matchMedia("(prefers-reduced-motion: reduce)");

function release() {
  session++;
  cancelAnimationFrame(animationFrame);
  resizeObserver?.disconnect();
  controls?.dispose();
  const resources = new Set<THREE.BufferGeometry | THREE.Material | THREE.Texture>();
  scene?.traverse((object) => {
    if (object instanceof THREE.DirectionalLight) object.shadow.dispose();
    if (!(object instanceof THREE.Mesh)) return;
    resources.add(object.geometry);
    for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
      resources.add(material);
      Object.values(material).forEach((value) => { if (value instanceof THREE.Texture) resources.add(value); });
    }
  });
  resources.forEach((resource) => resource.dispose());
  renderer?.dispose();
  renderer = undefined; scene = undefined; camera = undefined; controls = undefined;
}

function reset() {
  if (!camera || !controls) return;
  camera.position.set(-0.82, 0.5, 1).normalize().multiplyScalar(initialDistance);
  controls.target.set(0, 0, 0);
  controls.update();
  if (renderer && scene) renderer.render(scene, camera);
}

function resize() {
  if (!root.value || !renderer || !camera || !controls) return;
  const { clientWidth: width, clientHeight: height } = root.value;
  if (!width || !height) return;
  camera.aspect = width / height;
  camera.setViewOffset(width, height, 0, height * 0.035, width, height);
  camera.updateProjectionMatrix();
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
  renderer.setSize(width, height, false);
  initialDistance = radius / Math.sin(THREE.MathUtils.degToRad(14)) * (width < height ? 0.95 : 0.65);
  controls.minDistance = initialDistance * 0.65;
  controls.maxDistance = initialDistance * 1.7;
  reset();
  resume();
}

function render(now: number) {
  if (!renderer || !scene || !camera || !controls || document.hidden || !visible) return;
  animationFrame = requestAnimationFrame(render);
  if (now - lastTime < 1000 / 30) return;
  controls.autoRotate = rotating.value && !motion.matches;
  controls.update(Math.min((now - lastTime) / 1000, 0.1));
  lastTime = now;
  renderer.render(scene, camera);
}
function resume() {
  cancelAnimationFrame(animationFrame);
  if (!loading.value && !failed.value && !document.hidden && visible) { lastTime = performance.now(); animationFrame = requestAnimationFrame(render); }
}
function pauseMotion() { if (motion.matches) rotating.value = false; }
function zoom(factor: number) {
  if (!camera || !controls) return;
  const offset = camera.position.clone().sub(controls.target);
  camera.position.copy(controls.target).add(offset.setLength(THREE.MathUtils.clamp(offset.length() * factor, controls.minDistance, controls.maxDistance)));
  controls.update();
  if (renderer && scene) renderer.render(scene, camera);
}
function onKey(event: KeyboardEvent) {
  if (!camera || !controls || !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "+", "-"].includes(event.key)) return;
  event.preventDefault();
  if (event.key === "+" || event.key === "-") return zoom(event.key === "+" ? 0.9 : 1.1);
  const position = new THREE.Spherical().setFromVector3(camera.position.clone().sub(controls.target));
  if (event.key === "ArrowLeft") position.theta -= 0.13;
  if (event.key === "ArrowRight") position.theta += 0.13;
  if (event.key === "ArrowUp") position.phi -= 0.1;
  if (event.key === "ArrowDown") position.phi += 0.1;
  position.phi = THREE.MathUtils.clamp(position.phi, 0.25, Math.PI * 0.72);
  camera.position.setFromSpherical(position).add(controls.target); controls.update();
}
async function load() {
  release(); const current = session;
  loading.value = true; failed.value = false;
  try {
    if (!canvas.value || !root.value) return;
    renderer = new THREE.WebGLRenderer({ canvas: canvas.value, alpha: true, antialias: true });
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.15;
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(28, 1, 0.01, 100);
    controls = new OrbitControls(camera, canvas.value);
    controls.enableDamping = true; controls.enablePan = false; controls.autoRotateSpeed = 0.55;
    controls.minPolarAngle = 0.25; controls.maxPolarAngle = Math.PI * 0.72;
    scene.add(new THREE.HemisphereLight(0xffffff, 0x739c9b, 2.5));
    const key = new THREE.DirectionalLight(0xffefda, 3.5); key.position.set(-4, 8, 7);
    key.castShadow = true; key.shadow.mapSize.set(1024, 1024);
    key.shadow.camera.left = -4; key.shadow.camera.right = 4;
    key.shadow.camera.top = 4; key.shadow.camera.bottom = -4;
    key.shadow.camera.near = 0.1; key.shadow.camera.far = 24;
    key.shadow.normalBias = 0.02; key.shadow.radius = 4; scene.add(key);
    const fill = new THREE.DirectionalLight(0xb7eeed, 2); fill.position.set(5, 3, -4); scene.add(fill);
    const gltf = await new GLTFLoader().loadAsync(`${base}models/one_piece_-going_merry.glb`);
    if (current !== session || !scene) {
      gltf.scene.traverse((object) => { if (object instanceof THREE.Mesh) { object.geometry.dispose(); for (const material of Array.isArray(object.material) ? object.material : [object.material]) { Object.values(material).forEach((value) => { if (value instanceof THREE.Texture) value.dispose(); }); material.dispose(); } } });
      return;
    }
    const bounds = new THREE.Box3().setFromObject(gltf.scene);
    const size = bounds.getSize(new THREE.Vector3());
    const scale = 3.25 / Math.max(size.x, size.y, size.z);
    gltf.scene.scale.setScalar(scale);
    gltf.scene.position.sub(bounds.getCenter(new THREE.Vector3()).multiplyScalar(scale));
    radius = new THREE.Box3().setFromObject(gltf.scene).getBoundingSphere(new THREE.Sphere()).radius;
    gltf.scene.traverse((object) => { if (object instanceof THREE.Mesh) object.castShadow = true; });
    scene.add(gltf.scene);
    // 透明承影面让船底贴合海面，同时保留背景中的水纹。
    const waterline = new THREE.Mesh(new THREE.PlaneGeometry(24, 24), new THREE.ShadowMaterial({ color: 0x28686c, opacity: 0.3 }));
    waterline.rotation.x = -Math.PI / 2;
    waterline.position.y = new THREE.Box3().setFromObject(gltf.scene).min.y + 0.015;
    waterline.receiveShadow = true; scene.add(waterline);
    resizeObserver = new ResizeObserver(resize); resizeObserver.observe(root.value); resize();
    loading.value = false; resume();
  } catch (error) {
    if (current !== session) return;
    console.error("大屏梅利号加载失败", error); release(); loading.value = false; failed.value = true;
  }
}
function contextLost(event: Event) { event.preventDefault(); release(); failed.value = true; loading.value = false; }
onMounted(() => {
  void load();
  visibilityObserver = new IntersectionObserver(([entry]) => { visible = !!entry?.isIntersecting; resume(); });
  if (root.value) visibilityObserver.observe(root.value);
  document.addEventListener("visibilitychange", resume); motion.addEventListener("change", pauseMotion);
});
onBeforeUnmount(() => { release(); visibilityObserver?.disconnect(); document.removeEventListener("visibilitychange", resume); motion.removeEventListener("change", pauseMotion); });
</script>

<template>
  <div class="dashboard-merry" :aria-busy="loading">
    <div ref="root" class="merry-stage">
      <canvas ref="canvas" class="merry-canvas" :tabindex="failed || loading ? -1 : 0" aria-label="梅利号三维模型，可拖动旋转，方向键调整视角" @keydown="onKey" @webglcontextlost="contextLost"></canvas>
      <img v-if="failed" class="merry-fallback" :src="`${base}dashboard/going-merry.webp`" alt="梅利号" />
      <div v-if="loading" class="merry-loading"><LoaderCircle class="spin" :size="21" /><span>梅利号加载中</span></div>
    </div>
    <div class="merry-actions">
      <button v-if="failed" class="dashboard-tool" aria-label="重新加载梅利号" title="重新加载梅利号" @click="load"><RefreshCw :size="19" /></button>
      <template v-else>
        <button class="dashboard-tool" title="复位视角" aria-label="复位视角" :disabled="loading" @click="reset"><RotateCcw :size="19" /></button>
        <button class="dashboard-tool" title="缩小" aria-label="缩小梅利号" :disabled="loading" @click="zoom(1.12)"><Minus :size="19" /></button>
        <button class="dashboard-tool" title="放大" aria-label="放大梅利号" :disabled="loading" @click="zoom(0.88)"><Plus :size="19" /></button>
        <label class="merry-rotate"><span>自动旋转</span><input v-model="rotating" type="checkbox" role="switch" :disabled="loading || motion.matches" aria-label="自动旋转" /></label>
      </template>
    </div>
  </div>
</template>

<style scoped>
.dashboard-merry { position: relative; height: 100%; min-height: 0; }
.merry-stage { position: absolute; inset: -12px 0 10px; }
.merry-canvas { display: block; width: 100%; height: 100%; cursor: grab; touch-action: none; }
.merry-canvas:active { cursor: grabbing; }
.merry-fallback { width: 100%; height: 100%; position: absolute; inset: 0; object-fit: contain; }
.merry-loading { position: absolute; inset: 0; display: flex; justify-content: center; align-items: center; gap: 8px; font-size: 14px; color: #345d65; pointer-events: none; }
.merry-actions { position: absolute; right: 11px; bottom: 24px; display: flex; align-items: center; gap: 12px; }
.merry-actions .dashboard-tool { background: rgba(239,249,244,.78); border-radius: 50%; width: 34px; height: 34px; }
.merry-rotate { display: flex; align-items: center; gap: 12px; font-size: 12px; color: #466a75; cursor: pointer; }
.merry-rotate input { appearance: none; width: 36px; height: 21px; border-radius: 20px; background: #a7c9c8; border: 1px solid #8aafaf; position: relative; cursor: pointer; margin: 0; }
.merry-rotate input::after { content: ""; position: absolute; width: 16px; height: 16px; border-radius: 50%; background: #fff; top: 1.5px; left: 2px; transition: transform .2s; }
.merry-rotate input:checked { background: #398c93; }
.merry-rotate input:checked::after { transform: translateX(14px); }
.merry-rotate input:disabled { opacity: .55; cursor: default; }
.spin { animation: merry-spin 1s linear infinite; }
@keyframes merry-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .spin { animation: none; } .merry-rotate input::after { transition: none; } }
</style>
