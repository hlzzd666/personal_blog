<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef } from "vue";
import { ArrowLeft, ArrowRight, Search, X, Maximize, Minimize, BookOpen, MoveUpRight } from "lucide-vue-next";
import { fetchGallery, type GalleryCharacter, type GalleryResponse } from "../api/gallery";
import type { GalleryScene, NavigationState } from "../gallery/GalleryScene";
import { entryChapter, museumAsset } from "../gallery/curation";
import { artifacts, logoCredit, type MuseumArtifact } from "../gallery/artifacts";
import GalleryPortrait from "../components/GalleryPortrait.vue";
import GalleryCompass from "../components/GalleryCompass.vue";

type View = "entry" | "archive" | "story" | "moments" | "tour";
const view = ref<View>("entry");
const chapter = ref(0);
const sceneRoot = ref<HTMLElement | null>(null);
const detailDialog = ref<HTMLDialogElement | null>(null);
const artifactDialog = ref<HTMLDialogElement | null>(null);
const characterCopyScroll = ref<HTMLElement | null>(null);
const gallery = shallowRef<GalleryResponse | null>(null);
const navigation = shallowRef<NavigationState | null>(null);
const loading = ref(true);
const sceneLoading = ref(false);
const error = ref("");
const notice = ref("");
const query = ref("");
const searchInput = ref<HTMLInputElement | null>(null);
const desktopSupported = ref(false);
const locked = ref(false);
const fullscreen = ref(false);
const activeCharacter = shallowRef<GalleryCharacter | null>(null);
const activeSlot = ref<number | null>(null);
const activeArtifact = shallowRef<MuseumArtifact | null>(null);
const selectedCharacter = shallowRef<GalleryCharacter | null>(null);
const selectedArtifact = shallowRef<MuseumArtifact | null>(null);
let scene: GalleryScene | null = null;
let generation = 0;
let resumeAfterDialog = false;
const characters = computed(() => gallery.value?.characters ?? []);
const currentChapters = computed(() => [entryChapter, ...(gallery.value?.chapters ?? [])]);
const currentChapter = computed(() => currentChapters.value[chapter.value] ?? currentChapters.value[0]!);
const title = computed(() => chapter.value === 0 ? (gallery.value?.settings.hall_name || currentChapter.value.heading).replace("伟大航路人物档案馆", "伟大航路\n人物档案馆") : currentChapter.value.heading || currentChapter.value.title);
const filteredCharacters = computed(() => {
  const term = query.value.trim().toLocaleLowerCase();
  const selectedChapter = currentChapters.value[chapter.value];
  const scopedCharacters = chapter.value === 0
    ? characters.value
    : characters.value.filter((character) => character.chapter_id === selectedChapter?.id);
  return scopedCharacters.filter((c) =>
    [c.name, c.epithet, c.faction, c.description, c.ability].join(" ").toLocaleLowerCase().includes(term),
  );
});
const featuredCharacter = computed(() => characters.value.find((c) => c.name.includes("路飞")) ?? characters.value[0]);
const assetSourcesUrl = `${import.meta.env.BASE_URL}gallery/artifacts/ASSET_SOURCES.md`;
const selectedSlot = computed(() => selectedCharacter.value ? characters.value.findIndex((c) => c.id === selectedCharacter.value!.id) + 1 : 0);
const selectedArtifactSlot = computed(() => {
  const index = artifacts.findIndex((item) => item.id === selectedArtifact.value?.id);
  return index >= 0 ? index + 1 : 0;
});
const ordinal = (n: number) => String(n).padStart(2, "0");
const slotOf = (character: GalleryCharacter) => characters.value.findIndex((c) => c.id === character.id) + 1;
const mapY = (z: number) => navigation.value ? 18 + (z - navigation.value.hall.minZ) / (navigation.value.hall.maxZ - navigation.value.hall.minZ) * 224 : 0;
const mapX = (x: number) => 90 + x * 11;
const markers = computed(() => (navigation.value?.markers ?? []).filter((m) => m.screenY > 18 && m.screenY < 80 && m.screenX < 80).slice(0, 4));

