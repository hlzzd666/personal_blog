<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef } from "vue";
import { fetchGallery, type GalleryCharacter, type GalleryResponse } from "../api/gallery";
import { GalleryScene, localPosterUrl, type NavigationState } from "../gallery/GalleryScene";
import OceanIcon from "../components/OceanIcon.vue";

const sceneRoot = ref<HTMLElement | null>(null);
const detailDialog = ref<HTMLDialogElement | null>(null);
const gallery = shallowRef<GalleryResponse | null>(null);
const navigation = shallowRef<NavigationState | null>(null);
const loading = ref(true);
const sceneLoading = ref(false);
const error = ref("");
const notice = ref("");
const desktopSupported = ref(false);
const entered = ref(false);
const locked = ref(false);
const activeCharacter = shallowRef<GalleryCharacter | null>(null);
const activeSlot = ref<number | null>(null);
const selectedCharacter = shallowRef<GalleryCharacter | null>(null);
const selectedSlot = ref<number | null>(null);
let scene: GalleryScene | null = null;
let generation = 0;
let resumeAfterDialog = false;
const characters = computed(() => gallery.value?.characters ?? []);
const mapY = (z: number) =>
  navigation.value
    ? 18 +
      ((z - navigation.value.hall.minZ) /
        (navigation.value.hall.maxZ - navigation.value.hall.minZ)) *
        224
    : 0;
const mapX = (x: number) => 90 + x * 11;
const markers = computed(() => {
  const result: NonNullable<NavigationState["markers"]> = [];
  for (const marker of [...(navigation.value?.markers ?? [])].sort(
    (a, b) => a.distance - b.distance,
  )) {
    if (marker.screenY < 15 || marker.screenY > 82 || marker.screenX > 79) continue;
    if (
      result.some(
        (other) =>
          Math.abs(other.screenX - marker.screenX) < 8 &&
          Math.abs(other.screenY - marker.screenY) < 7,
      )
    )
      continue;
    result.push(marker);
    if (result.length === 4) break;
  }
  return result;
});

function supportsGallery() {
  if (
    innerWidth < 1024 ||
    !matchMedia("(hover: hover) and (pointer: fine)").matches ||
    !("pointerLockElement" in document)
  )
    return false;
  const canvas = document.createElement("canvas");
  const gl = canvas.getContext("webgl2");
  if (!gl) return false;
  gl.getExtension("WEBGL_lose_context")?.loseContext();
  return true;
}

function fallback(reason = "") {
  notice.value = reason;
  desktopSupported.value = false;
  entered.value = locked.value = sceneLoading.value = false;
  scene?.dispose();
  scene = null;
}

async function loadGallery() {
  const run = ++generation;
  scene?.dispose();
  scene = null;
  loading.value = true;
  error.value = "";
  notice.value = "";
  entered.value = locked.value = false;
  activeCharacter.value = null;
  navigation.value = null;
  try {
    const data = await fetchGallery();
    if (run !== generation) return;
    gallery.value = {
      ...data,
      characters: data.characters
        .filter((item) => item.is_visible)
        .sort((a, b) => a.sort_order - b.sort_order || a.id - b.id)
        .slice(0, 40),
    };
  } catch {
    if (run === generation) {
      loading.value = false;
      error.value = "人物档案读取失败，请稍后重试。";
    }
    return;
  }
  loading.value = false;
  desktopSupported.value = supportsGallery();
  if (!desktopSupported.value) return;
  sceneLoading.value = true;
  await nextTick();
  if (run !== generation || !sceneRoot.value) return;
  try {
    const current = new GalleryScene(
      sceneRoot.value,
      characters.value,
      matchMedia("(prefers-reduced-motion: reduce)").matches,
      {
        onActiveCharacter(character, slot) {
          activeCharacter.value = character;
          activeSlot.value = slot;
        },
        onLockChange(value) {
          locked.value = value;
        },
        onOpenCharacter: openCharacter,
        onNavigation(state) {
          navigation.value = state;
        },
        onUnavailable: fallback,
      },
    );
    scene = current;
    await current.ready;
    if (run !== generation) {
      current.dispose();
      return;
    }
    sceneLoading.value = false;
  } catch {
    if (run === generation) fallback("船舱暂时无法载入，人物档案仍可查阅。");
  }
}

