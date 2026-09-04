<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue";

import { fetchGallery, type GalleryCharacter, type GalleryResponse } from "../api/gallery";
import { GalleryScene } from "../gallery/GalleryScene";
import OceanIcon from "../components/OceanIcon.vue";

const sceneRoot = ref<HTMLElement | null>(null);
const detailDialog = ref<HTMLDialogElement | null>(null);
const gallery = ref<GalleryResponse | null>(null);
const loading = ref(true);
const errorMessage = ref("");
const desktopSupported = ref(false);
const entered = ref(false);
const locked = ref(false);
const activeCharacter = ref<GalleryCharacter | null>(null);
const activeSlot = ref<number | null>(null);
const selectedCharacter = ref<GalleryCharacter | null>(null);
const selectedSlot = ref<number | null>(null);
let galleryScene: GalleryScene | null = null;

function supportsGalleryExperience() {
  if (window.innerWidth < 1024) return false;
  if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return false;
  if (!("pointerLockElement" in document)) return false;
  const canvas = document.createElement("canvas");
  return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
}

async function loadGallery() {
  galleryScene?.dispose();
  galleryScene = null;
  loading.value = true;
  errorMessage.value = "";
  entered.value = false;
  locked.value = false;
  try {
    gallery.value = await fetchGallery();
    loading.value = false;
    await nextTick();
    if (desktopSupported.value && sceneRoot.value) {
      galleryScene = new GalleryScene(
        sceneRoot.value,
        gallery.value.characters,
        window.matchMedia("(prefers-reduced-motion: reduce)").matches,
        {
          onActiveCharacter(character, slot) {
            activeCharacter.value = character;
            activeSlot.value = slot;
          },
          onLockChange(value) {
            locked.value = value;
          },
          onOpenCharacter(character, slot) {
            openCharacter(character, slot);
          },
        },
      );
    }
  } catch {
    loading.value = false;
    errorMessage.value = "展厅档案读取失败，请确认服务可用后重试。";
  }
}

function startTour() {
  if (!gallery.value?.characters.length) return;
  entered.value = true;
  galleryScene?.lock();
}

function pauseTour() {
  galleryScene?.unlock();
}

function resumeTour() {
  galleryScene?.lock();
}

function openCharacter(character: GalleryCharacter, slot = activeSlot.value) {
  selectedCharacter.value = character;
  selectedSlot.value = slot;
  galleryScene?.unlock();
  void nextTick(() => detailDialog.value?.showModal());
}

function closeCharacter() {
  detailDialog.value?.close();
  selectedCharacter.value = null;
  selectedSlot.value = null;
  galleryScene?.lock();
}

function handleDialogCancel(event: Event) {
  event.preventDefault();
  closeCharacter();
}

function handleImageError(event: Event) {
  (event.currentTarget as HTMLImageElement).hidden = true;
}

function posterDisplayUrl(character: GalleryCharacter) {
  return character.poster_url || undefined;
}

onMounted(() => {
  desktopSupported.value = supportsGalleryExperience();
  void loadGallery();
});

onBeforeUnmount(() => {
  galleryScene?.dispose();
  galleryScene = null;
});
</script>

