<script setup lang="ts">
import DOMPurify from "dompurify";
import { marked } from "marked";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { fetchArticle, likeArticle, type Article } from "../api/articles";

type TocItem = { id: string; level: number; text: string };

const route = useRoute();
const article = ref<Article | null>(null);
const articleContent = ref("");
const articleToc = ref<TocItem[]>([]);
const contentRoot = ref<HTMLElement | null>(null);
const readingRegion = ref<HTMLElement | null>(null);
const documentScrollTrack = ref<HTMLElement | null>(null);
const loading = ref(true);
const errorText = ref("");
const liking = ref(false);
const likeError = ref("");
const likedRecently = ref(false);
const readingProgress = ref(0);
const activeHeadingId = ref("");
const documentIsScrollable = ref(false);
const documentScrollThumbSize = ref(1);
const pageScrollProgress = ref(0);

let scrollFrame: number | undefined;
let revealObserver: IntersectionObserver | undefined;
let likeTimer: number | undefined;
let loadVersion = 0;
let documentScrollbarDragOffset = 0;

const articleNumber = computed(() => String(article.value?.id ?? 0).padStart(4, "0"));
const readingPercent = computed(() => Math.round(readingProgress.value * 100));
const readingProgressStyle = computed(() => ({ "--reading-progress": `${readingProgress.value * 360}deg` }));
const documentScrollThumbStyle = computed(() => {
  const size = Math.max(documentScrollThumbSize.value, 0.08);
  return {
    height: `${size * 100}%`,
    top: `${pageScrollProgress.value * (1 - size) * 100}%`,
  };
});
const heroStyle = computed(() => {
  if (!article.value?.cover_image_url) return undefined;
  return { "--article-cover": `url("${article.value.cover_image_url.replace(/"/g, "%22")}")` };
});
const readingMinutes = computed(() => {
  if (!article.value) return 1;
  const text = normalizeMarkdown(article.value.content_markdown)
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/[#>*_`()!-]/g, " ");
  const chineseCharacters = text.match(/[\u3400-\u9fff]/g)?.length ?? 0;
  const words = text.match(/[A-Za-z0-9]+/g)?.length ?? 0;
  return Math.max(1, Math.ceil((chineseCharacters + words * 1.6) / 420));
});

function normalizeMarkdown(value: string) {
  return !value.includes("\n") && value.includes("\\n") ? value.replace(/\\n/g, "\n") : value;
}

function buildArticleContent(markdown: string) {
  const rawHtml = marked.parse(normalizeMarkdown(markdown)) as string;
  const safeDocument = new DOMParser().parseFromString(DOMPurify.sanitize(rawHtml), "text/html");
  const headings = Array.from(safeDocument.body.querySelectorAll("h2, h3"));

  articleToc.value = headings.map((heading, index) => {
    const id = `section-${String(index + 1).padStart(2, "0")}`;
    heading.id = id;
    return { id, level: Number(heading.tagName.slice(1)), text: heading.textContent?.trim() || `章节 ${index + 1}` };
  });
  safeDocument.body.querySelectorAll("a[href]").forEach((link) => {
    if (/^https?:\/\//i.test(link.getAttribute("href") ?? "")) {
      link.setAttribute("target", "_blank");
      link.setAttribute("rel", "noreferrer noopener");
    }
  });
  safeDocument.body.querySelectorAll("img").forEach((image) => {
    image.setAttribute("loading", "lazy");
    image.setAttribute("decoding", "async");
  });
  articleContent.value = safeDocument.body.innerHTML;
  activeHeadingId.value = articleToc.value[0]?.id ?? "";
}

function formatDate(value: string | null) {
  if (!value) return "时间待定";
  return new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "long", day: "numeric" }).format(new Date(value));
}

function formatDateTime(value: string | null) {
  if (!value) return "时间待定";
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

function setupContentReveal() {
  revealObserver?.disconnect();
  const root = contentRoot.value;
  if (!root) return;
  const blocks = Array.from(root.children) as HTMLElement[];
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    blocks.forEach((block) => block.classList.add("is-visible"));
    return;
  }
  root.classList.add("motion-ready");
  blocks.forEach((block, index) => block.style.setProperty("--reveal-delay", `${Math.min(index, 5) * 45}ms`));
  revealObserver = new IntersectionObserver(
    (entries) => entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      revealObserver?.unobserve(entry.target);
    }),
    { rootMargin: "0px 0px -8%", threshold: 0.08 },
  );
  blocks.forEach((block) => revealObserver?.observe(block));
}