function supportsGallery() {
  if (innerWidth < 1024 || !matchMedia("(hover: hover) and (pointer: fine)").matches || !("pointerLockElement" in document)) return false;
  const canvas = document.createElement("canvas");
  const gl = canvas.getContext("webgl2");
  if (!gl) return false;
  gl.getExtension("WEBGL_lose_context")?.loseContext();
  return true;
}
function fallback(reason = "") {
  notice.value = reason;
  desktopSupported.value = false;
  locked.value = sceneLoading.value = false;
  activeArtifact.value = null;
  activeCharacter.value = null;
  resumeAfterDialog = false;
  scene?.dispose();
  scene = null;
  if (view.value === "tour") view.value = "archive";
}
async function loadGallery() {
  const run = ++generation;
  scene?.dispose();
  scene = null;
  loading.value = true;
  error.value = "";
  notice.value = "";
  locked.value = false;
  activeCharacter.value = null;
  activeSlot.value = null;
  activeArtifact.value = null;
  selectedCharacter.value = null;
  selectedArtifact.value = null;
  navigation.value = null;
  try {
    const data = await fetchGallery(true);
    if (run !== generation) return;
    gallery.value = { ...data, characters: data.characters.filter((c) => c.is_visible).sort((a, b) => a.sort_order - b.sort_order || a.id - b.id).slice(0, 40) };
    chapter.value = 0;
  } catch {
    if (run === generation) { loading.value = false; error.value = "人物档案暂时无法读取，请重试。"; }
    return;
  }
  loading.value = false;
  desktopSupported.value = supportsGallery();
  if (!desktopSupported.value) return;
  sceneLoading.value = true;
  await nextTick();
  if (run !== generation || !sceneRoot.value) return;
  try {
    const { GalleryScene: Scene } = await import("../gallery/GalleryScene");
    if (run !== generation || !sceneRoot.value) return;
    const current = new Scene(sceneRoot.value, characters.value, matchMedia("(prefers-reduced-motion: reduce)").matches, {
      onActiveCharacter(character, slot) { activeCharacter.value = character; activeSlot.value = slot; },
      onActiveArtifact(artifact) { activeArtifact.value = artifact; },
      onLockChange(value) { locked.value = value; },
      onOpenCharacter: openCharacter,
      onOpenArtifact: openArtifact,
      onNavigation(state) { navigation.value = state; },
      onUnavailable: fallback,
    });
    scene = current;
    current.setRunning(false);
    await current.ready;
    if (run !== generation) { current.dispose(); return; }
    sceneLoading.value = false;
  } catch {
    if (run === generation) fallback("实时展舱暂时无法开启，仍可阅读图志和人物档案。");
  }
}
function navigate(next: View) {
  if (next !== "tour") { scene?.unlock(); scene?.setRunning(false); }
  view.value = next;
  window.scrollTo({ top: 0, behavior: "instant" });
}
function showArchive() {
  chapter.value = 0;
  query.value = "";
  navigate("archive");
}
function searchArchive() {
  showArchive();
  void nextTick(() => searchInput.value?.focus());
}
function selectChapter(index: number) {
  chapter.value = index;
  query.value = "";
}
function startTour() {
  if (!desktopSupported.value || !scene) { showArchive(); return; }
  if (sceneLoading.value) return;
  view.value = "tour";
  scene.setRunning(true);
  scene.lock();
}
function toggleTour() { if (locked.value) scene?.unlock(); else scene?.lock(); }
function openCharacter(character: GalleryCharacter) {
  resumeAfterDialog = locked.value;
  artifactDialog.value?.close();
  selectedArtifact.value = null;
  selectedCharacter.value = character;
  scene?.unlock();
  void nextTick(() => {
    characterCopyScroll.value?.scrollTo({ top: 0 });
    detailDialog.value?.showModal();
  });
}
function closeCharacter() {
  detailDialog.value?.close();
  selectedCharacter.value = null;
  if (resumeAfterDialog && view.value === "tour") scene?.lock();
  resumeAfterDialog = false;
}
function openArtifact(artifact: MuseumArtifact) {
  resumeAfterDialog = locked.value;
  detailDialog.value?.close();
  selectedCharacter.value = null;
  selectedArtifact.value = artifact;
  scene?.unlock();
  void nextTick(() => artifactDialog.value?.showModal());
}
function closeArtifact() {
  artifactDialog.value?.close();
  selectedArtifact.value = null;
  if (resumeAfterDialog && view.value === "tour") scene?.lock();
  resumeAfterDialog = false;
}
function openActiveDisplay() {
  if (activeArtifact.value) openArtifact(activeArtifact.value);
  else if (activeCharacter.value) openCharacter(activeCharacter.value);
}
function adjacentCharacter(delta: number) {
  const index = characters.value.findIndex((c) => c.id === selectedCharacter.value?.id);
  const character = characters.value[(index + delta + characters.value.length) % characters.value.length];
  if (character) {
    selectedCharacter.value = character;
    void nextTick(() => characterCopyScroll.value?.scrollTo({ top: 0 }));
  }
}
async function toggleFullscreen() {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await document.documentElement.requestFullscreen();
  } catch { notice.value = "当前浏览器未允许全屏，可继续窗口参观。"; }
}
const updateFullscreen = () => { fullscreen.value = !!document.fullscreenElement; };
function resizeDevice() { if (innerWidth < 1024 && scene) fallback(); }
onMounted(() => {
  void loadGallery();
  window.addEventListener("resize", resizeDevice);
  document.addEventListener("fullscreenchange", updateFullscreen);
});
onBeforeUnmount(() => {
  generation++;
  scene?.dispose();
  window.removeEventListener("resize", resizeDevice);
  document.removeEventListener("fullscreenchange", updateFullscreen);
});
</script>