<template>
  <main class="gallery-page">
    <section v-if="loading" class="gallery-status-screen" aria-live="polite">
      <span class="gallery-compass-loader" aria-hidden="true"></span>
      <h1>正在开启展厅</h1>
      <p>航线与人物档案正在就位。</p>
    </section>

    <section v-else-if="errorMessage" class="gallery-status-screen" role="alert">
      <OceanIcon class="gallery-status-mark" name="warning" :size="48" />
      <h1>展厅暂未开启</h1>
      <p>{{ errorMessage }}</p>
      <div class="gallery-status-actions">
        <button type="button" class="gallery-primary-action" @click="loadGallery">重新读取</button>
        <RouterLink class="gallery-secondary-action" to="/"><OceanIcon name="home" :size="18" />返回博客</RouterLink>
      </div>
    </section>

    <template v-else-if="gallery">
      <section v-if="!desktopSupported" class="gallery-fallback">
        <header class="gallery-fallback-header">
          <div>
            <h1>{{ gallery.settings.hall_name }}</h1>
            <p>当前设备使用人物档案视图；电脑端可进入完整 3D 展厅。</p>
          </div>
          <RouterLink class="gallery-secondary-action" to="/"><OceanIcon name="home" :size="18" />返回博客</RouterLink>
        </header>
        <div v-if="gallery.characters.length" class="gallery-fallback-grid">
          <article v-for="(character, index) in gallery.characters" :key="character.id" class="gallery-fallback-item">
            <div class="gallery-fallback-poster">
              <div><small>WANTED · {{ String(index + 1).padStart(2, "0") }}</small><strong>{{ character.name }}</strong></div>
              <img v-if="posterDisplayUrl(character)" :src="posterDisplayUrl(character)" :alt="`${character.name}海报`" width="960" height="1440" loading="lazy" decoding="async" @error="handleImageError" />
            </div>
            <div class="gallery-fallback-copy">
              <h2>{{ character.name }}</h2>
              <p class="gallery-fallback-meta">{{ character.epithet }} · {{ character.faction }}</p>
              <p>{{ character.description }}</p>
              <dl><div><dt>悬赏</dt><dd>{{ character.bounty }}</dd></div><div><dt>能力</dt><dd>{{ character.ability }}</dd></div></dl>
              <blockquote>“{{ character.quote }}”</blockquote>
            </div>
          </article>
        </div>
        <div v-else class="gallery-empty-state"><h2>展厅正在布展</h2><p>人物档案启用后会在这里出现。</p></div>
      </section>

      <section v-else class="gallery-experience">
        <div ref="sceneRoot" class="gallery-scene-root"></div>

        <div class="gallery-topbar">
          <RouterLink class="gallery-exit-link" to="/">返回博客</RouterLink>
          <span>{{ gallery.settings.hall_name }}</span>
          <button v-if="entered && locked" type="button" class="gallery-pause-button" @click="pauseTour">暂停</button>
        </div>

        <div v-if="locked" class="gallery-crosshair" :class="{ active: activeCharacter }" aria-hidden="true"></div>
        <button
          v-if="locked && activeCharacter"
          type="button"
          class="gallery-active-prompt"
          @click="openCharacter(activeCharacter, activeSlot)"
        >
          <span>{{ String(activeSlot).padStart(2, "0") }}</span>
          <strong>{{ activeCharacter.name }}</strong>
          <small>查看档案</small>
        </button>

        <div v-if="!entered" class="gallery-entry-layer">
          <div class="gallery-entry-copy">
            <div v-if="gallery.settings.show_logo && gallery.settings.logo_url" class="gallery-entry-mark">
              <img :src="gallery.settings.logo_url" alt="展厅 Logo" width="512" height="512" fetchpriority="high" decoding="async" @error="handleImageError" />
            </div>
            <h1>{{ gallery.settings.hall_name }}</h1>
            <p>{{ gallery.settings.entry_title }}</p>
            <div class="gallery-entry-actions">
              <button type="button" class="gallery-primary-action" :disabled="!gallery.characters.length" @click="startTour">
                {{ gallery.characters.length ? "进入展厅" : "展厅正在布展" }}
              </button>
              <RouterLink class="gallery-secondary-action" to="/"><OceanIcon name="home" :size="18" />返回博客</RouterLink>
            </div>
            <small>{{ gallery.characters.length }} 位人物档案已开放</small>
          </div>
        </div>

        <div v-else-if="!locked && !selectedCharacter" class="gallery-entry-layer gallery-pause-layer">
          <div class="gallery-entry-copy">
            <h1>漫游已暂停</h1>
            <p>航线停在当前位置。</p>
            <div class="gallery-entry-actions">
              <button type="button" class="gallery-primary-action" @click="resumeTour">继续漫游</button>
              <RouterLink class="gallery-secondary-action" to="/">退出展厅</RouterLink>
            </div>
          </div>
        </div>
      </section>

      <dialog ref="detailDialog" class="gallery-character-dialog" @cancel="handleDialogCancel">
        <article v-if="selectedCharacter" class="gallery-character-record">
          <button type="button" class="gallery-dialog-close" @click="closeCharacter">关闭</button>
          <div class="gallery-dialog-poster">
            <div><small>WANTED</small><strong>{{ selectedCharacter.name }}</strong><span>{{ selectedCharacter.bounty }}</span></div>
            <img v-if="posterDisplayUrl(selectedCharacter)" :src="posterDisplayUrl(selectedCharacter)" :alt="`${selectedCharacter.name}海报`" width="960" height="1440" decoding="async" @error="handleImageError" />
          </div>
          <div class="gallery-dialog-copy">
            <p class="gallery-dialog-index">GRAND LINE ARCHIVE · {{ String(selectedSlot).padStart(2, "0") }}</p>
            <h2>{{ selectedCharacter.name }}</h2>
            <p class="gallery-dialog-title">{{ selectedCharacter.epithet }} · {{ selectedCharacter.faction }}</p>
            <dl>
              <div><dt>悬赏</dt><dd>{{ selectedCharacter.bounty }}</dd></div>
              <div><dt>能力</dt><dd>{{ selectedCharacter.ability }}</dd></div>
            </dl>
            <p class="gallery-dialog-description">{{ selectedCharacter.description }}</p>
            <blockquote>“{{ selectedCharacter.quote }}”</blockquote>
          </div>
        </article>
      </dialog>
    </template>
  </main>