function updateReadingState() {
  if (scrollFrame !== undefined) return;
  scrollFrame = window.requestAnimationFrame(() => {
    const pageDistance = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
    documentIsScrollable.value = document.documentElement.scrollHeight > window.innerHeight;
    documentScrollThumbSize.value = window.innerHeight / document.documentElement.scrollHeight;
    pageScrollProgress.value = Math.min(Math.max(window.scrollY / pageDistance, 0), 1);
    const region = readingRegion.value;
    if (region) {
      const start = region.offsetTop - window.innerHeight * 0.32;
      const distance = Math.max(region.offsetHeight - window.innerHeight * 0.55, 1);
      readingProgress.value = Math.min(Math.max((window.scrollY - start) / distance, 0), 1);
    }
    if (articleToc.value.length) {
      let currentId = articleToc.value[0]?.id ?? "";
      const currentLine = window.innerHeight * 0.28;
      articleToc.value.forEach((item) => {
        const heading = document.getElementById(item.id);
        if (heading && heading.getBoundingClientRect().top <= currentLine) currentId = item.id;
      });
      activeHeadingId.value = currentId;
    }
    scrollFrame = undefined;
  });
}

function scrollToHeading(id: string) {
  const heading = document.getElementById(id);
  if (!heading) return;
  heading.scrollIntoView({ behavior: "smooth", block: "start" });
}

function scrollDocumentToTrackPosition(clientY: number, thumbOffset: number) {
  const track = documentScrollTrack.value;
  if (!track || !documentIsScrollable.value) return;
  const trackBounds = track.getBoundingClientRect();
  const thumb = track.querySelector<HTMLElement>(".document-scrollbar-thumb");
  if (!thumb) return;
  const thumbHeight = thumb.getBoundingClientRect().height;
  const travel = Math.max(trackBounds.height - thumbHeight, 1);
  const position = Math.min(Math.max((clientY - trackBounds.top - thumbOffset) / travel, 0), 1);
  window.scrollTo({ top: position * (document.documentElement.scrollHeight - window.innerHeight), behavior: "auto" });
}

function handleDocumentScrollbarPointerDown(event: PointerEvent) {
  const track = documentScrollTrack.value;
  if (!track || !documentIsScrollable.value) return;
  event.preventDefault();
  const thumb = track.querySelector<HTMLElement>(".document-scrollbar-thumb");
  if (!thumb) return;
  const thumbBounds = thumb.getBoundingClientRect();
  const pressedThumb = (event.target as HTMLElement).closest(".document-scrollbar-thumb") !== null;
  documentScrollbarDragOffset = pressedThumb ? event.clientY - thumbBounds.top : thumbBounds.height / 2;
  scrollDocumentToTrackPosition(event.clientY, documentScrollbarDragOffset);
  window.addEventListener("pointermove", handleDocumentScrollbarPointerMove);
  window.addEventListener("pointerup", handleDocumentScrollbarPointerUp, { once: true });
}

function handleDocumentScrollbarPointerMove(event: PointerEvent) {
  scrollDocumentToTrackPosition(event.clientY, documentScrollbarDragOffset);
}

function handleDocumentScrollbarPointerUp() {
  window.removeEventListener("pointermove", handleDocumentScrollbarPointerMove);
  documentScrollbarDragOffset = 0;
}

function handleDocumentScrollbarKeydown(event: KeyboardEvent) {
  if (!documentIsScrollable.value) return;
  const scrollDirections: Record<string, number> = {
    ArrowDown: 0.12,
    ArrowRight: 0.12,
    ArrowUp: -0.12,
    ArrowLeft: -0.12,
    PageDown: 0.86,
    PageUp: -0.86,
  };
  if (event.key === "Home" || event.key === "End") {
    event.preventDefault();
    window.scrollTo({ top: event.key === "Home" ? 0 : document.documentElement.scrollHeight, behavior: "smooth" });
    return;
  }
  if (scrollDirections[event.key] === undefined) return;
  event.preventDefault();
  window.scrollBy({ top: window.innerHeight * scrollDirections[event.key], behavior: "smooth" });
}

async function loadArticle() {
  const currentLoad = ++loadVersion;
  loading.value = true;
  errorText.value = "";
  article.value = null;
  articleContent.value = "";
  articleToc.value = [];
  readingProgress.value = 0;
  revealObserver?.disconnect();
  try {
    const result = await fetchArticle(String(route.params.slug));
    if (currentLoad !== loadVersion) return;
    article.value = result;
    buildArticleContent(result.content_markdown);
    await nextTick();
    updateReadingState();
    await nextTick();
    setupContentReveal();
  } catch {
    if (currentLoad === loadVersion) errorText.value = "这段航行记录不存在，或已经离开当前航线。";
  } finally {
    if (currentLoad === loadVersion) loading.value = false;
  }
}

async function handleLike() {
  if (!article.value || liking.value || article.value.liked_by_current_visitor) return;
  liking.value = true;
  likeError.value = "";
  try {
    const result = await likeArticle(article.value.slug);
    article.value.likes = result.likes;
    article.value.liked_by_current_visitor = result.liked_by_current_visitor;
    likedRecently.value = true;
    window.clearTimeout(likeTimer);
    likeTimer = window.setTimeout(() => { likedRecently.value = false; }, 900);
  } catch {
    likeError.value = "点赞未送达，请稍后再试。";
  } finally {
    liking.value = false;
  }
}

watch(() => route.params.slug, loadArticle, { immediate: true });

onMounted(() => {
  window.addEventListener("scroll", updateReadingState, { passive: true });
  window.addEventListener("resize", updateReadingState, { passive: true });
});