function startTour() {
  entered.value = true;
  scene?.lock();
}
function toggleTour() {
  if (locked.value) scene?.unlock();
  else scene?.lock();
}
function openCharacter(character: GalleryCharacter, slot: number | null = activeSlot.value) {
  resumeAfterDialog = locked.value;
  selectedCharacter.value = character;
  selectedSlot.value = slot;
  scene?.unlock();
  void nextTick(() => detailDialog.value?.showModal());
}
function closeCharacter() {
  detailDialog.value?.close();
  selectedCharacter.value = null;
  selectedSlot.value = null;
  if (resumeAfterDialog) scene?.lock();
}
function imageError(event: Event) {
  (event.currentTarget as HTMLImageElement).hidden = true;
}
function resizeDevice() {
  if (innerWidth < 1024 && scene) fallback();
}
onMounted(() => {
  void loadGallery();
  window.addEventListener("resize", resizeDevice);
});
onBeforeUnmount(() => {
  generation++;
  scene?.dispose();
  scene = null;
  window.removeEventListener("resize", resizeDevice);
});
</script>

<template>
  <main class="gallery-page">
    <section v-if="loading || error" class="gallery-status" :role="error ? 'alert' : 'status'">
      <OceanIcon :name="error ? 'warning' : 'gallery'" :size="48" />
      <h1>{{ error ? "展馆暂未开启" : "正在开启展馆" }}</h1>
      <p v-if="error">{{ error }}</p>
      <div class="gallery-actions">
        <button v-if="error" class="primary" @click="loadGallery">重新读取</button>
        <RouterLink class="secondary" to="/"
          ><OceanIcon name="home" :size="18" />返回博客</RouterLink
        >
      </div>
    </section>

    <template v-else-if="gallery">
      <section v-if="desktopSupported" class="gallery-experience" aria-label="旗舰船舱展馆">
        <div ref="sceneRoot" class="gallery-scene-root"></div>
        <header class="gallery-topbar">
          <RouterLink to="/" class="exit-link"
            ><OceanIcon name="previous" :size="22" />返回博客</RouterLink
          >
          <span class="hall-name">{{ gallery.settings.hall_name }}</span>
          <button v-if="entered" class="secondary compact" @click="toggleTour">
            {{ locked ? "暂停漫游" : "继续漫游" }}
          </button>
          <span v-else class="gallery-count">{{ characters.length }} / 40</span>
        </header>

        <div
          v-if="!entered || (!locked && !selectedCharacter)"
          class="entry-layer"
          :class="{ paused: entered }"
        >
          <div class="entry-copy">
            <img
              v-if="gallery.settings.show_logo && gallery.settings.logo_url && !entered"
              class="entry-logo"
              :src="localPosterUrl(gallery.settings.logo_url)"
              alt="展馆 Logo"
              width="72"
              height="72"
              @error="imageError"
            />
            <h1>{{ entered ? "漫游已暂停" : gallery.settings.hall_name }}</h1>
            <p>{{ entered ? navigation?.zone : gallery.settings.entry_title }}</p>
            <div class="gallery-actions">
              <button class="primary" :disabled="sceneLoading" @click="startTour">
                <OceanIcon name="next" :size="22" />{{
                  sceneLoading ? "船舱载入中" : entered ? "继续漫游" : "进入展馆"
                }}
              </button>
              <button class="secondary" @click="fallback()">
                <OceanIcon name="archive" :size="20" />人物档案
              </button>
            </div>
            <p v-if="!characters.length" class="empty-note">展馆正在布展</p>
          </div>
        </div>

        <template v-if="entered && navigation && !selectedCharacter">
          <aside class="gallery-minimap" aria-label="船舱航图">
            <div class="map-title">
              <OceanIcon name="location" :size="20" /><strong>{{ navigation.zone }}</strong
              ><span>{{ characters.length }} 位</span>
            </div>
            <svg viewBox="0 0 180 260" role="img" aria-label="船舱、当前所在位置与视野内展位">
              <path
                :d="`M 90 18 L 145 ${mapY(navigation.hall.cabinFront - 3)} L 145 228 Q 145 242 130 242 L 50 242 Q 35 242 35 228 L 35 ${mapY(navigation.hall.cabinFront - 3)} Z`"
                fill="#d9e5de"
                fill-opacity=".12"
                stroke="#92bfb2"
                stroke-width="1.2"
              />
              <path
                :d="`M 35 ${mapY(navigation.hall.cabinFront)} H 145 M 35 ${mapY(navigation.hall.cabinBack)} H 145`"
                stroke="#92bfb2"
                stroke-dasharray="3 4"
              />
              <path
                d="M 90 30 V 232"
                stroke="#d9e5de"
                stroke-opacity=".25"
                stroke-dasharray="2 5"
              />
              <circle
                v-for="marker in navigation.markers"
                :key="marker.slot"
                :cx="mapX(marker.x)"
                :cy="mapY(marker.z)"
                r="3"
                :fill="marker.near ? '#ffd593' : '#a1cbbb'"
              >
                <title>{{ marker.slot }} · {{ marker.name }}</title>
              </circle>
              <g
                :transform="`translate(${mapX(navigation.x)}, ${mapY(navigation.z)}) rotate(${(navigation.heading * 180) / Math.PI})`"
              >
                <path
                  d="M 0 -8 L 5 5 L 0 2 L -5 5 Z"
                  fill="#ff8f79"
                  stroke="#fff3df"
                  stroke-width="1"
                />
              </g>
              <text x="90" y="10" fill="#d4e5dd" text-anchor="middle" font-size="8">船首</text>
              <text x="90" y="255" fill="#d4e5dd" text-anchor="middle" font-size="8">船尾</text>
            </svg>
          </aside>
          <template v-if="locked">
            <div
              class="gallery-crosshair"
              :class="{ active: activeCharacter }"
              aria-hidden="true"
            ></div>
            <div
              v-for="marker in markers"
              :key="marker.slot"
              class="gallery-nav-marker"
              :class="{ near: marker.near }"
              :style="{ left: `${marker.screenX}%`, top: `${marker.screenY}%` }"
              aria-hidden="true"
            >
              <b>{{ String(marker.slot).padStart(2, "0") }}</b
              ><span>{{ marker.distance }} m</span>
            </div>
            <button
              v-if="activeCharacter"
              class="gallery-active-prompt"
              @click="openCharacter(activeCharacter)"
            >
              <span>{{ String(activeSlot).padStart(2, "0") }}</span
              ><strong>{{ activeCharacter.name }}</strong
              ><span>查看档案</span><OceanIcon name="next" :size="20" />
            </button>
          </template>
        </template>
      </section>

      <section v-else class="gallery-fallback">
        <header class="fallback-header">
          <div>
            <h1>{{ gallery.settings.hall_name }}</h1>
            <p>{{ gallery.settings.entry_title }}</p>
          </div>
          <RouterLink class="secondary" to="/"
            ><OceanIcon name="home" :size="18" />返回博客</RouterLink
          >
        </header>
        <p v-if="notice" class="gallery-notice" role="status">
          {{ notice }} <button class="text-button" @click="loadGallery">重试</button>
        </p>
        <div v-if="characters.length" class="fallback-grid">
          <article
            v-for="(character, index) in characters"
            :key="character.id"
            class="fallback-item"
          >
            <button
              class="poster-button"
              :aria-label="`查看${character.name}档案`"
              @click="openCharacter(character, index + 1)"
            >
              <span class="poster-placeholder"
                ><small>{{ String(index + 1).padStart(2, "0") }}</small
                ><strong>{{ character.name }}</strong
                ><span>{{ character.bounty }}</span></span
              >
              <img
                v-if="character.poster_url"
                :src="localPosterUrl(character.poster_url)"
                :alt="`${character.name}海报`"
                width="512"
                height="768"
                loading="lazy"
                decoding="async"
                @error="imageError"
              />
            </button>
            <div class="fallback-copy">
              <h2>{{ character.name }}</h2>
              <p>{{ character.epithet }} · {{ character.faction }}</p>
              <button class="text-button" @click="openCharacter(character, index + 1)">
                查看档案<OceanIcon name="next" :size="18" />
              </button>
            </div>
          </article>
        </div>
        <p v-else class="fallback-empty">展馆正在布展</p>
      </section>

      <dialog
        ref="detailDialog"
        class="gallery-character-dialog"
        aria-labelledby="character-title"
        @cancel.prevent="closeCharacter"
      >
        <article v-if="selectedCharacter" class="character-record">
          <button class="dialog-close secondary" autofocus @click="closeCharacter">关闭</button>
          <div class="dialog-poster">
            <div class="poster-placeholder">
              <small>{{ String(selectedSlot).padStart(2, "0") }}</small
              ><strong>{{ selectedCharacter.name }}</strong
              ><span>{{ selectedCharacter.bounty }}</span>
            </div>
            <img
              v-if="selectedCharacter.poster_url"
              :src="localPosterUrl(selectedCharacter.poster_url)"
              :alt="`${selectedCharacter.name}海报`"
              width="512"
              height="768"
              decoding="async"
              @error="imageError"
            />
          </div>
          <div class="dialog-copy">
            <h2 id="character-title">{{ selectedCharacter.name }}</h2>
            <p class="character-meta">
              {{ selectedCharacter.epithet }} · {{ selectedCharacter.faction }}
            </p>
            <dl>
              <div>
                <dt>悬赏</dt>
                <dd>{{ selectedCharacter.bounty }}</dd>
              </div>
              <div>
                <dt>能力</dt>
                <dd>{{ selectedCharacter.ability }}</dd>
              </div>
            </dl>
            <p class="character-description">{{ selectedCharacter.description }}</p>
            <blockquote>{{ selectedCharacter.quote }}</blockquote>
          </div>
        </article>
      </dialog>
    </template>
  </main>