</template>

<style scoped>
.gallery-page {
  min-height: 100vh;
  color: #07334b;
  background: #bcecff;
  font-family: "Noto Sans SC", sans-serif;
}

.gallery-experience,
.gallery-scene-root,
.gallery-status-screen {
  position: fixed;
  inset: 0;
}

.gallery-scene-root :deep(.gallery-canvas) {
  display: block;
  width: 100%;
  height: 100%;
}

.gallery-status-screen {
  z-index: 30;
  display: grid;
  place-content: center;
  justify-items: center;
  padding: 2rem;
  text-align: center;
}

.gallery-status-screen h1,
.gallery-entry-copy h1,
.gallery-fallback h1,
.gallery-character-record h2 {
  font-family: var(--display-font);
  letter-spacing: 0;
}

.gallery-status-screen h1 {
  margin: 1.4rem 0 0.5rem;
  font-size: clamp(2rem, 5vw, 4.2rem);
}

.gallery-status-screen p,
.gallery-entry-copy p {
  color: #245b70;
}

.gallery-compass-loader {
  width: 54px;
  height: 54px;
  border: 1px solid #157f9d;
  border-radius: 50%;
  animation: gallery-compass 1.4s linear infinite;
}

.gallery-compass-loader::before {
  content: "";
  display: block;
  width: 2px;
  height: 38px;
  margin: 7px auto;
  background: #f0ad45;
  transform: rotate(26deg);
}

.gallery-status-mark {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border: 1px solid #db6d4c;
  color: #c85238;
  font-size: 1.5rem;
}

.gallery-status-actions,
.gallery-entry-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.gallery-primary-action,
.gallery-secondary-action,
.gallery-exit-link,
.gallery-pause-button,
.gallery-active-prompt,
.gallery-dialog-close {
  border-radius: 4px;
  font: inherit;
  text-decoration: none;
  cursor: pointer;
}

.gallery-primary-action,
.gallery-secondary-action {
  display: inline-flex;
  gap: 0.35rem;
  align-items: center;
  justify-content: center;
  min-width: 138px;
  padding: 0.8rem 1.2rem;
  border: 1px solid #0f7898;
  font-weight: 700;
}

.gallery-primary-action {
  color: #07334b;
  background: #f7bd55;
}

.gallery-primary-action:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.gallery-secondary-action {
  color: #07334b;
  background: rgba(236, 252, 255, 0.82);
}

.gallery-topbar {
  position: fixed;
  top: 0;
  right: 0;
  left: 0;
  z-index: 8;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  min-height: 58px;
  padding: 0.65rem 1rem;
  color: #07334b;
  background: rgba(236, 252, 255, 0.78);
  border-bottom: 1px solid rgba(6, 104, 132, 0.25);
  backdrop-filter: blur(14px);
}

.gallery-topbar > span {
  font-family: var(--display-font);
  font-size: 0.92rem;
}

.gallery-exit-link,
.gallery-pause-button {
  width: fit-content;
  padding: 0.5rem 0.7rem;
  border: 1px solid rgba(6, 104, 132, 0.32);
  color: #07334b;
  background: rgba(255, 255, 255, 0.58);
}

