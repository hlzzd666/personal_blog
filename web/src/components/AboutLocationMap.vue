<script setup lang="ts">
import { load } from "@amap/amap-jsapi-loader";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps<{
  name: string;
  longitude: number | null;
  latitude: number | null;
}>();

type MapInstance = {
  add: (overlay: unknown) => void;
  addControl: (control: unknown) => void;
  destroy: () => void;
};

const mapRoot = ref<HTMLElement | null>(null);
const mapStatus = ref<"idle" | "loading" | "ready" | "unavailable">("idle");
let mapInstance: MapInstance | undefined;
let renderVersion = 0;

const hasCoordinates = computed(() => props.longitude !== null && props.latitude !== null);
const statusText = computed(() => {
  if (!hasCoordinates.value) return "城市坐标等待维护";
  if (!import.meta.env.VITE_AMAP_WEB_KEY) return "地图服务暂未连接";
  if (mapStatus.value === "loading") return "正在展开城市地图";
  if (mapStatus.value === "unavailable") return "地图暂时无法加载";
  return "";
});

async function renderMap() {
  const version = ++renderVersion;
  mapInstance?.destroy();
  mapInstance = undefined;

  if (
    !mapRoot.value ||
    props.longitude === null ||
    props.latitude === null ||
    !import.meta.env.VITE_AMAP_WEB_KEY
  ) {
    mapStatus.value = "unavailable";
    return;
  }

  const longitude = props.longitude;
  const latitude = props.latitude;

  mapStatus.value = "loading";
  const securityCode = import.meta.env.VITE_AMAP_SECURITY_CODE;
  if (securityCode) {
    window._AMapSecurityConfig = { securityJsCode: securityCode };
  }

  try {
    const AMap = await load({
      key: import.meta.env.VITE_AMAP_WEB_KEY,
      version: "2.0",
    });
    if (version !== renderVersion || !mapRoot.value) return;

    const center = [longitude, latitude];
    mapInstance = new AMap.Map(mapRoot.value, {
      viewMode: "2D",
      zoom: 11,
      center,
      mapStyle: "amap://styles/whitesmoke",
      showLabel: true,
    }) as MapInstance;
    const marker = new AMap.Marker({
      position: center,
      anchor: "center",
      title: props.name,
      content: '<div class="about-map-marker" aria-hidden="true"><span></span></div>',
    });
    mapInstance.add(marker);
    mapStatus.value = "ready";
  } catch {
    if (version === renderVersion) mapStatus.value = "unavailable";
  }
}

watch(
  () => [props.longitude, props.latitude, props.name],
  async () => {
    await nextTick();
    void renderMap();
  },
);

onMounted(() => {
  void renderMap();
});

onBeforeUnmount(() => {
  renderVersion += 1;
  mapInstance?.destroy();
});
</script>

<template>
  <div class="about-map-shell" :class="{ 'map-ready': mapStatus === 'ready' }">
    <div ref="mapRoot" class="about-map-canvas" :aria-label="`${name}高德地图`"></div>
    <div v-if="mapStatus !== 'ready'" class="about-map-fallback" role="status">
      <div class="fallback-radar" aria-hidden="true"><i></i><span></span></div>
      <strong>{{ name }}</strong>
      <p>{{ statusText }}</p>
    </div>
    <div class="about-map-caption">
      <span>AMAP / CITY VIEW</span>
      <strong>{{ name }}</strong>
    </div>
  </div>
</template>

<style scoped>
.about-map-shell {
  position: relative;
  overflow: hidden;
  min-height: 224px;
  border-radius: 8px;
  background: #d7e1dd;
  box-shadow: 0 1.5rem 4rem rgba(7, 24, 35, 0.14);
}

.about-map-canvas {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.5s ease;
}

.map-ready .about-map-canvas {
  opacity: 1;
}

.about-map-fallback {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  justify-items: center;
  color: #0d2a38;
  background:
    linear-gradient(35deg, transparent 48%, rgba(13, 42, 56, 0.08) 49% 51%, transparent 52%) 0 0 /
      54px 54px,
    linear-gradient(-35deg, transparent 48%, rgba(13, 42, 56, 0.06) 49% 51%, transparent 52%) 0 0 /
      54px 54px,
    #d7e1dd;
}

.about-map-fallback strong {
  margin-top: 0.65rem;
  font-size: 1rem;
}

.about-map-fallback p {
  margin: 0.45rem 0 0;
  color: rgba(13, 42, 56, 0.58);
  font-size: 0.78rem;
}

.fallback-radar {
  position: relative;
  width: 5.5rem;
  aspect-ratio: 1;
  border: 1px solid rgba(13, 42, 56, 0.32);
  border-radius: 50%;
}

.fallback-radar::before,
.fallback-radar::after {
  content: "";
  position: absolute;
  border: 1px solid rgba(13, 42, 56, 0.18);
  border-radius: 50%;
}

.fallback-radar::before {
  inset: 22%;
}
.fallback-radar::after {
  inset: 42%;
  background: #e7674c;
  border-color: #e7674c;
}
.fallback-radar i {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 44%;
  height: 1px;
  background: #e7674c;
  transform-origin: left;
  animation: radar-scan 4s linear infinite;
}
.fallback-radar span {
  position: absolute;
  inset: 50% 0 auto;
  height: 1px;
  background: rgba(13, 42, 56, 0.16);
}

.about-map-caption {
  position: absolute;
  right: 0.65rem;
  bottom: 0.65rem;
  z-index: 2;
  display: grid;
  gap: 0.2rem;
  min-width: 142px;
  padding: 0.55rem 0.7rem;
  border-radius: 5px;
  color: #fff8e9;
  background: rgba(7, 24, 35, 0.9);
  box-shadow: 0 0.7rem 2rem rgba(7, 24, 35, 0.2);
  backdrop-filter: blur(10px);
}

.about-map-caption span {
  color: #f2bc5a;
  font:
    600 0.62rem "IBM Plex Mono",
    monospace;
}
.about-map-caption strong {
  font-size: 0.9rem;
}

:deep(.about-map-marker) {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border: 1px solid rgba(231, 103, 76, 0.56);
  border-radius: 50%;
  background: rgba(231, 103, 76, 0.12);
  animation: map-marker-pulse 2.4s ease-in-out infinite;
}

:deep(.about-map-marker span) {
  width: 14px;
  height: 14px;
  border: 4px solid #fff8e9;
  border-radius: 50%;
  background: #e7674c;
  box-shadow: 0 0 0 3px #e7674c;
}

@keyframes radar-scan {
  to {
    transform: rotate(360deg);
  }
}
@keyframes map-marker-pulse {
  50% {
    box-shadow: 0 0 0 16px rgba(231, 103, 76, 0.06);
  }
}

@media (max-width: 760px) {
  .about-map-shell {
    min-height: 210px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .about-map-canvas {
    transition: none;
  }
  .fallback-radar i,
  :deep(.about-map-marker) {
    animation: none;
  }
}
</style>