onBeforeUnmount(() => {
  window.removeEventListener("scroll", updateReadingState);
  window.removeEventListener("resize", updateReadingState);
  window.removeEventListener("pointermove", handleDocumentScrollbarPointerMove);
  if (scrollFrame !== undefined) window.cancelAnimationFrame(scrollFrame);
  window.clearTimeout(likeTimer);
  revealObserver?.disconnect();
});
</script>

<template>
  <div class="article-detail-page" :style="readingProgressStyle">
    <div class="reading-progress" aria-hidden="true"><span></span></div>
    <div class="article-chart" aria-hidden="true">
      <span class="chart-orbit chart-orbit-one"></span>
      <span class="chart-orbit chart-orbit-two"></span>
      <svg class="chart-route" viewBox="0 0 1440 720" preserveAspectRatio="none">
        <path class="chart-route-base" d="M-80 530 C 210 390, 320 650, 610 430 S 1010 130, 1510 310" />
        <path class="chart-route-flow" d="M-80 530 C 210 390, 320 650, 610 430 S 1010 130, 1510 310" />
      </svg>
    </div>

    <template v-if="article">
      <header :class="['article-hero', { 'has-cover': article.cover_image_url }]" :style="heroStyle">
        <div class="hero-shade" aria-hidden="true"></div>
        <div class="article-hero-inner">
          <RouterLink class="article-back-link" :to="{ path: '/articles', query: { view: 'archive' } }">
            <span aria-hidden="true">←</span> 返回文章归档
          </RouterLink>
          <div class="hero-heading">
            <p class="article-kicker"><span>LOGBOOK / {{ article.category }}</span><span>{{ formatDate(article.published_at) }}</span></p>
            <h1>{{ article.title }}</h1>
            <p class="article-summary">{{ article.summary }}</p>
          </div>
          <div class="article-manifest" aria-label="文章信息">
            <div><span>记录编号</span><strong>NO. {{ articleNumber }}</strong></div>
            <div><span>执笔</span><strong>{{ article.author }}</strong></div>
            <div><span>阅读时间</span><strong>{{ readingMinutes }} 分钟</strong></div>
            <div><span>浏览</span><strong>{{ article.views }}</strong></div>
          </div>
        </div>
        <div class="hero-depth" aria-hidden="true"><span>DEPTH 042</span><i></i><span>COURSE 118</span></div>
      </header>

      <main ref="readingRegion" class="article-reading-layout">
        <aside class="reading-rail" aria-label="阅读导航">
          <div class="reading-rail-sticky">
            <div class="reading-gauge" :aria-label="`阅读进度 ${readingPercent}%`" role="progressbar" aria-valuemin="0" aria-valuemax="100" :aria-valuenow="readingPercent">
              <div class="reading-gauge-ring"><span>{{ readingPercent }}</span><small>%</small></div>
              <p>READING<br />POSITION</p>
            </div>
            <nav v-if="articleToc.length" class="article-toc" aria-label="文章目录">
              <p>航线节点</p>
              <div class="article-toc-list">
                <button v-for="(item, index) in articleToc" :key="item.id" :class="[{ active: item.id === activeHeadingId }, `level-${item.level}`]" type="button" @click="scrollToHeading(item.id)">
                  <span>{{ String(index + 1).padStart(2, "0") }}</span>{{ item.text }}
                </button>
              </div>
            </nav>
            <div v-else class="article-toc-empty"><span></span>单程航线</div>
          </div>
        </aside>

        <article id="article-content" class="article-document">
          <div class="document-header">
            <p>FIELD NOTES</p>
            <div><span>{{ article.is_repost ? "转载记录" : "原创记录" }}</span><span>最后校准 {{ formatDateTime(article.updated_at) }}</span></div>
          </div>
          <img v-if="article.cover_image_url" class="article-detail-cover" :src="article.cover_image_url" :alt="article.title" />
          <!-- 内容已由 DOMPurify 清洗后再插入，保留 Markdown 的排版能力。 -->
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div ref="contentRoot" class="markdown-body" v-html="articleContent"></div>
          <p v-if="article.is_repost && article.source_url" class="article-source">本文转载自 <a :href="article.source_url" target="_blank" rel="noreferrer noopener">原始来源</a></p>
          <footer class="article-detail-footer">
            <div class="article-detail-tags"><span v-for="tag in article.tags" :key="tag"># {{ tag }}</span></div>
            <div class="article-like-area">
              <button :class="['article-like-button', { celebrated: likedRecently, 'is-liked': article.liked_by_current_visitor }]" type="button" :disabled="liking || article.liked_by_current_visitor" @click="handleLike">
                <span class="like-symbol" aria-hidden="true">♥</span><span>{{ article.liked_by_current_visitor ? "已点赞" : liking ? "正在送达" : "点赞" }}</span><strong>{{ article.likes }}</strong>
              </button>
              <small v-if="likeError" role="status">{{ likeError }}</small>
            </div>
          </footer>
          <div class="document-end" aria-hidden="true"><i></i><span>END OF ENTRY / {{ articleNumber }}</span><i></i></div>
        </article>
        <div
          v-if="documentIsScrollable"
          ref="documentScrollTrack"
          class="document-scrollbar"
          role="slider"
          tabindex="0"
          aria-label="文章快速滚动"
          aria-controls="article-content"
          aria-valuemin="0"
          aria-valuemax="100"
          :aria-valuenow="readingPercent"
          :aria-valuetext="`阅读进度 ${readingPercent}%`"
          @keydown="handleDocumentScrollbarKeydown"
          @pointerdown="handleDocumentScrollbarPointerDown"
        >
          <span class="document-scrollbar-thumb" :style="documentScrollThumbStyle"></span>
        </div>
      </main>
    </template>

    <div v-else-if="loading" class="article-detail-state" aria-live="polite">
      <span class="state-radar" aria-hidden="true"></span><p>正在读取航行记录</p><small>LOG SIGNAL CONNECTING</small>
    </div>
    <div v-else class="article-detail-state article-detail-error">
      <p>{{ errorText }}</p><RouterLink :to="{ path: '/articles', query: { view: 'archive' } }">返回文章归档</RouterLink>
    </div>
  </div>