.gallery-pause-button {
  justify-self: end;
}

.gallery-crosshair {
  position: fixed;
  top: 50%;
  left: 50%;
  z-index: 7;
  width: 10px;
  height: 10px;
  border: 1px solid rgba(3, 66, 92, 0.72);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: border-color 160ms ease, transform 160ms ease;
}

.gallery-crosshair.active {
  border-color: #e17d3f;
  transform: translate(-50%, -50%) scale(1.45);
}

.gallery-active-prompt {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  z-index: 8;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 0.7rem;
  align-items: center;
  min-width: 320px;
  padding: 0.75rem 0.9rem;
  border: 1px solid rgba(6, 104, 132, 0.4);
  color: #07334b;
  background: rgba(242, 253, 255, 0.92);
  box-shadow: 0 12px 32px rgba(4, 76, 105, 0.16);
  transform: translateX(-50%);
}

.gallery-active-prompt span,
.gallery-active-prompt small,
.gallery-dialog-index {
  color: #bc6b24;
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.7rem;
}

.gallery-entry-layer {
  position: fixed;
  inset: 0;
  z-index: 10;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  background: rgba(175, 232, 248, 0.42);
  backdrop-filter: blur(3px);
}

.gallery-entry-copy {
  width: min(760px, 100%);
  display: grid;
  justify-items: center;
  text-align: center;
}

.gallery-entry-mark {
  display: grid;
  width: 84px;
  aspect-ratio: 1;
  place-items: center;
  box-sizing: border-box;
  margin-bottom: 1.1rem;
  padding: 0.7rem;
  border: 1px solid rgba(181, 138, 81, 0.88);
  border-radius: 50%;
  background: rgba(7, 51, 75, 0.88);
  box-shadow: inset 0 0 0 4px rgba(240, 189, 85, 0.16), 0 12px 28px rgba(4, 76, 105, 0.18);
}

.gallery-entry-mark img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.gallery-entry-copy h1 {
  max-width: min(100%, 12ch);
  margin: 0;
  overflow-wrap: anywhere;
  font-size: 4.25rem;
  line-height: 1.08;
  text-wrap: balance;
}

.gallery-entry-copy p {
  max-width: 56ch;
  margin: 1rem auto 0;
  color: #164f67;
  font-size: 1.05rem;
  line-height: 1.7;
}

.gallery-entry-copy > small {
  display: block;
  margin-top: 1.25rem;
  color: #326c7f;
  font-family: "IBM Plex Mono", monospace;
}

.gallery-pause-layer {
  background: rgba(170, 227, 246, 0.58);
}

.gallery-character-dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  width: min(920px, calc(100vw - 2rem));
  max-height: calc(100dvh - 2rem);
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  overflow: auto;
  border: 1px solid rgba(10, 111, 139, 0.35);
  border-radius: 6px;
  color: #07334b;
  background: rgba(240, 252, 255, 0.97);
  box-shadow: 0 30px 90px rgba(4, 76, 105, 0.28);
  transform: translate(-50%, -50%);
}

.gallery-character-dialog::backdrop {
  background: rgba(5, 74, 102, 0.28);
}

.gallery-character-record {
  position: relative;
  display: grid;
  grid-template-columns: minmax(240px, 0.78fr) minmax(0, 1.22fr);
  min-height: 570px;
}

.gallery-dialog-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 2;
  display: grid;
  place-items: center;
  min-width: 56px;
  height: 40px;
  border: 1px solid rgba(6, 104, 132, 0.28);
  color: #07334b;
  background: rgba(220, 247, 255, 0.8);
  font-size: 0.8rem;
  font-weight: 700;
}

.gallery-dialog-poster,
.gallery-fallback-poster {
  position: relative;
  overflow: hidden;
  background: #d8c49b;
  color: #5d3c20;
}

.gallery-dialog-poster > div,
.gallery-fallback-poster > div {
  display: grid;
  position: absolute;
  inset: 0;
  z-index: 0;
  place-content: center;
  padding: 1.25rem;
  text-align: center;
}