<template>
  <main class="gallery-page" :class="'view-' + view">
    <div v-if="desktopSupported" ref="sceneRoot" class="gallery-scene-root" :class="{ 'scene-visible': view === 'tour' }" :aria-hidden="view !== 'tour'"></div>

    <header class="gallery-topbar">
      <nav class="museum-navigation" aria-label="展馆导航">
        <button :class="{ active: view === 'entry' }" :aria-current="view === 'entry' ? 'page' : undefined" @click="navigate('entry')">首页</button>
        <button :class="{ active: view === 'archive' }" :aria-current="view === 'archive' ? 'page' : undefined" @click="showArchive">人物档案</button>
        <button :class="{ active: view === 'story' }" :aria-current="view === 'story' ? 'page' : undefined" @click="navigate('story')">航海图志</button>
        <button :class="{ active: view === 'moments' }" :aria-current="view === 'moments' ? 'page' : undefined" @click="navigate('moments')">经典时刻</button>
        <RouterLink to="/about">关于本站</RouterLink>
      </nav>
      <button class="header-search" aria-label="搜索人物档案" @click="searchArchive"><Search :size="18" /><span>搜索角色、篇章或关键词…</span></button>
      <p class="header-motto">为每一个热爱的灵魂，留下一段航海的证明。</p>
      <RouterLink class="header-exit" to="/" aria-label="返回航海日志"><ArrowLeft :size="17" /></RouterLink>
    </header>

    <section v-show="view === 'entry'" class="museum-entry" aria-label="展馆序厅">
      <div class="entry-stage">
        <div :key="chapter" class="entry-copy">
          <h1>{{ title }}</h1>
          <p class="entry-intro">{{ currentChapter.description }}</p>
          <p class="entry-note">{{ currentChapter.note }}</p>
          <button class="brass-button" :disabled="loading || (chapter === 0 && desktopSupported && sceneLoading)" @click="chapter === 0 ? startTour() : navigate('story')">
            <i aria-hidden="true"></i>{{ loading ? '正在开馆' : chapter > 0 ? '阅读本章' : sceneLoading ? '展舱准备中' : '开始参观' }}<ArrowRight :size="22" /><i aria-hidden="true"></i>
          </button>
          <button class="entry-archive-link" @click="showArchive">浏览全部人物档案 <MoveUpRight :size="13" /></button>
          <p v-if="error" class="entry-message" role="alert">{{ error }} <button @click="loadGallery">重新读取</button></p>
          <p v-else-if="notice" class="entry-message" role="status">{{ notice }}</p>
        </div>
        <div class="entry-visual">
          <div class="entry-image">
            <img v-show="chapter === 0" class="cabin-backdrop" :src="museumAsset('collection-interior.webp')" alt="深海色典藏舱中，草帽、和道一文字、橡胶果实与梅利号围绕 ONE PIECE 徽标陈列" fetchpriority="high" />
            <div v-if="chapter > 0" class="chapter-backdrop chapter-art" :class="'chapter-art-' + currentChapter.artwork_index" role="img" :aria-label="currentChapter.title + '航路插画'"></div>
          </div>
          <div class="entry-visual-caption">
            <button v-if="chapter === 0 && featuredCharacter" class="featured-label" @click="openCharacter(featuredCharacter)">
              <strong>{{ featuredCharacter.name }}</strong><span>{{ featuredCharacter.quote || '走进人物的故事，重访大海上的梦想。' }}</span><ArrowRight :size="16" />
            </button>
            <span v-else class="entry-chapter-caption">{{ currentChapter.subtitle }}</span>
            <div class="entry-tools">
              <span>{{ chapter === 0 ? '常设展 · 人物典藏' : currentChapter.title }}</span>
              <button :aria-label="fullscreen ? '退出全屏' : '全屏欣赏'" @click="toggleFullscreen"><Minimize v-if="fullscreen" :size="17" /><Maximize v-else :size="17" /></button>
            </div>
          </div>
        </div>
      </div>
      <footer class="exhibition-dock">
        <ol class="archive-rail" aria-label="展馆章节">
          <li v-for="(item, index) in currentChapters" :key="item.id">
            <button :class="{ active: chapter === index }" :aria-pressed="chapter === index" @click="selectChapter(index)">
              <span class="chapter-art" :class="'chapter-art-' + item.artwork_index"></span>
              <span class="chapter-number">{{ ordinal(index + 1) }}</span>
              <span class="chapter-heading"><strong>{{ item.title }}</strong><small>{{ index === 0 ? '馆藏序章' : item.label }}</small></span>
              <span class="chapter-caption">{{ item.subtitle }}</span>
            </button>
          </li>
        </ol>
        <div class="dock-compass">
          <GalleryCompass :heading="chapter * 45" />
          <div><small>当前方位</small><strong>{{ currentChapter.title }}</strong><i></i><span>第 {{ ordinal(chapter + 1) }} 章 / 共 {{ ordinal(currentChapters.length) }} 章</span><p>伟大的航路，永不止步。</p></div>
        </div>
      </footer>
    </section>

    <section v-if="view === 'archive'" class="gallery-fallback">
      <div class="collection-heading"><button class="quiet-button" @click="navigate('entry')"><ArrowLeft :size="16" />返回序厅</button><span>THE COLLECTION · {{ ordinal(characters.length) }} RECORDS</span></div>
      <header class="fallback-header"><div><h1>人物档案</h1><p>他们的名字，构成了一个时代的航海史。</p></div><div class="collection-count"><strong>{{ ordinal(characters.length) }}</strong><span>人物档案 / 现正展出</span></div></header>
      <div class="archive-controls">
        <nav aria-label="档案章节筛选"><button v-for="(item, index) in currentChapters" :key="item.id" :class="{ active: chapter === index }" :aria-pressed="chapter === index" @click="selectChapter(index)">{{ index === 0 ? '全部馆藏' : item.title }}</button></nav>
        <label class="archive-search"><Search :size="17" /><input ref="searchInput" v-model="query" type="search" placeholder="姓名、称号、能力…" aria-label="检索馆藏" /><span>{{ filteredCharacters.length }} 件</span></label>
      </div>
      <p v-if="loading" role="status" class="empty-state">正在读取馆藏…</p>
      <div v-else-if="error" class="empty-state" role="alert"><p>{{ error }}</p><button class="quiet-button" @click="loadGallery">重新读取</button></div>
      <p v-if="notice" class="gallery-notice" role="status">{{ notice }}</p>
      <div v-if="filteredCharacters.length" class="fallback-grid">
        <article v-for="character in filteredCharacters" :key="character.id" class="fallback-item">
          <button class="poster-button" :aria-label="'查看' + character.name + '档案'" @click="openCharacter(character)"><GalleryPortrait :record-number="slotOf(character)" :character="character" /></button>
          <div class="fallback-copy"><small>GL · {{ String(slotOf(character)).padStart(3, '0') }}</small><h2>{{ character.name }}</h2><p>{{ character.epithet }} · {{ character.faction }}</p><button class="text-button" @click="openCharacter(character)">查看档案<ArrowRight :size="16" /></button></div>
        </article>
      </div>
      <div v-else-if="!loading && !error" class="empty-state"><BookOpen :size="32" /><h2>{{ query ? '没有找到这份档案' : '这一章正在布展' }}</h2><p>{{ query ? '试试人物姓名、称号或能力关键词。' : '可以先在全部馆藏中继续参观。' }}</p><button class="quiet-button" @click="showArchive">查看全部馆藏</button></div>
      <p class="collection-footnote">馆藏资料由本站整理维护 · 默认人物插画为 AI 生成同人作品</p>
      <section class="artifact-catalog" aria-labelledby="artifact-catalog-title">
        <h2 id="artifact-catalog-title">道具典藏</h2>
        <p>从一顶草帽到一艘船，重访航程中的信物。</p>
        <ul><li v-for="artifact in artifacts" :key="artifact.id"><button @click="openArtifact(artifact)"><span><strong>{{ artifact.title }}</strong><small>{{ artifact.subtitle }}</small></span><ArrowRight :size="18" /></button></li></ul>
      </section>
      <aside class="gallery-asset-credits" aria-label="展馆素材来源">
        <p>展馆标识：<a :href="logoCredit.modelUrl" target="_blank" rel="noreferrer">{{ logoCredit.title }}</a>，作者 <a :href="logoCredit.authorUrl" target="_blank" rel="noreferrer">{{ logoCredit.author }}</a> · <a :href="logoCredit.licenseUrl" target="_blank" rel="noreferrer">{{ logoCredit.license }}</a>。{{ logoCredit.changes }}</p>
        <p>道具模型署名、许可与修改说明：<a :href="assetSourcesUrl" target="_blank" rel="noreferrer">完整素材来源与处理记录</a></p>
      </aside>
    </section>

    <section v-if="view === 'story' || view === 'moments'" class="editorial-page">
      <div class="collection-heading"><button class="quiet-button" @click="navigate('entry')"><ArrowLeft :size="16" />返回序厅</button><span>{{ view === 'story' ? 'THE VOYAGE' : 'VOICES OF THE SEA' }}</span></div>
      <header class="editorial-heading"><h1>{{ view === 'story' ? '航海图志' : '经典时刻' }}</h1><p>{{ view === 'story' ? '把相遇写进航线，把梦想留给大海。' : '一句话，记住一个人；一个约定，驶过整片海。' }}</p></header>
      <template v-if="view === 'story'">
        <nav class="story-tabs" aria-label="阅读章节"><button v-for="(item, index) in currentChapters" :key="item.id" :aria-pressed="chapter === index" :class="{ active: chapter === index }" @click="selectChapter(index)">{{ ordinal(index + 1) }} <span>{{ item.title }}</span></button></nav>
        <article :key="chapter" class="chapter-spread"><div class="chapter-landscape chapter-art" :class="'chapter-art-' + currentChapter.artwork_index" role="img" :aria-label="currentChapter.title + '航路插画'"></div><div class="chapter-essay"><h2>{{ currentChapter.title }}</h2><p>{{ currentChapter.story || '本章故事正在整理，可以先查阅人物档案。' }}</p><button class="text-button" @click="navigate('archive')">查阅本章人物<ArrowRight :size="17" /></button></div></article>
      </template>
      <div v-else class="moments-list"><article v-for="character in characters.filter(c => c.quote.trim())" :key="character.id"><button class="moment-portrait" :aria-label="'查看' + character.name + '档案'" @click="openCharacter(character)"><GalleryPortrait :record-number="slotOf(character)" :character="character" /></button><div><span>GL · {{ String(slotOf(character)).padStart(3, '0') }}</span><blockquote>“{{ character.quote }}”</blockquote><button @click="openCharacter(character)">{{ character.name }}<ArrowRight :size="18" /></button></div></article><p v-if="!characters.some(c => c.quote.trim())" class="empty-state">馆藏语录正在整理，稍后再来看看。</p></div>
    </section>

    <section v-if="view === 'tour'" class="tour-interface" aria-label="实时船长舱漫游">
      <div v-if="!locked && !selectedCharacter && !selectedArtifact" class="pause-layer"><div><span>THE CAPTAIN'S CABIN</span><h1>在这里，继续航行。</h1><p>WASD / 方向键移动 · 鼠标观察<br />靠近画像或展品后，按 E 或点击查看展签 / 档案 · Esc 暂停</p><div class="gallery-actions"><button class="brass-button" @click="toggleTour">继续漫游<ArrowRight :size="20" /></button><button class="quiet-button" @click="navigate('entry')">返回序厅</button></div></div></div>
      <div class="tour-readout"><span>实时漫游 · {{ navigation?.zone || '船长舱' }}</span><strong>{{ activeArtifact?.title || activeCharacter?.name || '循着光，走进他们的故事。' }}</strong><small>WASD 移动 · E 查看展签 / 档案 · Esc 暂停</small></div>
      <aside v-if="navigation" class="gallery-minimap" aria-label="船舱航图"><div class="map-title"><strong>船舱航图</strong><span>{{ ordinal(characters.length) }} 位</span></div><svg viewBox="0 0 180 260" role="img" aria-label="当前所在位置与展位"><path d="M35 18H145V242H35Z" fill="#c9a55c0a" stroke="#b99a60" stroke-width="1" /><path d="M90 24V235" stroke="#b99a6050" stroke-dasharray="2 5" /><rect v-for="artifact in artifacts" :key="artifact.id" :x="mapX(artifact.x) - 2.5" :y="mapY(artifact.z) - 2.5" width="5" height="5" :fill="activeArtifact?.id === artifact.id ? '#f3d392' : '#bfa16e'" /><circle v-for="marker in navigation.markers" :key="marker.slot" :cx="mapX(marker.x)" :cy="mapY(marker.z)" r="3" :fill="marker.near ? '#f3d392' : '#948165'" /><g :transform="'translate(' + mapX(navigation.x) + ',' + mapY(navigation.z) + ') rotate(' + navigation.heading * 180 / Math.PI + ')'"><path d="M0 -8L5 5L0 2L-5 5Z" fill="#f5dca1" /></g><text x="90" y="11" fill="#c4ae88" text-anchor="middle" font-size="8">道具典藏舱</text><text x="90" y="255" fill="#c4ae88" text-anchor="middle" font-size="8">人物长廊</text></svg></aside>
      <template v-if="locked"><div class="gallery-crosshair" :class="{ active: activeCharacter || activeArtifact }" aria-hidden="true"></div><div v-for="marker in markers" :key="marker.slot" class="gallery-nav-marker" :style="{ left: marker.screenX + '%', top: marker.screenY + '%' }" aria-hidden="true"><b>{{ ordinal(marker.slot) }}</b><span>{{ marker.distance }} m</span></div><button v-if="activeCharacter || activeArtifact" class="gallery-active-prompt" @click="openActiveDisplay"><span>{{ activeArtifact ? 'EX' : ordinal(activeSlot || 0) }}</span><strong>{{ activeArtifact?.title || activeCharacter?.name }}</strong><span>E 查看{{ activeArtifact ? '展签' : '档案' }}</span><ArrowRight :size="18" /></button></template>
    </section>

    <dialog ref="detailDialog" class="gallery-character-dialog" aria-labelledby="character-title" @cancel.prevent="closeCharacter" @click="event => event.target === event.currentTarget && closeCharacter()">
      <article v-if="selectedCharacter" class="character-record">
        <button class="dialog-close" aria-label="关闭" autofocus @click="closeCharacter"><X :size="20" /></button>
        <div class="dialog-poster"><GalleryPortrait :record-number="selectedSlot" :character="selectedCharacter" /><span>GRAND LINE · COLLECTION</span></div>
        <div class="dialog-copy character-copy"><div ref="characterCopyScroll" class="character-copy-scroll"><span class="record-code">人物档案 / GL · {{ String(selectedSlot).padStart(3, '0') }}</span><h2 id="character-title">{{ selectedCharacter.name }}</h2><p class="character-meta">{{ selectedCharacter.epithet }} · {{ selectedCharacter.faction }}</p><dl><div><dt>悬赏记录</dt><dd>{{ selectedCharacter.bounty || '暂无记录' }}</dd></div><div><dt>能力档案</dt><dd>{{ selectedCharacter.ability || '暂无记录' }}</dd></div></dl><p class="character-description">{{ selectedCharacter.description || '人物履历正在整理。' }}</p><blockquote v-if="selectedCharacter.quote">“{{ selectedCharacter.quote }}”</blockquote></div><nav v-if="characters.length > 1" class="record-pagination" aria-label="前后人物"><button @click="adjacentCharacter(-1)"><ArrowLeft :size="16" />上一份</button><span>{{ ordinal(selectedSlot) }} / {{ ordinal(characters.length) }}</span><button @click="adjacentCharacter(1)">下一份<ArrowRight :size="16" /></button></nav></div>
      </article>
    </dialog>

    <dialog ref="artifactDialog" class="gallery-character-dialog gallery-artifact-dialog" aria-labelledby="artifact-title" @cancel.prevent="closeArtifact" @click="event => event.target === event.currentTarget && closeArtifact()">
      <article v-if="selectedArtifact" class="artifact-record">
        <button class="dialog-close" aria-label="关闭" autofocus @click="closeArtifact"><X :size="20" /></button>
        <div class="dialog-copy artifact-copy">
          <header>
            <h2 id="artifact-title">{{ selectedArtifact.title }}</h2>
            <p class="artifact-subtitle">{{ selectedArtifact.subtitle }}</p>
          </header>
          <p class="character-description">{{ selectedArtifact.description }}</p>
          <section class="artifact-features" aria-labelledby="artifact-features-title">
            <h3 id="artifact-features-title">展品看点</h3>
            <ul><li v-for="feature in selectedArtifact.features" :key="feature">{{ feature }}</li></ul>
          </section>
          <footer class="artifact-footer"><span class="record-code">典藏展签 · {{ ordinal(selectedArtifactSlot) }} / {{ ordinal(artifacts.length) }}</span></footer>
        </div>
      </article>
    </dialog>
  </main>
</template>

<style scoped src="../gallery/gallery-page.css"></style>