</template>

<style scoped lang="scss">
.article-detail-page {
  --ink: #f4f0df;
  --muted: rgba(226, 235, 224, 0.62);
  --deep-sea: #051923;
  --signal: #f4ca58;
  --coral: #df7b59;
  --current: #75c9bd;
  position: relative;
  isolation: isolate;
  min-height: 100vh;
  overflow: clip;
  color: var(--ink);
  background:
    linear-gradient(rgba(117, 201, 189, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(117, 201, 189, 0.035) 1px, transparent 1px),
    linear-gradient(160deg, #051923 0%, #0a3039 52%, #061b26 100%);
  background-size: 5rem 5rem, 5rem 5rem, auto;
}

.reading-progress { position: fixed; z-index: 30; inset: 0 0 auto; height: 3px; pointer-events: none; }
.reading-progress span { display: block; width: calc(var(--reading-progress) / 360deg * 100%); height: 100%; background: linear-gradient(90deg, var(--coral), var(--signal), var(--current)); box-shadow: 0 0 0.9rem rgba(244, 202, 88, 0.55); transition: width 0.12s linear; }
.article-chart { position: fixed; z-index: -1; inset: 0; overflow: hidden; pointer-events: none; opacity: 0.72; }
.chart-route { position: absolute; top: 22vh; left: 0; width: 100%; height: 52rem; color: var(--current); transform: rotate(-4deg); }
.chart-route-base, .chart-route-flow { fill: none; vector-effect: non-scaling-stroke; }
.chart-route-base { stroke: currentColor; stroke-width: 1; stroke-dasharray: 3 10; opacity: 0.25; }
.chart-route-flow { stroke: var(--signal); stroke-width: 2; stroke-linecap: round; stroke-dasharray: 8 180; filter: drop-shadow(0 0 0.45rem rgba(244, 202, 88, 0.68)); animation: route-signal 11s linear infinite; }
.chart-orbit { position: absolute; width: 24rem; aspect-ratio: 1; border: 1px solid rgba(117, 201, 189, 0.1); border-radius: 50%; }
.chart-orbit::before, .chart-orbit::after { content: ""; position: absolute; inset: 16%; border: 1px dashed rgba(244, 202, 88, 0.1); border-radius: 50%; }
.chart-orbit::after { inset: 42%; border-style: solid; box-shadow: 0 0 2rem rgba(117, 201, 189, 0.13); }
.chart-orbit-one { top: 38rem; right: -10rem; animation: orbit-turn 38s linear infinite; }
.chart-orbit-two { bottom: 8rem; left: -11rem; width: 32rem; animation: orbit-turn 52s linear infinite reverse; }

.article-hero { position: relative; min-height: min(48rem, 86vh); display: flex; align-items: flex-end; overflow: hidden; padding: 8.5rem 1.5rem 5.5rem; background: radial-gradient(circle at 82% 22%, rgba(244, 202, 88, 0.13), transparent 17rem), linear-gradient(122deg, rgba(223, 123, 89, 0.18), transparent 35%), #061d28; }
.article-hero::before { content: ""; position: absolute; inset: 0; pointer-events: none; background: repeating-linear-gradient(112deg, transparent 0 2.8rem, rgba(117, 201, 189, 0.045) 2.85rem 2.9rem), linear-gradient(90deg, transparent 49.9%, rgba(244, 202, 88, 0.1) 50%, transparent 50.1%); mask-image: linear-gradient(90deg, #000, transparent 78%); }
.article-hero::after { content: "LOG"; position: absolute; right: -0.05em; bottom: -0.22em; color: rgba(244, 240, 223, 0.035); font-family: var(--display-font); font-size: clamp(12rem, 30vw, 32rem); line-height: 0.8; pointer-events: none; }
.article-hero.has-cover { background-image: linear-gradient(90deg, rgba(5, 25, 35, 0.97) 0%, rgba(5, 25, 35, 0.78) 48%, rgba(5, 25, 35, 0.34) 100%), var(--article-cover); background-position: center; background-size: cover; }
.hero-shade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(180deg, transparent 58%, #061d28 100%); }
.article-hero-inner { position: relative; z-index: 1; width: min(1180px, 100%); margin: 0 auto; }
.article-back-link { display: inline-flex; gap: 0.55rem; align-items: center; margin-bottom: clamp(3rem, 8vh, 6.5rem); color: var(--current); font-family: "Noto Sans SC", sans-serif; font-size: 0.78rem; text-decoration: none; transition: color 0.25s ease, transform 0.25s ease; }
.article-back-link:hover, .article-back-link:focus-visible { color: var(--signal); transform: translateX(-0.3rem); }
.hero-heading { max-width: 58rem; animation: hero-entry 0.9s 0.08s cubic-bezier(0.2, 0.76, 0.26, 1) both; }
.article-kicker { display: flex; flex-wrap: wrap; gap: 0.75rem 1.4rem; align-items: center; margin: 0 0 1.15rem; color: var(--signal); font-family: "Noto Sans SC", sans-serif; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em; }
.article-kicker span + span { color: rgba(244, 240, 223, 0.52); font-weight: 500; letter-spacing: 0.04em; }
.article-hero h1 { max-width: 15ch; margin: 0; color: #fff9e9; font-family: var(--display-font); font-size: clamp(3.25rem, 8vw, 7.8rem); line-height: 0.98; text-wrap: balance; text-shadow: 0 1.2rem 4rem rgba(0, 0, 0, 0.34); }
.article-summary { max-width: 45rem; margin: 1.7rem 0 0; color: rgba(244, 240, 223, 0.76); font-family: "Noto Sans SC", sans-serif; font-size: clamp(1rem, 1.8vw, 1.2rem); line-height: 1.85; }
.article-manifest { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); width: min(47rem, 100%); margin-top: 3.2rem; border-top: 1px solid rgba(244, 240, 223, 0.2); animation: manifest-entry 0.8s 0.32s cubic-bezier(0.2, 0.76, 0.26, 1) both; }
.article-manifest div { display: grid; gap: 0.35rem; padding: 1rem 1rem 0 0; }
.article-manifest span { color: rgba(244, 240, 223, 0.42); font-family: "Noto Sans SC", sans-serif; font-size: 0.63rem; }
.article-manifest strong { color: var(--ink); font-family: "Noto Sans SC", sans-serif; font-size: 0.85rem; font-weight: 500; }
.hero-depth { position: absolute; right: 2rem; bottom: 2rem; z-index: 1; display: flex; gap: 0.65rem; align-items: center; color: rgba(117, 201, 189, 0.46); font-family: "Noto Sans SC", sans-serif; font-size: 0.54rem; letter-spacing: 0.14em; writing-mode: vertical-rl; }
.hero-depth i { width: 1px; height: 4.5rem; background: linear-gradient(transparent, var(--current), transparent); }

.article-reading-layout { position: relative; z-index: 1; display: grid; grid-template-columns: minmax(10rem, 15rem) minmax(0, 48rem); gap: clamp(2rem, 6vw, 6rem); width: min(1120px, calc(100% - 3rem)); margin: 0 auto; padding: 7rem 0 8rem; }
.reading-rail-sticky { position: sticky; top: 7rem; display: grid; grid-template-rows: auto minmax(0, 1fr); gap: 2rem; max-height: calc(100vh - 8.5rem); }
.reading-gauge { display: flex; gap: 0.85rem; align-items: center; }
.reading-gauge p { margin: 0; color: rgba(244, 240, 223, 0.38); font-family: "Noto Sans SC", sans-serif; font-size: 0.54rem; line-height: 1.5; letter-spacing: 0.13em; }
.reading-gauge-ring { position: relative; display: flex; align-items: baseline; justify-content: center; width: 4.5rem; aspect-ratio: 1; border-radius: 50%; background: conic-gradient(var(--signal) var(--reading-progress), rgba(244, 240, 223, 0.1) 0); }
.reading-gauge-ring::before { content: ""; position: absolute; inset: 3px; border-radius: inherit; background: #08232d; }
.reading-gauge-ring span, .reading-gauge-ring small { position: relative; z-index: 1; }
.reading-gauge-ring span { font-family: var(--display-font); font-size: 1.25rem; }
.reading-gauge-ring small { color: var(--current); font-family: "Noto Sans SC", sans-serif; font-size: 0.52rem; }
.article-toc { display: grid; grid-template-rows: auto minmax(0, 1fr); min-height: 0; }
.article-toc-list { min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding-right: 0.45rem; scrollbar-color: rgba(117, 201, 189, 0.38) transparent; scrollbar-width: thin; }
.article-toc-list::-webkit-scrollbar { width: 4px; }
.article-toc-list::-webkit-scrollbar-thumb { border-radius: 999px; background: rgba(117, 201, 189, 0.38); }
.article-toc-list::-webkit-scrollbar-track { background: transparent; }
.article-toc > p { margin: 0 0 1rem; color: var(--signal); font-family: "Noto Sans SC", sans-serif; font-size: 0.64rem; letter-spacing: 0.14em; }
.article-toc button { position: relative; display: grid; grid-template-columns: 1.65rem minmax(0, 1fr); gap: 0.45rem; width: 100%; padding: 0.62rem 0.4rem 0.62rem 0; border: 0; color: rgba(244, 240, 223, 0.48); background: transparent; font-family: "Noto Sans SC", sans-serif; font-size: 0.72rem; line-height: 1.45; text-align: left; cursor: pointer; transition: color 0.25s ease, transform 0.25s ease; }
.article-toc button::before { content: ""; position: absolute; top: 50%; left: -1.1rem; width: 0.42rem; height: 0.42rem; border: 1px solid currentColor; border-radius: 50%; opacity: 0; transform: translateY(-50%) scale(0.45); transition: opacity 0.25s ease, transform 0.25s ease; }
.article-toc button span { color: rgba(117, 201, 189, 0.46); font-size: 0.58rem; }
.article-toc button:hover, .article-toc button:focus-visible, .article-toc button.active { color: var(--ink); transform: translateX(0.3rem); }
.article-toc button.active::before { color: var(--signal); opacity: 1; transform: translateY(-50%) scale(1); box-shadow: 0 0 0.75rem rgba(244, 202, 88, 0.55); }
.article-toc button.level-3 { padding-left: 1.1rem; font-size: 0.67rem; }
.article-toc-empty { display: flex; gap: 0.65rem; align-items: center; color: rgba(244, 240, 223, 0.36); font-family: "Noto Sans SC", sans-serif; font-size: 0.65rem; }
.article-toc-empty span { width: 2.5rem; height: 1px; background: rgba(117, 201, 189, 0.38); }
.article-document { min-width: 0; }
.document-scrollbar { position: fixed; z-index: 19; top: 7.4rem; right: 1.15rem; bottom: 2rem; width: 0.68rem; border: 1px solid rgba(117, 201, 189, 0.24); border-radius: 999px; background: rgba(4, 21, 30, 0.52); cursor: ns-resize; touch-action: none; }
.document-scrollbar::before, .document-scrollbar::after { content: ""; position: absolute; right: 50%; width: 0.18rem; height: 0.18rem; border: 1px solid rgba(244, 202, 88, 0.58); border-radius: 50%; transform: translateX(50%); }
.document-scrollbar::before { top: -0.7rem; }
.document-scrollbar::after { bottom: -0.7rem; }
.document-scrollbar-thumb { position: absolute; right: 1px; left: 1px; display: block; min-height: 3.25rem; border-radius: inherit; background: linear-gradient(180deg, var(--signal), var(--current)); box-shadow: 0 0 0.85rem rgba(117, 201, 189, 0.38); transition: background 0.2s ease, box-shadow 0.2s ease; }
.document-scrollbar:hover .document-scrollbar-thumb, .document-scrollbar:focus-visible .document-scrollbar-thumb { background: linear-gradient(180deg, #ffe28a, #8fe2d5); box-shadow: 0 0 1.2rem rgba(244, 202, 88, 0.48); }
.document-header { display: flex; justify-content: space-between; gap: 1rem; align-items: flex-end; margin-bottom: 3.5rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(244, 240, 223, 0.16); font-family: "Noto Sans SC", sans-serif; }
.document-header p { margin: 0; color: var(--signal); font-size: 0.67rem; font-weight: 700; letter-spacing: 0.16em; }
.document-header div { display: flex; flex-wrap: wrap; gap: 0.5rem 1rem; justify-content: flex-end; color: rgba(244, 240, 223, 0.42); font-size: 0.62rem; }
.article-detail-cover { display: block; width: 100%; max-height: 32rem; margin-bottom: 4rem; border: 1px solid rgba(244, 240, 223, 0.14); border-radius: 4px; object-fit: cover; box-shadow: 1.2rem 1.2rem 0 rgba(117, 201, 189, 0.06); }

.markdown-body { color: rgba(244, 240, 223, 0.86); font-family: "Noto Sans SC", sans-serif; font-size: 1.04rem; line-height: 2.05; overflow-wrap: anywhere; }
.markdown-body.motion-ready > :deep(*) { opacity: 0; transform: translateY(1.3rem); }
.markdown-body.motion-ready > :deep(.is-visible) { opacity: 1; transform: translateY(0); transition: opacity 0.72s var(--reveal-delay) ease, transform 0.72s var(--reveal-delay) cubic-bezier(0.2, 0.76, 0.26, 1); }
.markdown-body :deep(h1) { margin: 0 0 2rem; color: var(--ink); font-family: var(--display-font); font-size: clamp(2rem, 4vw, 3.25rem); line-height: 1.22; }
.markdown-body :deep(h2), .markdown-body :deep(h3) { scroll-margin-top: 7rem; color: var(--ink); font-family: var(--display-font); line-height: 1.3; }
.markdown-body :deep(h2) { position: relative; margin: 5.5rem 0 1.5rem; padding-top: 1.2rem; border-top: 1px solid rgba(117, 201, 189, 0.22); font-size: clamp(1.75rem, 3.4vw, 2.6rem); }
.markdown-body :deep(h2)::before { content: ""; position: absolute; top: -0.28rem; left: 0; width: 3.2rem; height: 0.5rem; background: var(--coral); clip-path: polygon(0 42%, 83% 42%, 100% 0, 89% 50%, 100% 100%, 83% 58%, 0 58%); }
.markdown-body :deep(h3) { margin: 3.2rem 0 1rem; font-size: 1.55rem; }
.markdown-body :deep(p) { margin: 1.4rem 0; }
.markdown-body :deep(a) { color: var(--signal); text-decoration-color: rgba(244, 202, 88, 0.42); text-underline-offset: 0.28em; }
.markdown-body :deep(a):hover { color: #ffe28a; }
.markdown-body :deep(strong) { color: #fff9e9; }
.markdown-body :deep(hr) { height: 1px; margin: 4rem 0; border: 0; background: linear-gradient(90deg, transparent, rgba(117, 201, 189, 0.42), transparent); }
.markdown-body :deep(img) { display: block; max-width: 100%; height: auto; margin: 2.8rem auto; border: 1px solid rgba(244, 240, 223, 0.14); border-radius: 4px; box-shadow: 0 1.5rem 4rem rgba(0, 0, 0, 0.26); }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 1.5rem; }
.markdown-body :deep(li) { margin: 0.55rem 0; padding-left: 0.35rem; }
.markdown-body :deep(li)::marker { color: var(--coral); }
.markdown-body :deep(blockquote) { position: relative; margin: 2.8rem 0; padding: 1.4rem 1.7rem 1.4rem 2rem; border: 0; border-left: 2px solid var(--signal); color: rgba(244, 240, 223, 0.7); background: linear-gradient(90deg, rgba(244, 202, 88, 0.09), transparent); }
.markdown-body :deep(blockquote)::before { content: "SIGNAL"; position: absolute; top: -0.65rem; left: 1.55rem; padding: 0 0.4rem; color: var(--signal); background: #092832; font-size: 0.52rem; letter-spacing: 0.12em; }
.markdown-body :deep(blockquote p) { margin: 0; }
.markdown-body :deep(code) { padding: 0.12rem 0.35rem; border: 1px solid rgba(223, 123, 89, 0.16); border-radius: 3px; color: #ffd9ae; background: rgba(223, 123, 89, 0.1); font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace; font-size: 0.9em; }
.markdown-body :deep(pre) { position: relative; overflow-x: auto; margin: 2.6rem 0; padding: 2.8rem 1.45rem 1.45rem; border: 1px solid rgba(117, 201, 189, 0.18); border-radius: 4px; color: #e7f2e8; background: linear-gradient(90deg, rgba(117, 201, 189, 0.06) 1px, transparent 1px), #04151e; background-size: 3rem 100%; box-shadow: 0 1.4rem 3.5rem rgba(0, 0, 0, 0.22); }
.markdown-body :deep(pre)::before { content: "CODE / SHIP LOG"; position: absolute; top: 0.78rem; left: 1.4rem; color: rgba(117, 201, 189, 0.55); font-size: 0.55rem; letter-spacing: 0.12em; }
.markdown-body :deep(pre code) { padding: 0; border: 0; color: inherit; background: transparent; }
.markdown-body :deep(table) { width: 100%; margin: 2.5rem 0; border-collapse: collapse; font-size: 0.9rem; }
.markdown-body :deep(th), .markdown-body :deep(td) { padding: 0.8rem; border-bottom: 1px solid rgba(244, 240, 223, 0.14); text-align: left; }
.markdown-body :deep(th) { color: var(--signal); font-weight: 500; }

.article-source { margin: 4rem 0 0; padding: 1rem 1.2rem; border-left: 2px solid var(--coral); color: rgba(244, 240, 223, 0.56); background: rgba(223, 123, 89, 0.06); font-family: "Noto Sans SC", sans-serif; font-size: 0.78rem; }
.article-source a { color: var(--signal); }
.article-detail-footer { display: flex; align-items: center; justify-content: space-between; gap: 1.5rem; margin-top: 5rem; padding-top: 2rem; border-top: 1px solid rgba(244, 240, 223, 0.16); }
.article-detail-tags { display: flex; flex-wrap: wrap; gap: 0.55rem; }
.article-detail-tags span { padding: 0.38rem 0; color: var(--current); font-family: "Noto Sans SC", sans-serif; font-size: 0.75rem; }
.article-like-area { display: grid; justify-items: end; gap: 0.45rem; }
.article-like-area small { color: #f2a183; font-family: "Noto Sans SC", sans-serif; font-size: 0.68rem; }
.article-like-button { display: grid; grid-template-columns: auto auto auto; gap: 0.65rem; align-items: center; min-height: 2.9rem; padding: 0.6rem 0.85rem; border: 1px solid rgba(223, 123, 89, 0.68); border-radius: 4px; color: #f3a181; background: rgba(223, 123, 89, 0.06); font-family: "Noto Sans SC", sans-serif; cursor: pointer; transition: color 0.25s ease, background-color 0.25s ease, transform 0.25s ease, box-shadow 0.25s ease; }
.article-like-button strong { min-width: 2rem; padding-left: 0.65rem; border-left: 1px solid rgba(223, 123, 89, 0.32); color: var(--ink); }
.article-like-button:hover:not(:disabled), .article-like-button:focus-visible { color: #fff6e6; background: rgba(223, 123, 89, 0.2); box-shadow: 0 0 1.7rem rgba(223, 123, 89, 0.16); transform: translateY(-0.18rem); }
.article-like-button:disabled { cursor: wait; opacity: 0.72; }
.article-like-button.is-liked { border-color: rgba(117, 201, 189, 0.7); color: var(--current); background: rgba(117, 201, 189, 0.12); cursor: default; opacity: 1; }
.article-like-button.is-liked .like-symbol { color: var(--current); }
.article-like-button.celebrated .like-symbol { animation: like-burst 0.72s cubic-bezier(0.2, 0.76, 0.26, 1); }
.like-symbol { color: var(--coral); font-size: 1rem; }
.document-end { display: flex; gap: 1rem; align-items: center; margin-top: 5rem; color: rgba(244, 240, 223, 0.26); font-family: "Noto Sans SC", sans-serif; font-size: 0.55rem; letter-spacing: 0.16em; }
.document-end i { flex: 1; height: 1px; background: linear-gradient(90deg, transparent, rgba(117, 201, 189, 0.26)); }
.document-end i:last-child { transform: scaleX(-1); }

.article-detail-state { position: relative; z-index: 1; display: grid; min-height: 100vh; place-content: center; justify-items: center; color: var(--muted); font-family: "Noto Sans SC", sans-serif; }
.article-detail-state p { margin: 1.5rem 0 0.35rem; }
.article-detail-state small { color: rgba(117, 201, 189, 0.42); font-size: 0.58rem; letter-spacing: 0.16em; }
.state-radar { position: relative; width: 4rem; aspect-ratio: 1; border: 1px solid rgba(117, 201, 189, 0.38); border-radius: 50%; }
.state-radar::before { content: ""; position: absolute; inset: 50% 50% 0; border-left: 1px solid var(--signal); transform-origin: top left; animation: radar-sweep 1.6s linear infinite; }
.article-detail-error { gap: 1rem; }
.article-detail-error a { color: var(--signal); }

@keyframes route-signal { to { stroke-dashoffset: -376; } }
@keyframes orbit-turn { to { transform: rotate(360deg); } }
@keyframes hero-entry { from { opacity: 0; transform: translateY(2.2rem); } to { opacity: 1; transform: translateY(0); } }
@keyframes manifest-entry { from { opacity: 0; clip-path: inset(0 100% 0 0); } to { opacity: 1; clip-path: inset(0); } }
@keyframes like-burst { 0%, 100% { transform: scale(1); } 42% { color: var(--signal); transform: scale(1.8) rotate(-10deg); filter: drop-shadow(0 0 0.5rem rgba(244, 202, 88, 0.7)); } }
@keyframes radar-sweep { to { transform: rotate(360deg); } }

@media (max-width: 900px) {
  .article-hero { min-height: 46rem; padding-top: 10rem; }
  .article-reading-layout { grid-template-columns: 1fr; width: min(48rem, calc(100% - 3rem)); padding-top: 4.5rem; }
  .reading-rail, .hero-depth { display: none; }
  .document-scrollbar { right: 0.55rem; }
}

@media (max-width: 600px) {
  .article-hero { min-height: 42rem; padding: 10.5rem 1rem 3.5rem; }
  .article-back-link { margin-bottom: 3.5rem; }
  .article-hero h1 { font-size: clamp(2.8rem, 14vw, 4.5rem); }
  .article-manifest { grid-template-columns: repeat(2, minmax(0, 1fr)); margin-top: 2.2rem; }
  .article-reading-layout { width: calc(100% - 2rem); padding: 3.5rem 0 5rem; }
  .document-header { align-items: flex-start; flex-direction: column; }
  .document-header div { justify-content: flex-start; }
  .markdown-body { font-size: 0.98rem; line-height: 1.95; }
  .markdown-body :deep(h2) { margin-top: 4rem; }
  .markdown-body :deep(pre) { margin-inline: -0.35rem; padding-inline: 1rem; }
  .article-detail-footer { align-items: stretch; flex-direction: column; }
  .article-like-area { justify-items: stretch; }
  .article-like-button { justify-content: center; }
  .document-end { gap: 0.55rem; }
  .document-end span { letter-spacing: 0.08em; white-space: nowrap; }
  .document-scrollbar { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  .chart-route-flow, .chart-orbit, .hero-heading, .article-manifest, .article-like-button.celebrated .like-symbol, .state-radar::before { animation: none; }
  .markdown-body.motion-ready > :deep(*) { opacity: 1; transform: none; transition: none; }
  .reading-progress span, .article-toc button, .article-back-link, .article-like-button { transition: none; }
}
</style>