</template>

<style scoped>
.gallery-page {
  min-height: 100dvh;
  background: #edf3ee;
  color: #193e37;
  font-family: "Noto Sans SC", sans-serif;
  letter-spacing: 0;
}
.gallery-page :is(button, a) {
  -webkit-tap-highlight-color: transparent;
}
.gallery-page button {
  font: inherit;
  cursor: pointer;
}
.gallery-page :is(button, a):focus-visible {
  outline: 3px solid #e76b51;
  outline-offset: 4px;
}
.gallery-page ::selection {
  background: #ffbaa3;
  color: #173e35;
}
.gallery-page h1,
.gallery-page h2 {
  font-family: var(--display-font);
  overflow-wrap: anywhere;
  letter-spacing: 0;
}
.gallery-experience,
.gallery-scene-root {
  position: fixed;
  inset: 0;
}
.gallery-scene-root :deep(canvas) {
  display: block;
  width: 100%;
  height: 100%;
}
.gallery-status {
  min-height: 100dvh;
  display: grid;
  align-content: center;
  justify-items: center;
  padding: 24px;
  text-align: center;
}
.gallery-status h1 {
  font-size: 30px;
}
.gallery-status p {
  line-height: 1.7;
}
.gallery-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.primary,
.secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 46px;
  padding: 10px 18px;
  border-radius: 4px;
  text-decoration: none;
  box-sizing: border-box;
  font-size: 14px;
  font-weight: 700;
}
.primary {
  background: #174e43;
  border: 1px solid #a4cabb;
  color: #fffaf0;
}
.primary:hover {
  background: #276b5c;
}
.primary:disabled {
  opacity: 0.65;
  cursor: progress;
}
.secondary {
  border: 1px solid #8ba69b;
  color: #24473c;
  background: #edf3eeef;
}
.secondary:hover {
  background: #d8e9df;
}
.compact {
  min-height: 36px;
  padding: 6px 12px;
}
.gallery-topbar {
  position: absolute;
  z-index: 15;
  inset: 0 0 auto;
  display: grid;
  grid-template-columns: 1fr minmax(0, 2fr) 1fr;
  gap: 16px;
  align-items: center;
  min-height: 62px;
  padding: 8px 26px;
  background: #f0f5eeef;
  border-bottom: 1px solid #69877980;
  box-sizing: border-box;
}
.gallery-topbar > :last-child {
  justify-self: end;
}
.exit-link {
  display: flex;
  gap: 8px;
  align-items: center;
  color: #24473c;
  text-decoration: none;
  font-size: 13px;
}
.hall-name {
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  font-weight: 700;
}
.gallery-count {
  font:
    12px "IBM Plex Mono",
    monospace;
}
.entry-layer {
  position: absolute;
  inset: 62px 0 0;
  z-index: 8;
  display: flex;
  align-items: flex-end;
  padding: 5% 5% 48px;
  box-sizing: border-box;
  pointer-events: none;
  background: #071e1215;
}
.entry-copy {
  max-width: 580px;
  color: #123a30;
  text-shadow: 0 1px 2px #fffbee;
  pointer-events: auto;
}
.entry-copy h1 {
  -webkit-text-stroke: 1.5px #fffbee;
  paint-order: stroke fill;
  font-size: 42px;
  line-height: 1.2;
  margin: 12px 0;
  max-width: 13ch;
  text-wrap: balance;
}
.entry-copy p {
  font-size: 15px;
  line-height: 1.8;
  max-width: 48ch;
}
.entry-copy .gallery-actions {
  text-shadow: none;
  margin-top: 22px;
}
.entry-logo {
  width: 64px;
  height: 64px;
  object-fit: contain;
}
.entry-copy .empty-note {
  font-size: 13px;
}
.paused .entry-copy h1 {
  font-size: 34px;
}
.gallery-minimap {
  position: absolute;
  right: 22px;
  top: 84px;
  width: 190px;
  height: 312px;
  padding: 12px;
  border: 1px solid #a8c5ae80;
  border-radius: 4px;
  box-sizing: border-box;
  background: #143a32df;
  color: #e0eee3;
  pointer-events: none;
  z-index: 9;
}
.map-title {
  display: flex;
  gap: 7px;
  align-items: center;
  font-size: 12px;
}
.map-title > span {
  margin-left: auto;
  font-size: 10px;
  white-space: nowrap;
}
.gallery-minimap svg {
  display: block;
  width: 100%;
  height: 266px;
  margin-top: 4px;
}
.gallery-crosshair {
  position: absolute;
  z-index: 7;
  top: 50%;
  left: 50%;
  width: 6px;
  height: 6px;
  border: 1px solid #244c3b;
  border-radius: 50%;
  background: #fffef1;
  transform: translate(-50%, -50%);
  pointer-events: none;
}
.gallery-crosshair.active {
  background: #ff9b76;
  border-color: #fff6d5;
}
.gallery-nav-marker {
  position: absolute;
  z-index: 6;
  display: flex;
  gap: 6px;
  align-items: center;
  transform: translate(-50%, -50%);
  padding: 4px 7px;
  border-bottom: 1px solid #bfd7c2;
  color: #fffbee;
  background: #173e34cb;
  font:
    11px "IBM Plex Mono",
    monospace;
  pointer-events: none;
  white-space: nowrap;
}
.gallery-nav-marker.near {
  color: #ffdb9a;
  border-color: #ffdb9a;
}
.gallery-active-prompt {
  position: absolute;
  z-index: 10;
  left: 50%;
  bottom: 28px;
  display: flex;
  align-items: center;
  gap: 16px;
  width: min(480px, calc(100% - 48px));
  min-height: 54px;
  padding: 12px 18px;
  transform: translateX(-50%);
  color: #fff7df;
  background: #17483eee;
  border: 1px solid #c6b27f;
  border-radius: 4px;
}
.gallery-active-prompt strong {
  flex: 1;
  min-width: 0;
  overflow-wrap: anywhere;
  text-align: left;
}
.gallery-active-prompt span {
  font-size: 12px;
  flex-shrink: 0;
}
.gallery-fallback {
  max-width: 1200px;
  margin: auto;
  padding: 32px 24px 64px;
}
.fallback-header {
  display: flex;
  gap: 24px;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 26px;
  border-bottom: 1px solid #adc6b9;
}
.fallback-header h1 {
  margin: 0 0 12px;
  font-size: 34px;
}
.fallback-header p {
  margin: 0;
  color: #527266;
  line-height: 1.7;
}
.fallback-header .secondary {
  flex-shrink: 0;
}
.fallback-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 32px 26px;
  padding-top: 28px;
}
.fallback-item {
  min-width: 0;
}
.poster-button,
.dialog-poster {
  position: relative;
  display: block;
  width: 100%;
  aspect-ratio: 2 / 3;
  background: #cbdcd1;
  overflow: hidden;
  border: 0;
  padding: 0;
  color: #355c52;
}
.poster-placeholder {
  display: flex;
  position: absolute;
  inset: 0;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 20px;
  text-align: center;
  padding: 24px;
  box-sizing: border-box;
  overflow-wrap: anywhere;
}
.poster-placeholder small {
  font:
    56px "IBM Plex Mono",
    monospace;
  color: #5b8070;
}
.poster-placeholder strong {
  font-family: var(--display-font);
  font-size: 28px;
  line-height: 1.4;
}
.poster-placeholder span {
  font-size: 13px;
}
.poster-button img,
.dialog-poster img {
  display: block;
  position: relative;
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.fallback-copy {
  padding: 16px 0;
  border-bottom: 1px solid #adc6b9;
}
.fallback-copy h2 {
  font-size: 24px;
  margin: 0;
}
.fallback-copy p {
  font-size: 13px;
  line-height: 1.7;
  color: #527266;
}
.text-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: none;
  padding: 7px 0;
  background: transparent;
  color: #215647;
  text-decoration: underline;
  text-underline-offset: 4px;
}
.gallery-notice {
  padding: 14px 0;
  font-size: 14px;
  line-height: 1.7;
}
.fallback-empty {
  text-align: center;
  padding: 70px 12px;
}
.gallery-character-dialog {
  position: fixed;
  inset: 0;
  width: min(960px, calc(100% - 32px));
  max-height: calc(100dvh - 32px);
  margin: auto;
  padding: 0;
  border: 1px solid #789688;
  border-radius: 6px;
  background: #f1f5ee;
  color: #234737;
  overflow: auto;
  scrollbar-color: #7b9e8b #e5eee5;
}
.gallery-character-dialog::backdrop {
  background: #071d18a6;
}
.character-record {
  display: grid;
  grid-template-columns: minmax(0, 0.85fr) minmax(0, 1.15fr);
  align-items: start;
}
.dialog-close {
  position: absolute;
  z-index: 2;
  top: 14px;
  right: 14px;
  min-height: 38px;
}
.dialog-copy {
  padding: 60px 34px 32px;
  min-width: 0;
  overflow-wrap: anywhere;
}
.dialog-copy h2 {
  font-size: 32px;
  line-height: 1.25;
  margin: 0 0 12px;
}
.character-meta {
  font-size: 14px;
  line-height: 1.7;
  color: #5b725d;
}
.dialog-copy dl {
  display: grid;
  gap: 16px;
  border-top: 1px solid #b6c9b9;
  border-bottom: 1px solid #b6c9b9;
  padding: 20px 0;
  margin: 24px 0;
}
.dialog-copy dt {
  color: #647966;
  font-size: 12px;
  margin-bottom: 6px;
}
.dialog-copy dd {
  font-size: 15px;
  margin: 0;
  line-height: 1.7;
}
.character-description {
  line-height: 1.9;
  font-size: 15px;
  white-space: pre-wrap;
}
.dialog-copy blockquote {
  margin: 24px 0 0;
  padding-top: 18px;
  border-top: 1px solid #b6c9b9;
  color: #387862;
  line-height: 1.8;
}
@media (max-height: 680px) {
  .gallery-minimap {
    height: 250px;
    width: 155px;
  }
  .gallery-minimap svg {
    height: 204px;
  }
  .entry-layer {
    padding-bottom: 24px;
  }
  .entry-logo {
    display: none;
  }
  .entry-copy h1 {
    font-size: 32px;
  }
}
@media (max-width: 720px) {
  .gallery-fallback {
    padding: 24px 18px 40px;
  }
  .fallback-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 18px;
  }
  .fallback-header h1 {
    font-size: 28px;
  }
  .fallback-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 20px 14px;
  }
  .fallback-copy h2 {
    font-size: 19px;
  }
  .poster-placeholder {
    padding: 12px;
    gap: 10px;
  }
  .poster-placeholder strong {
    font-size: 20px;
  }
  .poster-placeholder small {
    font-size: 34px;
  }
  .character-record {
    grid-template-columns: 1fr;
  }
  .dialog-poster {
    max-width: 290px;
    justify-self: center;
  }
  .dialog-copy {
    padding: 28px 22px;
  }
  .dialog-copy h2 {
    font-size: 28px;
  }
}
@media (max-width: 380px) {
  .fallback-grid {
    grid-template-columns: 1fr;
  }
}
</style>