.gallery-dialog-poster img,
.gallery-fallback-poster img {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.gallery-dialog-poster small,
.gallery-fallback-poster small {
  font: 700 0.8rem "IBM Plex Mono", monospace;
}

.gallery-dialog-poster strong,
.gallery-fallback-poster strong {
  margin-top: 0.8rem;
  font-family: var(--display-font);
  font-size: 2rem;
}

.gallery-dialog-poster span {
  margin-top: 1rem;
  font-weight: 800;
}

.gallery-dialog-copy {
  align-self: center;
  padding: 4.2rem 3.2rem 3.2rem;
}

.gallery-dialog-copy h2 {
  margin: 0.45rem 0 0;
  font-size: clamp(2.4rem, 5vw, 4.5rem);
  line-height: 1.08;
}

.gallery-dialog-title {
  margin: 0.75rem 0 0;
  color: #bb6a27;
  font-weight: 700;
}

.gallery-dialog-copy dl,
.gallery-fallback-copy dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0;
  margin: 1.5rem 0;
  border-top: 1px solid rgba(6, 104, 132, 0.2);
  border-bottom: 1px solid rgba(6, 104, 132, 0.2);
}

.gallery-dialog-copy dl div,
.gallery-fallback-copy dl div {
  padding: 0.8rem 1rem 0.8rem 0;
}

.gallery-dialog-copy dt,
.gallery-fallback-copy dt {
  color: #437488;
  font-size: 0.72rem;
}

.gallery-dialog-copy dd,
.gallery-fallback-copy dd {
  margin: 0.3rem 0 0;
  line-height: 1.45;
}

.gallery-dialog-description {
  color: #24576d;
  line-height: 1.75;
}

.gallery-dialog-copy blockquote,
.gallery-fallback-copy blockquote {
  margin: 1.5rem 0 0;
  color: #bb6a27;
  font-family: var(--display-font);
  font-size: 1.22rem;
  line-height: 1.65;
}

.gallery-fallback {
  width: min(1120px, calc(100% - 2rem));
  margin: 0 auto;
  padding: 2rem 0 4rem;
}

.gallery-fallback-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(6, 104, 132, 0.24);
}

.gallery-fallback-header h1,
.gallery-fallback-header p {
  margin: 0;
}

.gallery-fallback-header h1 {
  font-size: clamp(2rem, 8vw, 3.5rem);
}

.gallery-fallback-header p {
  margin-top: 0.6rem;
  color: #326c7f;
}

.gallery-fallback-grid {
  display: grid;
  gap: 1px;
  margin-top: 1px;
  background: rgba(6, 104, 132, 0.2);
}

.gallery-fallback-item {
  display: grid;
  grid-template-columns: minmax(160px, 0.5fr) minmax(0, 1.5fr);
  min-height: 310px;
  background: rgba(240, 252, 255, 0.96);
}

.gallery-fallback-copy {
  align-self: center;
  padding: 1.5rem;
}

.gallery-fallback-copy h2,
.gallery-fallback-copy p {
  margin-top: 0;
}

.gallery-fallback-copy h2 {
  margin-bottom: 0.35rem;
  font-family: var(--display-font);
  font-size: 2rem;
}

.gallery-fallback-meta {
  color: #bb6a27;
}

.gallery-fallback-copy > p:not(.gallery-fallback-meta) {
  color: #24576d;
  line-height: 1.65;
}

.gallery-empty-state {
  padding: 5rem 1rem;
  text-align: center;
}

button:focus-visible,
a:focus-visible {
  outline: 3px solid #f1c86e;
  outline-offset: 3px;
}

@keyframes gallery-compass {
  to { transform: rotate(360deg); }
}

@media (max-width: 720px) {
  .gallery-entry-mark {
    width: 72px;
    margin-bottom: 0.9rem;
  }

  .gallery-entry-copy h1 {
    font-size: 2.8rem;
  }

  .gallery-fallback-header,
  .gallery-fallback-item,
  .gallery-character-record {
    grid-template-columns: 1fr;
  }

  .gallery-fallback-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .gallery-fallback-poster {
    min-height: 360px;
  }

  .gallery-dialog-poster {
    min-height: 480px;
  }

  .gallery-dialog-copy {
    padding: 2rem 1.25rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .gallery-compass-loader { animation: none; }
  .gallery-crosshair { transition: none; }
}
</style>
