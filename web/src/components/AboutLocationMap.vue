<script setup lang="ts">
import { load } from "@amap/amap-jsapi-loader";
import { MapPin } from "lucide-vue-next";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps<{
  name: string;
  longitude: number | null;
  latitude: number | null;
}>();

type MapInstance = {
  add: (overlay: unknown) => void;
  destroy: () => void;
};

const mapShell = ref<HTMLElement | null>(null);
const mapRoot = ref<HTMLElement | null>(null);
const mapStatus = ref<"idle" | "loading" | "ready" | "unavailable">("idle");
let mapInstance: MapInstance | undefined;
let visibilityObserver: IntersectionObserver | undefined;
let enteredViewport = false;
let disposed = false;
let renderVersion = 0;

const cityName = computed(() => props.name.trim() || "所在城市");
const hasCoordinates = computed(() => props.longitude !== null && props.latitude !== null);
const statusText = computed(() => {
  if (!hasCoordinates.value) return "暂未标记城市坐标";
  if (!import.meta.env.VITE_AMAP_WEB_KEY) return "地图服务暂未连接";
  if (mapStatus.value === "loading") return "正在展开城市地图";
  if (mapStatus.value === "unavailable") return "地图暂时无法加载";
  if (mapStatus.value === "idle") return "靠近后展开城市地图";
  return "";
});

async function renderMap() {
  if (disposed || !enteredViewport) return;
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
    if (disposed || version !== renderVersion || !mapRoot.value) return;

    const center = [longitude, latitude];
    mapInstance = new AMap.Map(mapRoot.value, {
      viewMode: "2D",
      zoom: 11,
      center,
      mapStyle: "amap://styles/darkblue",
      showLabel: true,
    }) as MapInstance;
    const marker = new AMap.Marker({
      position: center,
      anchor: "center",
      title: cityName.value,
      content: '<div class="about-map-marker" aria-hidden="true"><span></span></div>',
    });
    mapInstance.add(marker);
    mapStatus.value = "ready";
  } catch {
    if (!disposed && version === renderVersion) mapStatus.value = "unavailable";
  }
}

watch(
  () => [props.longitude, props.latitude, props.name],
  () => {
    if (enteredViewport) void renderMap();
  },
);

onMounted(() => {
  if (!mapShell.value) return;
  if (typeof IntersectionObserver === "undefined") {
    enteredViewport = true;
    void renderMap();
    return;
  }
  visibilityObserver = new IntersectionObserver(
    (entries) => {
      if (disposed || !entries.some((entry) => entry.isIntersecting)) return;
      enteredViewport = true;
      visibilityObserver?.disconnect();
      visibilityObserver = undefined;
      void renderMap();
    },
    { rootMargin: "300px" },
  );
  visibilityObserver.observe(mapShell.value);
});

onBeforeUnmount(() => {
  disposed = true;
  renderVersion += 1;
  visibilityObserver?.disconnect();
  visibilityObserver = undefined;
  mapInstance?.destroy();
  mapInstance = undefined;
});
</script>

<template>
  <div ref="mapShell" class="about-map-shell" :class="{ 'map-ready': mapStatus === 'ready' }">
    <div ref="mapRoot" class="about-map-canvas" :aria-label="`${cityName}高德地图`"></div>
    <div v-if="mapStatus !== 'ready'" class="about-map-fallback" role="status">
      <MapPin class="fallback-location" :size="32" :stroke-width="1.3" aria-hidden="true" />
      <strong>{{ cityName }}</strong>
      <p>{{ statusText }}</p>
    </div>
    <div v-if="mapStatus === 'ready'" class="about-map-caption">
      <span>所在城市</span>
      <strong>{{ cityName }}</strong>
    </div>
  </div>
</template>

<style scoped>
.about-map-shell {
  position: relative;
  overflow: hidden;
  min-height: 300px;
  border: 1px solid rgba(169, 187, 192, 0.18);
  border-radius: 4px;
  background: #061a22;
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
  padding: 2rem;
  color: #f3edda;
  text-align: center;
  background:
    radial-gradient(ellipse at center, rgba(38, 78, 88, 0.3), transparent 70%),
    #061a22;
}

.about-map-fallback strong {
  margin-top: 1rem;
  font-size: 1rem;
  overflow-wrap: anywhere;
}

.about-map-fallback p {
  margin: 0.45rem 0 0;
  color: #a9bbc0;
  font-size: 0.82rem;
  line-height: 1.6;
}

.fallback-location {
  color: #e2bc74;
}

.about-map-caption {
  position: absolute;
  top: 0.65rem;
  right: 0.65rem;
  z-index: 2;
  display: grid;
  gap: 0.2rem;
  max-width: calc(100% - 1.3rem);
  padding: 0.55rem 0.7rem;
  border: 1px solid rgba(169, 187, 192, 0.18);
  border-radius: 3px;
  color: #f3edda;
  background: rgba(6, 26, 34, 0.92);
  backdrop-filter: blur(10px);
  pointer-events: none;
}

.about-map-caption span {
  color: #a9bbc0;
  font-size: 0.7rem;
}
.about-map-caption strong {
  font-size: 0.9rem;
  overflow-wrap: anywhere;
}

:deep(.about-map-marker) {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border: 1px solid rgba(226, 188, 116, 0.56);
  border-radius: 50%;
  background: rgba(226, 188, 116, 0.12);
}

:deep(.about-map-marker span) {
  width: 14px;
  height: 14px;
  border: 4px solid #f3edda;
  border-radius: 50%;
  background: #e2bc74;
  box-shadow: 0 0 0 3px #e2bc74;
}

@media (prefers-reduced-motion: reduce) {
  .about-map-canvas {
    transition: none;
  }
}
</style>
