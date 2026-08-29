<script setup lang="ts">
import DOMPurify from "dompurify";
import hljs from "highlight.js/lib/common";
import { marked } from "marked";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import {
  fetchArticle,
  fetchArticleContext,
  likeArticle,
  type Article,
  type ArticleContext,
} from "../api/articles";
import { ApiError } from "../api/http";
import OceanAtmosphere from "../components/OceanAtmosphere.vue";
import { readArticleReturnContext } from "../composables/useArticleReturnContext";
import { useSeo } from "../composables/useSeo";

type TocItem = { id: string; level: number; text: string };
type PreviewImage = { src: string; alt: string };

const route = useRoute();
const router = useRouter();
const article = ref<Article | null>(null);
const articleContext = ref<ArticleContext | null>(null);
const articleContent = ref("");
const articleToc = ref<TocItem[]>([]);
const contentRoot = ref<HTMLElement | null>(null);
const readingRegion = ref<HTMLElement | null>(null);
const documentScrollTrack = ref<HTMLElement | null>(null);
const loading = ref(true);
const errorText = ref("");
const notFound = ref(false);
const liking = ref(false);
const likeError = ref("");
const likedRecently = ref(false);
const readingProgress = ref(0);
const activeHeadingId = ref("");
const documentIsScrollable = ref(false);
const documentScrollThumbSize = ref(1);
const pageScrollProgress = ref(0);
const previewImage = ref<PreviewImage | null>(null);
const copyState = ref<"idle" | "copied" | "error">("idle");
const shareState = ref<"idle" | "shared" | "copied" | "error">("idle");
const { applySeo } = useSeo();

let scrollFrame: number | undefined;
let revealObserver: IntersectionObserver | undefined;
let likeTimer: number | undefined;
let loadVersion = 0;
let documentScrollbarDragOffset = 0;
let bodyOverflowBeforePreview: string | null = null;
let feedbackTimer: number | undefined;

const articleNumber = computed(() => String(article.value?.id ?? 0).padStart(4, "0"));
const returnContext = computed(() => readArticleReturnContext());
const articleReturnLabel = computed(() =>
  returnContext.value?.source === "series" ? "返回专题" : "返回文章列表",
);
const readingPercent = computed(() => Math.round(readingProgress.value * 100));
const readingProgressStyle = computed(() => ({
  "--reading-progress": `${readingProgress.value * 360}deg`,
  "--reading-ratio": String(readingProgress.value),
}));
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

// 复制图标的内联 SVG：站点未引入图标库，保持与后台预览类似的极简剪贴板图形。
const CODE_COPY_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2" /><path d="M5 15V5a2 2 0 0 1 2-2h10" /></svg>';

function escapeCodeHtml(value: string) {
  const holder = document.createElement("div");
  holder.textContent = value;
  return holder.innerHTML;
}

// 将 Markdown 代码块重建为 mac 风格卡片：行号、语言标识、复制按钮 + highlight.js 高亮，
// 视觉对齐后台编辑器（md-editor-v3）的预览效果。
function transformCodeBlocks(root: HTMLElement) {
  root.querySelectorAll("pre > code").forEach((codeElement) => {
    const preElement = codeElement.parentElement;
    if (!preElement) return;
    const requestedLanguage = /language-([\w-]+)/.exec(codeElement.className)?.[1] ?? "";
    // marked 会在代码文本末尾补一个换行，先去掉，行号和高亮才不会多出一行。
    const rawCode = (codeElement.textContent ?? "").replace(/\n$/, "");
    const language = hljs.getLanguage(requestedLanguage) ? requestedLanguage : "";
    let highlighted: string;
    let displayLanguage = requestedLanguage || "code";
    try {
      if (language) {
        highlighted = hljs.highlight(rawCode, { language }).value;
      } else {
        const detected = hljs.highlightAuto(rawCode);
        highlighted = detected.value;
        displayLanguage = detected.language ?? "code";
      }
    } catch {
      // 高亮失败时退化为转义后的纯文本，保证内容仍然可读
      highlighted = escapeCodeHtml(rawCode);
    }
    const lineNumbers = Array.from({ length: Math.max(rawCode.split("\n").length, 1) }, (_, index) => index + 1).join("\n");
    const wrapper = document.createElement("div");
    wrapper.className = "md-code";
    wrapper.innerHTML = [
      '<div class="md-code-head">',
      '  <span class="md-code-dots" aria-hidden="true"><i></i><i></i><i></i></span>',
      '  <span class="md-code-meta">',
      `    <span class="md-code-lang">${escapeCodeHtml(displayLanguage)}</span>`,
      `    <button class="md-code-copy" type="button">${CODE_COPY_ICON}<span>复制代码</span></button>`,
      "  </span>",
      "</div>",
      '<div class="md-code-body">',
      `  <pre class="md-code-lines" aria-hidden="true">${lineNumbers}</pre>`,
      `  <pre class="md-code-content"><code class="hljs">${highlighted}</code></pre>`,
      "</div>",
    ].join("");
    preElement.replaceWith(wrapper);
  });
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
    image.setAttribute("tabindex", "0");
    image.setAttribute("role", "button");
    image.setAttribute("aria-label", image.getAttribute("alt") || "查看文章图片");
  });
  transformCodeBlocks(safeDocument.body);
  articleContent.value = safeDocument.body.innerHTML;
  activeHeadingId.value = articleToc.value[0]?.id ?? "";
}

function openImagePreview(image: HTMLImageElement) {
  const src = image.currentSrc || image.getAttribute("src");
  if (!src) return;
  previewImage.value = { src, alt: image.getAttribute("alt") || article.value?.title || "文章图片" };
}

function handleContentClick(event: MouseEvent) {
  if (!(event.target instanceof Element)) return;
  const copyButton = event.target.closest(".md-code-copy");
  if (copyButton instanceof HTMLButtonElement) {
    handleCodeCopy(copyButton);
    return;
  }
  const target = event.target.closest("img");
  if (!(target instanceof HTMLImageElement)) return;
  event.preventDefault();
  openImagePreview(target);
}

async function handleCodeCopy(button: HTMLButtonElement) {
  const label = button.querySelector("span");
  const code = button.closest(".md-code")?.querySelector(".md-code-content code")?.textContent ?? "";
  if (!label || !code) return;
  const copied = await copyTextToClipboard(code);
  button.classList.toggle("is-copied", copied);
  button.classList.toggle("is-failed", !copied);
  label.textContent = copied ? "已复制" : "复制失败";
  window.setTimeout(() => {
    button.classList.remove("is-copied", "is-failed");
    label.textContent = "复制代码";
  }, 1600);
}

function handleContentKeydown(event: KeyboardEvent) {
  if (event.key !== "Enter" && event.key !== " ") return;
  if (!(event.target instanceof HTMLImageElement)) return;
  event.preventDefault();
  openImagePreview(event.target);
}

function closeImagePreview() {
  previewImage.value = null;
}

function handlePreviewKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") closeImagePreview();
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
  notFound.value = false;
  article.value = null;
  articleContext.value = null;
  articleContent.value = "";
  articleToc.value = [];
  readingProgress.value = 0;
  revealObserver?.disconnect();
  try {
    const slug = String(route.params.slug);
    const result = await fetchArticle(slug);
    if (currentLoad !== loadVersion) return;
    article.value = result;
    const context = await fetchArticleContext(slug).catch(() => null);
    if (currentLoad !== loadVersion) return;
    articleContext.value = context;
    buildArticleContent(result.content_markdown);
    applySeo({
      title: result.title,
      description: result.summary || normalizeMarkdown(result.content_markdown).replace(/[#>*_`[\]()!-]/g, " ").replace(/\s+/g, " ").trim().slice(0, 160),
      canonicalPath: `/articles/${result.slug}`,
      image: result.cover_image_url,
      type: "article",
      jsonLd: {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        headline: result.title,
        description: result.summary,
        image: result.cover_image_url,
        datePublished: result.published_at ?? result.created_at,
        dateModified: result.updated_at,
        author: { "@type": "Person", name: result.author },
      },
    });
    await nextTick();
    updateReadingState();
    await nextTick();
    setupContentReveal();
  } catch (error) {
    if (currentLoad === loadVersion) {
      notFound.value = error instanceof ApiError && error.status === 404;
      errorText.value = notFound.value
        ? "这段航行记录不存在，或已经离开当前航线。"
        : "文章航线暂时无法连接，请检查网络后重试。";
    }
  } finally {
    if (currentLoad === loadVersion) loading.value = false;
  }
}

function resetFeedback() {
  window.clearTimeout(feedbackTimer);
  feedbackTimer = window.setTimeout(() => {
    copyState.value = "idle";
    shareState.value = "idle";
  }, 1600);
}

async function copyArticleLink() {
  copyState.value = (await copyTextToClipboard(window.location.href)) ? "copied" : "error";
  resetFeedback();
}

// 统一剪贴板入口：优先 Clipboard API，失败时降级为隐藏 textarea + execCommand。
async function copyTextToClipboard(text: string): Promise<boolean> {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // 进入降级方案
    }
  }
  const input = document.createElement("textarea");
  input.value = text;
  input.style.position = "fixed";
  input.style.opacity = "0";
  document.body.appendChild(input);
  input.select();
  let copied: boolean;
  try {
    copied = document.execCommand("copy");
  } catch {
    copied = false;
  }
  input.remove();
  return copied;
}

async function shareArticle() {
  if (!article.value) return;
  if (!navigator.share) {
    await copyArticleLink();
    shareState.value = copyState.value === "copied" ? "copied" : "error";
    resetFeedback();
    return;
  }
  try {
    await navigator.share({
      title: article.value.title,
      text: article.value.summary,
      url: window.location.href,
    });
    shareState.value = "shared";
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") return;
    shareState.value = "error";
  }
  resetFeedback();
}

async function returnToEntry() {
  const context = readArticleReturnContext();
  const targetPath = context?.path || "/articles?view=archive";
  await router.push(targetPath);

  if (!context) return;

  window.requestAnimationFrame(() => {
    window.scrollTo({ top: context.scrollY, left: 0, behavior: "auto" });
  });
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

watch(previewImage, (image) => {
  if (image) {
    if (bodyOverflowBeforePreview === null) bodyOverflowBeforePreview = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handlePreviewKeydown);
    return;
  }
  window.removeEventListener("keydown", handlePreviewKeydown);
  if (bodyOverflowBeforePreview !== null) document.body.style.overflow = bodyOverflowBeforePreview;
  bodyOverflowBeforePreview = null;
});

onMounted(() => {
  window.addEventListener("scroll", updateReadingState, { passive: true });
  window.addEventListener("resize", updateReadingState, { passive: true });
});

onBeforeUnmount(() => {
  window.removeEventListener("scroll", updateReadingState);
  window.removeEventListener("resize", updateReadingState);
  window.removeEventListener("pointermove", handleDocumentScrollbarPointerMove);
  window.removeEventListener("keydown", handlePreviewKeydown);
  if (scrollFrame !== undefined) window.cancelAnimationFrame(scrollFrame);
  window.clearTimeout(likeTimer);
  window.clearTimeout(feedbackTimer);
  if (bodyOverflowBeforePreview !== null) document.body.style.overflow = bodyOverflowBeforePreview;
  revealObserver?.disconnect();
});
</script>

<template>
  <div class="article-detail-page" :style="readingProgressStyle">
    <OceanAtmosphere variant="detail" />
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
        <div class="article-hero-inner">
          <div class="article-hero-copy">
            <button class="article-back-link" type="button" @click="returnToEntry">
              <span aria-hidden="true">←</span> {{ articleReturnLabel }}
            </button>
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
          <div v-if="article.cover_image_url" class="article-hero-visual" aria-label="文章封面信标">
            <span class="cover-route-line" aria-hidden="true"></span>
            <div class="cover-frame">
              <span class="cover-grid" aria-hidden="true"></span>
              <span class="cover-coordinate cover-coordinate-top">SIGNAL / {{ articleNumber }}</span>
              <span class="cover-coordinate cover-coordinate-bottom">{{ article.category }} · COVER FRAME</span>
              <span class="cover-beacon" aria-hidden="true"><i></i><b></b></span>
              <img class="article-hero-cover" :src="article.cover_image_url" :alt="article.title" />
            </div>
          </div>
        </div>
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
          <!-- 内容已由 DOMPurify 清洗后再插入，保留 Markdown 的排版能力。 -->
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div ref="contentRoot" class="markdown-body" @click="handleContentClick" @keydown="handleContentKeydown" v-html="articleContent"></div>
          <p v-if="article.is_repost && article.source_url" class="article-source">本文转载自 <a :href="article.source_url" target="_blank" rel="noreferrer noopener">原始来源</a></p>
          <footer class="article-detail-footer">
            <div class="article-detail-tags">
              <RouterLink
                v-for="tag in article.tags"
                :key="tag"
                :to="{ path: '/articles', query: { view: 'tags', tag } }"
              >
                # {{ tag }}
              </RouterLink>
            </div>
            <div class="article-like-area">
              <button :class="['article-like-button', { celebrated: likedRecently, 'is-liked': article.liked_by_current_visitor }]" type="button" :disabled="liking || article.liked_by_current_visitor" @click="handleLike">
                <span class="like-symbol" aria-hidden="true">♥</span><span>{{ article.liked_by_current_visitor ? "已点赞" : liking ? "正在送达" : "点赞" }}</span><strong>{{ article.likes }}</strong>
              </button>
              <small v-if="likeError" role="status">{{ likeError }}</small>
            </div>
          </footer>
          <section class="article-share-panel" aria-label="分享文章">
            <div><p>SHARE THIS LOG</p><span>把这段航行记录交给下一位读者。</span></div>
            <div>
              <button type="button" :class="{ confirmed: copyState === 'copied' }" @click="copyArticleLink">
                {{ copyState === "copied" ? "链接已复制" : copyState === "error" ? "复制失败" : "复制链接" }}
              </button>
              <button type="button" :class="{ confirmed: shareState === 'shared' || shareState === 'copied' }" @click="shareArticle">
                {{ shareState === "shared" ? "分享完成" : shareState === "copied" ? "链接已复制" : shareState === "error" ? "分享失败" : "系统分享" }}
              </button>
            </div>
          </section>
          <section v-if="articleContext" class="article-continuation" aria-label="继续阅读">
            <RouterLink v-if="articleContext.series" class="article-series-link" :to="`/series/${articleContext.series.slug}`">
              <span>当前专题</span><strong>{{ articleContext.series.title }}</strong><i aria-hidden="true">查看完整航线 →</i>
            </RouterLink>
            <div class="article-adjacent-links">
              <RouterLink v-if="articleContext.previous" :to="`/articles/${articleContext.previous.slug}`">
                <span>← 上一篇</span><strong>{{ articleContext.previous.title }}</strong>
              </RouterLink>
              <div v-else aria-hidden="true"></div>
              <RouterLink v-if="articleContext.next" :to="`/articles/${articleContext.next.slug}`">
                <span>下一篇 →</span><strong>{{ articleContext.next.title }}</strong>
              </RouterLink>
            </div>
            <div v-if="articleContext.related.length" class="related-articles">
              <p>RELATED LOGS / 相关推荐</p>
              <div>
                <RouterLink v-for="related in articleContext.related" :key="related.id" :to="`/articles/${related.slug}`">
                  <span>{{ related.category }}</span><strong>{{ related.title }}</strong><small>{{ related.summary || "打开文章继续阅读。" }}</small>
                </RouterLink>
              </div>
            </div>
          </section>
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
      <p>{{ errorText }}</p>
      <button v-if="notFound" type="button" @click="returnToEntry">{{ articleReturnLabel }}</button>
      <button v-else type="button" @click="loadArticle">重新读取</button>
    </div>

    <Teleport to="body">
      <Transition name="image-preview">
        <div v-if="previewImage" class="article-image-preview" role="dialog" aria-modal="true" :aria-label="previewImage.alt" tabindex="-1" @click.self="closeImagePreview" @keydown="handlePreviewKeydown">
          <button class="image-preview-close" type="button" aria-label="关闭图片预览" @click="closeImagePreview">×</button>
          <figure>
            <img :src="previewImage.src" :alt="previewImage.alt" />
            <figcaption v-if="previewImage.alt">{{ previewImage.alt }}</figcaption>
          </figure>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped lang="scss">
.article-detail-page {
  --ink: #183138;
  --muted: #637475;
  --deep-sea: #0e343b;
  --signal: #9f7a31;
  --coral: #b35f48;
  --current: #276f6d;
  --paper: #f7f2e9;
  --paper-soft: #fffaf2;
  --line: rgba(24, 49, 56, 0.12);
  position: relative;
  isolation: isolate;
  min-height: 100vh;
  overflow: clip;
  color: var(--ink);
  background:
    linear-gradient(180deg, rgba(239, 246, 241, 0.86) 0, rgba(247, 242, 233, 0.96) 22rem, #fbf7ef 100%);
}

.reading-progress { position: fixed; z-index: 30; inset: 0 0 auto; height: 3px; pointer-events: none; }
.reading-progress span { display: block; width: 100%; height: 100%; background: linear-gradient(90deg, var(--signal), var(--current)); box-shadow: none; transform: scaleX(var(--reading-ratio)); transform-origin: left; transition: transform 0.12s linear; }
.article-detail-page ::selection { color: #fffaf0; background: rgba(35, 123, 120, 0.72); }
.article-hero, .article-reading-layout, .article-detail-state { position: relative; z-index: 1; }
.article-chart { position: fixed; z-index: -1; inset: 0; overflow: hidden; pointer-events: none; opacity: 0.12; }
.chart-route { position: absolute; top: 22vh; left: 0; width: 100%; height: 52rem; color: var(--current); transform: rotate(-4deg); }
.chart-route-base, .chart-route-flow { fill: none; vector-effect: non-scaling-stroke; }
.chart-route-base { stroke: currentColor; stroke-width: 1; stroke-dasharray: 3 10; opacity: 0.18; }
.chart-route-flow { stroke: var(--signal); stroke-width: 1.25; stroke-linecap: round; stroke-dasharray: 8 180; filter: none; animation: route-signal 14s linear infinite; }
.chart-orbit { position: absolute; width: 24rem; aspect-ratio: 1; border: 1px solid rgba(35, 123, 120, 0.08); border-radius: 50%; }
.chart-orbit::before, .chart-orbit::after { content: ""; position: absolute; inset: 16%; border: 1px dashed rgba(182, 128, 34, 0.12); border-radius: 50%; }
.chart-orbit::after { inset: 42%; border-style: solid; box-shadow: none; }
.chart-orbit-one { top: 38rem; right: -10rem; animation: orbit-turn 38s linear infinite; }
.chart-orbit-two { bottom: 8rem; left: -11rem; width: 32rem; animation: orbit-turn 52s linear infinite reverse; }

.article-hero { position: relative; padding: 5.9rem 1.5rem 1.55rem; border-bottom: 1px solid rgba(24, 49, 56, 0.08); background: rgba(255, 250, 242, 0.55); }
.article-hero::before { content: ""; position: absolute; inset: auto 0 0; height: 1px; pointer-events: none; background: linear-gradient(90deg, transparent, rgba(39, 111, 109, 0.2), transparent); }
.article-hero.has-cover { background-image: none; }
.article-hero-inner { position: relative; z-index: 1; display: grid; grid-template-columns: minmax(0, 1fr) minmax(19rem, 27rem); gap: clamp(2rem, 5vw, 4.5rem); align-items: center; width: min(1120px, 100%); margin: 0 auto; }
.article-back-link { display: inline-flex; gap: 0.5rem; align-items: center; margin-bottom: 1.2rem; padding: 0; border: 0; color: var(--current); background: transparent; font-family: "Noto Sans SC", sans-serif; font-size: 0.78rem; text-decoration: none; cursor: pointer; transition: color 0.25s ease, transform 0.25s ease; }
.article-back-link:hover, .article-back-link:focus-visible { color: var(--signal); transform: translateX(-0.3rem); }
.hero-heading { max-width: 55rem; animation: hero-entry 0.7s 0.06s cubic-bezier(0.2, 0.76, 0.26, 1) both; }
.article-kicker { display: flex; flex-wrap: wrap; gap: 0.6rem 1rem; align-items: center; margin: 0 0 0.8rem; color: var(--signal); font-family: "Noto Sans SC", sans-serif; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.03em; }
.article-kicker span + span { color: #768685; font-weight: 500; letter-spacing: 0; }
.article-hero h1 { max-width: 24ch; margin: 0; color: #142e35; font-family: "Noto Sans SC", sans-serif; font-size: clamp(2.05rem, 4.2vw, 4rem); font-weight: 800; line-height: 1.16; text-wrap: balance; text-shadow: none; }
.article-summary { max-width: 45rem; margin: 0.9rem 0 0; color: #526466; font-family: "Noto Sans SC", sans-serif; font-size: clamp(0.98rem, 1.25vw, 1.08rem); line-height: 1.78; }
.article-manifest { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); width: min(43rem, 100%); margin-top: 1.35rem; border-top: 1px solid var(--line); animation: manifest-entry 0.65s 0.18s cubic-bezier(0.2, 0.76, 0.26, 1) both; }
.article-manifest div { display: grid; gap: 0.2rem; padding: 0.65rem 0.75rem 0 0; }
.article-manifest span { color: #7f918f; font-family: "Noto Sans SC", sans-serif; font-size: 0.62rem; }
.article-manifest strong { color: var(--ink); font-family: "Noto Sans SC", sans-serif; font-size: 0.82rem; font-weight: 700; }
.article-hero-visual { position: relative; display: grid; place-items: center; min-height: clamp(18rem, 31vw, 24rem); isolation: isolate; animation: cover-entry 0.8s 0.1s cubic-bezier(0.2, 0.76, 0.26, 1) both; }
.cover-route-line { position: absolute; top: 47%; left: -2.25rem; width: 4.25rem; border-top: 1px dashed rgba(39, 111, 109, 0.55); transform: rotate(-13deg); transform-origin: right center; }
.cover-route-line::after { content: ""; position: absolute; top: -0.25rem; right: -0.2rem; width: 0.38rem; aspect-ratio: 1; border: 1px solid var(--signal); border-radius: 50%; background: var(--paper-soft); box-shadow: 0 0 0 0.3rem rgba(159, 122, 49, 0.11); }
.cover-frame { position: relative; isolation: isolate; width: min(100%, 25rem); aspect-ratio: 4 / 3; padding: 0.8rem; border: 1px solid rgba(16, 47, 55, 0.72); background: #102f37; box-shadow: 1.1rem 1.3rem 0 rgba(16, 47, 55, 0.1), 0 1.6rem 2.8rem rgba(20, 52, 57, 0.18); transform: rotate(1.8deg); transition: transform 320ms cubic-bezier(0.22, 1, 0.36, 1), box-shadow 320ms ease; }
.cover-frame::before { content: ""; position: absolute; z-index: -1; inset: 0.55rem -0.62rem -0.62rem 0.55rem; border: 1px solid rgba(159, 122, 49, 0.62); pointer-events: none; }
.cover-grid { position: absolute; z-index: 1; inset: 0.8rem; pointer-events: none; background-image: linear-gradient(rgba(220, 231, 223, 0.13) 1px, transparent 1px), linear-gradient(90deg, rgba(220, 231, 223, 0.13) 1px, transparent 1px); background-size: 2rem 2rem; mix-blend-mode: screen; opacity: 0.35; }
.cover-grid::before, .cover-grid::after { content: ""; position: absolute; background: rgba(220, 231, 223, 0.46); }
.cover-grid::before { top: 0; bottom: 0; left: 50%; width: 1px; }
.cover-grid::after { left: 0; right: 0; top: 50%; height: 1px; }
.article-hero-cover { display: block; width: 100%; height: 100%; border: 0; border-radius: 0; object-fit: cover; opacity: 0.92; filter: saturate(0.98) contrast(1.03); transition: transform 420ms cubic-bezier(0.22, 1, 0.36, 1), filter 320ms ease; }
.cover-coordinate { position: absolute; z-index: 2; color: rgba(244, 240, 223, 0.9); font: 600 0.54rem/1 "IBM Plex Mono", monospace; letter-spacing: 0.08em; text-shadow: 0 1px 0 rgba(3, 15, 22, 0.35); pointer-events: none; }
.cover-coordinate-top { top: 1.2rem; left: 1.25rem; }
.cover-coordinate-bottom { right: 1.2rem; bottom: 1.15rem; color: rgba(244, 202, 88, 0.92); }
.cover-beacon { position: absolute; z-index: 3; top: 1.1rem; right: 1.15rem; display: grid; width: 0.82rem; aspect-ratio: 1; place-items: center; border: 1px solid rgba(244, 240, 223, 0.82); border-radius: 50%; background: rgba(16, 47, 55, 0.35); }
.cover-beacon i { display: block; width: 0.3rem; aspect-ratio: 1; border-radius: 50%; background: var(--signal); box-shadow: 0 0 0 0.22rem rgba(201, 154, 66, 0.18); animation: beacon-pulse 2.8s ease-out infinite; }
.cover-beacon b { position: absolute; inset: -0.35rem; border: 1px solid rgba(201, 154, 66, 0.38); border-radius: 50%; animation: beacon-ring 2.8s ease-out infinite; }
@media (hover: hover) and (pointer: fine) {
  .article-hero-visual:hover .cover-frame, .article-hero-visual:focus-within .cover-frame { box-shadow: 1.1rem 1.3rem 0 rgba(16, 47, 55, 0.13), 0 1.8rem 3.2rem rgba(20, 52, 57, 0.22); transform: rotate(0deg) translateY(-0.3rem); }
  .article-hero-visual:hover .article-hero-cover, .article-hero-visual:focus-within .article-hero-cover { filter: saturate(1.08) contrast(1.05); transform: scale(1.025); }
}

.article-reading-layout { position: relative; z-index: 1; display: grid; grid-template-columns: minmax(10rem, 14rem) minmax(0, 56rem); gap: clamp(2rem, 5vw, 4.5rem); width: min(1130px, calc(100% - 3rem)); margin: 0 auto; padding: 2.4rem 0 7rem; }
.reading-rail-sticky { position: sticky; top: 6.4rem; display: grid; grid-template-rows: auto minmax(0, 1fr); gap: 1.55rem; max-height: calc(100vh - 8rem); }
.reading-gauge { display: flex; gap: 0.85rem; align-items: center; }
.reading-gauge p { margin: 0; color: #8a9996; font-family: "Noto Sans SC", sans-serif; font-size: 0.54rem; line-height: 1.5; letter-spacing: 0.13em; }
.reading-gauge-ring { position: relative; display: flex; align-items: baseline; justify-content: center; width: 3.8rem; aspect-ratio: 1; border-radius: 50%; background: conic-gradient(var(--current) var(--reading-progress), rgba(24, 49, 56, 0.09) 0); }
.reading-gauge-ring::before { content: ""; position: absolute; inset: 3px; border-radius: inherit; background: var(--paper-soft); }
.reading-gauge-ring span, .reading-gauge-ring small { position: relative; z-index: 1; }
.reading-gauge-ring span { font-family: var(--display-font); font-size: 1.25rem; }
.reading-gauge-ring small { color: var(--current); font-family: "Noto Sans SC", sans-serif; font-size: 0.52rem; }
.article-toc { display: grid; grid-template-rows: auto minmax(0, 1fr); min-height: 0; }
.article-toc-list { min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding-right: 0.45rem; scrollbar-color: rgba(35, 123, 120, 0.38) transparent; scrollbar-width: thin; }
.article-toc-list::-webkit-scrollbar { width: 4px; }
.article-toc-list::-webkit-scrollbar-thumb { border-radius: 999px; background: rgba(35, 123, 120, 0.38); }
.article-toc-list::-webkit-scrollbar-track { background: transparent; }
.article-toc > p { margin: 0 0 0.75rem; color: #7d8b88; font-family: "Noto Sans SC", sans-serif; font-size: 0.66rem; font-weight: 700; letter-spacing: 0.04em; }
.article-toc button { position: relative; display: grid; grid-template-columns: 1.65rem minmax(0, 1fr); gap: 0.45rem; width: 100%; padding: 0.5rem 0.4rem 0.5rem 0; border: 0; color: #6f807f; background: transparent; font-family: "Noto Sans SC", sans-serif; font-size: 0.74rem; line-height: 1.5; text-align: left; cursor: pointer; transition: color 0.2s ease, transform 0.2s ease; }
.article-toc button::before { content: ""; position: absolute; top: 50%; left: -1.1rem; width: 0.42rem; height: 0.42rem; border: 1px solid currentColor; border-radius: 50%; opacity: 0; transform: translateY(-50%) scale(0.45); transition: opacity 0.25s ease, transform 0.25s ease; }
.article-toc button span { color: rgba(35, 123, 120, 0.58); font-size: 0.58rem; }
.article-toc button:hover, .article-toc button:focus-visible, .article-toc button.active { color: var(--ink); transform: translateX(0.18rem); }
.article-toc button.active::before { color: var(--current); opacity: 1; transform: translateY(-50%) scale(1); box-shadow: none; }
.article-toc button.level-3 { padding-left: 1.1rem; font-size: 0.67rem; }
.article-toc-empty { display: flex; gap: 0.65rem; align-items: center; color: #8a9996; font-family: "Noto Sans SC", sans-serif; font-size: 0.65rem; }
.article-toc-empty span { width: 2.5rem; height: 1px; background: rgba(35, 123, 120, 0.32); }
.article-document { min-width: 0; padding: clamp(0.7rem, 2vw, 1.4rem) 0 0; border: 0; border-radius: 0; background: transparent; box-shadow: none; }
.document-scrollbar { position: fixed; z-index: 19; top: 7.4rem; right: 1.15rem; bottom: 2rem; width: 0.68rem; border: 1px solid rgba(35, 123, 120, 0.18); border-radius: 999px; background: rgba(255, 252, 246, 0.72); cursor: ns-resize; touch-action: none; }
.document-scrollbar::before, .document-scrollbar::after { content: ""; position: absolute; right: 50%; width: 0.18rem; height: 0.18rem; border: 1px solid rgba(182, 128, 34, 0.5); border-radius: 50%; transform: translateX(50%); }
.document-scrollbar::before { top: -0.7rem; }
.document-scrollbar::after { bottom: -0.7rem; }
.document-scrollbar-thumb { position: absolute; right: 1px; left: 1px; display: block; min-height: 3.25rem; border-radius: inherit; background: linear-gradient(180deg, var(--signal), var(--current)); box-shadow: 0 0 0.55rem rgba(35, 123, 120, 0.22); transition: background 0.2s ease, box-shadow 0.2s ease; }
.document-scrollbar:hover .document-scrollbar-thumb, .document-scrollbar:focus-visible .document-scrollbar-thumb { background: linear-gradient(180deg, #d49628, #2a918c); box-shadow: 0 0 0.8rem rgba(182, 128, 34, 0.32); }
.document-header { display: flex; justify-content: space-between; gap: 1rem; align-items: flex-end; margin-bottom: 1.7rem; padding-bottom: 0.8rem; border-bottom: 1px solid var(--line); font-family: "Noto Sans SC", sans-serif; }
.document-header p { margin: 0; color: #7d8b88; font-size: 0.67rem; font-weight: 700; letter-spacing: 0.08em; }
.document-header div { display: flex; flex-wrap: wrap; gap: 0.5rem 1rem; justify-content: flex-end; color: #7d8c89; font-size: 0.62rem; }

.markdown-body { min-width: 0; color: #283f43; font-family: "Noto Sans SC", sans-serif; font-size: 1.03rem; line-height: 1.95; overflow-wrap: anywhere; }
.markdown-body.motion-ready > :deep(*) { opacity: 0; transform: translateY(0.8rem); }
.markdown-body.motion-ready > :deep(.is-visible) { opacity: 1; transform: translateY(0); transition: opacity 0.52s var(--reveal-delay) ease, transform 0.52s var(--reveal-delay) cubic-bezier(0.2, 0.76, 0.26, 1); }
.markdown-body :deep(h1) { margin: 0 0 1.7rem; color: var(--ink); font-family: "Noto Sans SC", sans-serif; font-size: clamp(1.8rem, 3.4vw, 2.8rem); font-weight: 800; line-height: 1.26; }
.markdown-body :deep(h1:first-child) { display: none; }
.markdown-body :deep(h2), .markdown-body :deep(h3) { scroll-margin-top: 7rem; color: var(--ink); font-family: "Noto Sans SC", sans-serif; line-height: 1.35; }
.markdown-body :deep(h2) { position: relative; margin: 3.6rem 0 1.1rem; padding-top: 1rem; border-top: 1px solid rgba(39, 111, 109, 0.15); font-size: clamp(1.45rem, 2.4vw, 2rem); font-weight: 800; }
.markdown-body :deep(h2)::before { content: ""; position: absolute; top: -1px; left: 0; width: 4.2rem; height: 1px; background: var(--current); }
.markdown-body :deep(h3) { margin: 2.55rem 0 0.8rem; font-size: 1.25rem; font-weight: 800; }
.markdown-body :deep(p) { margin: 1.2rem 0; }
.markdown-body :deep(a) { color: var(--current); text-decoration-color: rgba(35, 123, 120, 0.34); text-underline-offset: 0.28em; }
.markdown-body :deep(a):hover { color: #155d5b; }
.markdown-body :deep(strong) { color: #10292f; }
.markdown-body :deep(hr) { height: 1px; margin: 4rem 0; border: 0; background: linear-gradient(90deg, transparent, rgba(35, 123, 120, 0.28), transparent); }
.markdown-body :deep(img), .markdown-body :deep(blockquote), .markdown-body :deep(pre), .markdown-body :deep(.md-code), .markdown-body :deep(table) { box-sizing: border-box; max-width: 100%; }
.markdown-body :deep(img) { display: block; height: auto; margin: 2.4rem auto; border: 1px solid rgba(24, 49, 56, 0.1); border-radius: 4px; box-shadow: 0 0.8rem 2rem rgba(31, 54, 55, 0.1); cursor: zoom-in; transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease; }
.markdown-body :deep(img:hover) { border-color: rgba(39, 111, 109, 0.3); box-shadow: 0 1rem 2.2rem rgba(31, 54, 55, 0.12); transform: translateY(-0.08rem); }
.markdown-body :deep(img:focus-visible) { outline: 2px solid var(--signal); outline-offset: 0.35rem; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 1.5rem; }
.markdown-body :deep(li) { margin: 0.55rem 0; padding-left: 0.35rem; }
.markdown-body :deep(li)::marker { color: var(--current); }
.markdown-body :deep(blockquote) { position: relative; width: 100%; margin: 2.4rem 0; padding: 1.1rem 1.35rem 1.1rem 1.5rem; border: 0; border-left: 1px solid var(--current); color: #52686a; background: rgba(39, 111, 109, 0.055); overflow-wrap: anywhere; word-break: break-word; }
.markdown-body :deep(blockquote)::before { display: none; }
.markdown-body :deep(blockquote p) { margin: 0; overflow-wrap: anywhere; word-break: break-word; }
.markdown-body :deep(code) { padding: 0.12rem 0.35rem; border: 1px solid rgba(39, 111, 109, 0.16); border-radius: 3px; color: #285c5a; background: rgba(39, 111, 109, 0.07); font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace; font-size: 0.9em; }
.markdown-body :deep(pre:not([class])) { position: relative; overflow-x: auto; margin: 2.25rem 0; padding: 2.5rem 1.35rem 1.35rem; border: 1px solid rgba(39, 111, 109, 0.14); border-radius: 4px; color: #e7f2e8; background: #16363b; box-shadow: 0 0.9rem 2rem rgba(31, 54, 55, 0.12); }
.markdown-body :deep(pre:not([class]))::before { content: "CODE"; position: absolute; top: 0.72rem; left: 1.3rem; color: rgba(214, 229, 222, 0.66); font-size: 0.55rem; letter-spacing: 0.08em; }
.markdown-body :deep(pre:not([class]) code) { padding: 0; border: 0; color: inherit; background: transparent; }
/* mac 风格代码卡片：对齐后台编辑预览，用浅色代码区降低长文阅读疲劳。 */
.markdown-body :deep(.md-code) { margin: 2.25rem 0; overflow: hidden; border: 1px solid #d6ddd9; border-radius: 6px; color: #24292e; background: #f8faf8; box-shadow: 0 0.75rem 1.8rem rgba(31, 54, 55, 0.09); font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace; font-size: 0.85rem; }
.markdown-body :deep(.md-code-head) { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 0.55rem 0.9rem; border-bottom: 1px solid #dce2df; background: #f0f3f1; }
.markdown-body :deep(.md-code-dots) { display: inline-flex; gap: 0.42rem; }
.markdown-body :deep(.md-code-dots i) { width: 0.72rem; aspect-ratio: 1; border: 1px solid rgba(27, 31, 36, 0.14); border-radius: 50%; }
.markdown-body :deep(.md-code-dots i:nth-child(1)) { background: #d98570; }
.markdown-body :deep(.md-code-dots i:nth-child(2)) { background: #d9b768; }
.markdown-body :deep(.md-code-dots i:nth-child(3)) { background: #71a99c; }
.markdown-body :deep(.md-code-meta) { display: inline-flex; gap: 0.85rem; align-items: center; }
.markdown-body :deep(.md-code-lang) { color: #656d76; font-size: 0.75rem; font-weight: 600; line-height: 1; }
.markdown-body :deep(.md-code-copy) { display: inline-flex; gap: 0.35rem; align-items: center; padding: 0.28rem 0.5rem; border: 0; border-radius: 5px; color: #57606a; background: transparent; font-family: "Noto Sans SC", sans-serif; font-size: 0.75rem; line-height: 1; cursor: pointer; transition: color 0.18s ease, background-color 0.18s ease; }
.markdown-body :deep(.md-code-copy svg) { width: 0.9rem; height: 0.9rem; }
.markdown-body :deep(.md-code-copy:hover) { color: #1f2328; background: rgba(31, 35, 40, 0.08); }
.markdown-body :deep(.md-code-copy:focus-visible) { color: #1f2328; background: rgba(31, 35, 40, 0.08); outline: 2px solid #0969da; outline-offset: 1px; }
.markdown-body :deep(.md-code-copy.is-copied) { color: #1a7f37; }
.markdown-body :deep(.md-code-copy.is-failed) { color: #cf222e; }
/* 行号列与代码列共用字号和行高，两条 pre 各自的行保持单行高度，编号自然对齐 */
.markdown-body :deep(.md-code-body) { display: flex; overflow-x: auto; scrollbar-color: rgba(101, 109, 118, 0.45) transparent; scrollbar-width: thin; }
.markdown-body :deep(.md-code-lines), .markdown-body :deep(.md-code-content) { margin: 0; padding: 0.9rem 0; font-family: inherit; font-size: inherit; line-height: 1.65; font-variant-numeric: tabular-nums; white-space: pre; }
.markdown-body :deep(.md-code-lines) { position: sticky; left: 0; z-index: 1; flex-shrink: 0; padding-right: 0.9rem; padding-left: 1.05rem; color: #8c959f; background: #f8faf8; text-align: right; user-select: none; }
.markdown-body :deep(.md-code-content) { flex: 1 0 auto; padding-right: 1.1rem; padding-left: 1rem; }
.markdown-body :deep(.md-code code) { padding: 0; border: 0; color: inherit; background: transparent; font-size: inherit; }
.markdown-body :deep(.md-code) ::selection { color: #1f2328; background: rgba(9, 105, 218, 0.22); }
/* highlight.js 的 github 浅色主题配色，与后台编辑器预览保持一致 */
.markdown-body :deep(.md-code .hljs-doctag), .markdown-body :deep(.md-code .hljs-keyword), .markdown-body :deep(.md-code .hljs-meta .hljs-keyword), .markdown-body :deep(.md-code .hljs-template-tag), .markdown-body :deep(.md-code .hljs-template-variable), .markdown-body :deep(.md-code .hljs-type), .markdown-body :deep(.md-code .hljs-variable.language_) { color: #d73a49; }
.markdown-body :deep(.md-code .hljs-title), .markdown-body :deep(.md-code .hljs-title.class_), .markdown-body :deep(.md-code .hljs-title.class_.inherited__), .markdown-body :deep(.md-code .hljs-title.function_) { color: #6f42c1; }
.markdown-body :deep(.md-code .hljs-attr), .markdown-body :deep(.md-code .hljs-attribute), .markdown-body :deep(.md-code .hljs-literal), .markdown-body :deep(.md-code .hljs-meta), .markdown-body :deep(.md-code .hljs-number), .markdown-body :deep(.md-code .hljs-operator), .markdown-body :deep(.md-code .hljs-selector-attr), .markdown-body :deep(.md-code .hljs-selector-class), .markdown-body :deep(.md-code .hljs-selector-id), .markdown-body :deep(.md-code .hljs-variable) { color: #005cc5; }
.markdown-body :deep(.md-code .hljs-meta .hljs-string), .markdown-body :deep(.md-code .hljs-regexp), .markdown-body :deep(.md-code .hljs-string) { color: #032f62; }
.markdown-body :deep(.md-code .hljs-built_in), .markdown-body :deep(.md-code .hljs-symbol) { color: #e36209; }
.markdown-body :deep(.md-code .hljs-code), .markdown-body :deep(.md-code .hljs-comment), .markdown-body :deep(.md-code .hljs-formula) { color: #6a737d; font-style: italic; }
.markdown-body :deep(.md-code .hljs-name), .markdown-body :deep(.md-code .hljs-quote), .markdown-body :deep(.md-code .hljs-selector-pseudo), .markdown-body :deep(.md-code .hljs-selector-tag) { color: #22863a; }
.markdown-body :deep(.md-code .hljs-subst) { color: #24292e; }
.markdown-body :deep(.md-code .hljs-section) { color: #005cc5; font-weight: 700; }
.markdown-body :deep(.md-code .hljs-bullet) { color: #735c0f; }
.markdown-body :deep(.md-code .hljs-addition) { color: #22863a; background-color: #f0fff4; }
.markdown-body :deep(.md-code .hljs-deletion) { color: #b31d28; background-color: #ffeef0; }
.markdown-body :deep(table) { width: 100%; margin: 2.5rem 0; border-collapse: collapse; font-size: 0.9rem; }
.markdown-body :deep(th), .markdown-body :deep(td) { padding: 0.8rem; border-bottom: 1px solid var(--line); text-align: left; }
.markdown-body :deep(th) { color: var(--signal); font-weight: 500; }

.article-source { margin: 3.5rem 0 0; padding: 0.85rem 1rem; border-left: 1px solid var(--current); color: #657879; background: rgba(39, 111, 109, 0.055); font-family: "Noto Sans SC", sans-serif; font-size: 0.78rem; }
.article-source a { color: var(--current); }
.article-detail-footer { display: flex; align-items: center; justify-content: space-between; gap: 1.5rem; margin-top: 5rem; padding-top: 2rem; border-top: 1px solid var(--line); }
.article-detail-tags { display: flex; flex-wrap: wrap; gap: 0.55rem; }
.article-detail-tags a { padding: 0.38rem 0; color: var(--current); font-family: "Noto Sans SC", sans-serif; font-size: 0.75rem; text-decoration: none; transition: color 180ms ease, transform 140ms cubic-bezier(0.22, 1, 0.36, 1); }
.article-like-area { display: grid; justify-items: end; gap: 0.45rem; }
.article-like-area small { color: #a55e48; font-family: "Noto Sans SC", sans-serif; font-size: 0.68rem; }
.article-like-button { display: grid; grid-template-columns: auto auto auto; gap: 0.65rem; align-items: center; min-height: 2.9rem; padding: 0.6rem 0.85rem; border: 1px solid rgba(179, 95, 72, 0.42); border-radius: 4px; color: #9b5845; background: rgba(179, 95, 72, 0.055); font-family: "Noto Sans SC", sans-serif; cursor: pointer; transition: color 0.2s ease, background-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease; }
.article-like-button strong { min-width: 2rem; padding-left: 0.65rem; border-left: 1px solid rgba(223, 123, 89, 0.32); color: var(--ink); }
.article-like-button:hover:not(:disabled), .article-like-button:focus-visible { color: #783c29; background: rgba(179, 95, 72, 0.1); box-shadow: 0 0.5rem 1.2rem rgba(179, 95, 72, 0.1); transform: translateY(-0.1rem); }
.article-like-button:disabled { cursor: wait; opacity: 0.72; }
.article-like-button.is-liked { border-color: rgba(35, 123, 120, 0.42); color: var(--current); background: rgba(35, 123, 120, 0.08); cursor: default; opacity: 1; }
.article-like-button.is-liked .like-symbol { color: var(--current); }
.article-like-button.celebrated .like-symbol { animation: like-burst 0.72s cubic-bezier(0.2, 0.76, 0.26, 1); }
.like-symbol { color: var(--coral); font-size: 1rem; }
.article-share-panel { display: flex; justify-content: space-between; gap: 1.5rem; align-items: center; margin-top: 1.2rem; padding: 1.1rem; border: 1px solid rgba(39, 111, 109, 0.12); border-radius: 6px; background: rgba(255, 250, 242, 0.48); }
.article-share-panel p { margin: 0 0 0.25rem; color: #7d8b88; font: 700 0.65rem "Noto Sans SC", sans-serif; letter-spacing: 0.04em; }
.article-share-panel span { color: var(--muted); font: 500 0.74rem "Noto Sans SC", sans-serif; }
.article-share-panel > div:last-child { display: flex; gap: 0.55rem; }
.article-share-panel button { min-width: 6.8rem; padding: 0.58rem 0.8rem; border: 1px solid rgba(35, 123, 120, 0.24); border-radius: 5px; color: var(--ink); background: rgba(255, 252, 246, 0.68); font: 700 0.72rem "Noto Sans SC", sans-serif; cursor: pointer; touch-action: manipulation; transition: transform 140ms cubic-bezier(0.22, 1, 0.36, 1), color 150ms ease, background-color 150ms ease; }
.article-share-panel button.confirmed { color: #fffaf0; background: var(--current); }
.article-share-panel button:active { transform: scale(0.97); transition-duration: 0s; }
.article-continuation { display: grid; gap: 1rem; margin-top: 4rem; }
.article-series-link { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 1rem; align-items: center; padding: 1rem 1.2rem; border: 1px solid rgba(159, 122, 49, 0.18); border-radius: 6px; color: var(--ink); background: rgba(159, 122, 49, 0.045); text-decoration: none; transition: transform 160ms cubic-bezier(0.22, 1, 0.36, 1), border-color 180ms ease; }
.article-series-link span, .article-series-link i { color: var(--signal); font: 700 0.68rem "Noto Sans SC", sans-serif; }
.article-series-link i { font-style: normal; }
.article-adjacent-links { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.8rem; }
.article-adjacent-links a { display: grid; gap: 0.45rem; min-height: 6.8rem; padding: 1rem; border: 1px solid var(--line); border-radius: 6px; color: var(--ink); background: rgba(255, 252, 246, 0.5); text-decoration: none; transition: transform 160ms cubic-bezier(0.22, 1, 0.36, 1), border-color 180ms ease, background-color 180ms ease; }
.article-adjacent-links a:last-child { text-align: right; }
.article-adjacent-links span { color: var(--current); font: 700 0.68rem "Noto Sans SC", sans-serif; }
.article-adjacent-links strong { font-family: var(--display-font); font-size: 1.05rem; }
.related-articles { margin-top: 1.4rem; }
.related-articles > p { margin: 0 0 0.8rem; color: var(--signal); font: 700 0.66rem "IBM Plex Mono", monospace; }
.related-articles > div { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.7rem; }
.related-articles a { display: grid; align-content: start; gap: 0.45rem; min-height: 9rem; padding: 1rem; border: 1px solid rgba(35, 123, 120, 0.14); border-radius: 6px; color: var(--ink); background: rgba(35, 123, 120, 0.045); text-decoration: none; transition: transform 160ms cubic-bezier(0.22, 1, 0.36, 1), border-color 180ms ease; }
.related-articles a span { color: var(--current); font-size: 0.66rem; }
.related-articles a strong { font-family: var(--display-font); font-size: 1rem; }
.related-articles a small { display: -webkit-box; overflow: hidden; color: var(--muted); line-height: 1.6; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.article-detail-error button { padding: 0.65rem 0.9rem; border: 1px solid rgba(35, 123, 120, 0.26); border-radius: 5px; color: var(--ink); background: rgba(35, 123, 120, 0.08); cursor: pointer; }
@media (hover: hover) and (pointer: fine) {
  .article-detail-tags a:hover, .article-detail-tags a:focus-visible { color: var(--signal); transform: translateY(-0.1rem); }
  .article-series-link:hover, .article-series-link:focus-visible, .article-adjacent-links a:hover, .article-adjacent-links a:focus-visible, .related-articles a:hover, .related-articles a:focus-visible { border-color: rgba(182, 128, 34, 0.36); transform: translateY(-0.18rem); }
  .article-adjacent-links a:hover, .article-adjacent-links a:focus-visible { background-color: rgba(35, 123, 120, 0.06); }
}
.document-end { display: flex; gap: 1rem; align-items: center; margin-top: 5rem; color: rgba(23, 47, 53, 0.32); font-family: "Noto Sans SC", sans-serif; font-size: 0.55rem; letter-spacing: 0.16em; }
.document-end i { flex: 1; height: 1px; background: linear-gradient(90deg, transparent, rgba(35, 123, 120, 0.24)); }
.document-end i:last-child { transform: scaleX(-1); }

.article-image-preview { --signal: #f4ca58; --current: #75c9bd; position: fixed; z-index: 80; inset: 0; display: grid; place-items: center; padding: clamp(1rem, 4vw, 3rem); background: radial-gradient(circle at 74% 18%, rgba(244, 202, 88, 0.1), transparent 21rem), rgba(3, 15, 22, 0.88); backdrop-filter: blur(0.7rem); }
.article-image-preview::before { content: ""; position: absolute; inset: clamp(0.7rem, 2vw, 1.35rem); border: 1px solid rgba(117, 201, 189, 0.22); pointer-events: none; }
.article-image-preview figure { position: relative; display: grid; max-width: min(92vw, 86rem); max-height: min(86vh, 54rem); margin: 0; }
.article-image-preview img { display: block; max-width: 100%; max-height: calc(86vh - 3rem); border: 1px solid rgba(244, 240, 223, 0.18); border-radius: 4px; object-fit: contain; box-shadow: 0 2rem 6rem rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(117, 201, 189, 0.08); }
.article-image-preview figcaption { justify-self: center; max-width: min(100%, 52rem); margin-top: 0.85rem; color: rgba(244, 240, 223, 0.68); font-family: "Noto Sans SC", sans-serif; font-size: 0.78rem; line-height: 1.6; text-align: center; }
.image-preview-close { position: fixed; top: clamp(1.1rem, 3vw, 2rem); right: clamp(1.1rem, 3vw, 2rem); z-index: 1; display: grid; width: 2.75rem; aspect-ratio: 1; place-items: center; border: 1px solid rgba(244, 202, 88, 0.54); border-radius: 50%; color: var(--signal); background: rgba(5, 25, 35, 0.78); font-size: 1.55rem; line-height: 1; cursor: pointer; transition: color 0.2s ease, border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease; }
.image-preview-close:hover, .image-preview-close:focus-visible { color: #fff9e9; border-color: rgba(117, 201, 189, 0.72); box-shadow: 0 0 1.4rem rgba(117, 201, 189, 0.22); transform: rotate(6deg) scale(1.04); }
.image-preview-enter-active, .image-preview-leave-active { transition: opacity 0.22s ease; }
.image-preview-enter-active figure, .image-preview-leave-active figure { transition: transform 0.22s cubic-bezier(0.22, 1, 0.36, 1); }
.image-preview-enter-from, .image-preview-leave-to { opacity: 0; }
.image-preview-enter-from figure, .image-preview-leave-to figure { transform: translateY(0.8rem) scale(0.985); }

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
@keyframes cover-entry { from { opacity: 0; transform: translate3d(1.8rem, 0, 0); } to { opacity: 1; transform: translate3d(0, 0, 0); } }
@keyframes beacon-pulse { 0%, 100% { box-shadow: 0 0 0 0.18rem rgba(201, 154, 66, 0.2); } 52% { box-shadow: 0 0 0 0.5rem rgba(201, 154, 66, 0); } }
@keyframes beacon-ring { 0%, 100% { opacity: 0.8; transform: scale(0.9); } 65% { opacity: 0; transform: scale(1.35); } }
@keyframes like-burst { 0%, 100% { transform: scale(1); } 42% { color: var(--signal); transform: scale(1.8) rotate(-10deg); filter: drop-shadow(0 0 0.5rem rgba(244, 202, 88, 0.7)); } }
@keyframes radar-sweep { to { transform: rotate(360deg); } }

@media (max-width: 900px) {
  .article-hero { padding-top: 6.2rem; }
  .article-hero-inner { grid-template-columns: 1fr; }
  .article-hero-visual { justify-items: start; min-height: 19rem; margin-top: 0.8rem; }
  .cover-frame { width: min(100%, 30rem); }
  .cover-route-line { display: none; }
  .article-reading-layout { grid-template-columns: 1fr; width: min(56rem, calc(100% - 3rem)); padding-top: 2rem; }
  .reading-rail { display: none; }
  .document-scrollbar { right: 0.55rem; }
}

@media (max-width: 600px) {
  .article-hero { padding: 7.05rem 1rem 1.25rem; }
  .article-back-link { margin-bottom: 1rem; }
  .article-hero h1 { font-size: clamp(1.9rem, 8.5vw, 3rem); }
  .article-summary { font-size: 0.96rem; }
  .article-manifest { grid-template-columns: repeat(2, minmax(0, 1fr)); margin-top: 1.15rem; }
  .article-hero-visual { min-height: 0; margin-top: 1.4rem; }
  .cover-frame { width: 100%; padding: 0.62rem; transform: rotate(0.8deg); }
  .cover-frame::before { inset: 0.42rem -0.35rem -0.4rem 0.35rem; }
  .cover-grid { inset: 0.62rem; background-size: 1.3rem 1.3rem; }
  .cover-coordinate { font-size: 0.5rem; }
  .cover-coordinate-top { top: 0.95rem; left: 0.95rem; }
  .cover-coordinate-bottom { right: 0.95rem; bottom: 0.88rem; }
  .cover-beacon { top: 0.82rem; right: 0.85rem; }
  .article-reading-layout { width: calc(100% - 2rem); padding: 1.45rem 0 5rem; }
  .article-document { padding: 0; }
  .document-header { align-items: flex-start; flex-direction: column; }
  .document-header div { justify-content: flex-start; }
  .markdown-body { font-size: 0.98rem; line-height: 1.9; }
  .markdown-body :deep(h2) { margin-top: 3.3rem; }
  .markdown-body :deep(blockquote) { padding: 1rem 1rem 1rem 1.25rem; }
  .markdown-body :deep(blockquote p) { word-break: break-all; }
  .markdown-body :deep(pre:not([class])) { margin-inline: -0.35rem; padding-inline: 1rem; }
  .markdown-body :deep(.md-code-body) { font-size: 0.8rem; }
  .article-detail-footer { align-items: stretch; flex-direction: column; }
  .article-like-area { justify-items: stretch; }
  .article-like-button { justify-content: center; }
  .document-end { gap: 0.55rem; }
  .article-share-panel { align-items: stretch; flex-direction: column; }
  .article-share-panel > div:last-child { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .article-series-link { grid-template-columns: 1fr; gap: 0.35rem; }
  .article-adjacent-links, .related-articles > div { grid-template-columns: 1fr; }
  .article-adjacent-links a:last-child { text-align: left; }
  .document-end span { letter-spacing: 0.08em; white-space: nowrap; }
  .document-scrollbar { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  .chart-route-flow, .chart-orbit, .hero-heading, .article-manifest, .article-hero-visual, .cover-beacon i, .cover-beacon b, .article-like-button.celebrated .like-symbol, .state-radar::before { animation: none; }
  .markdown-body.motion-ready > :deep(*) { opacity: 1; transform: none; transition: none; }
  .article-detail-tags a, .article-share-panel button, .article-series-link, .article-adjacent-links a, .related-articles a, .cover-frame, .article-hero-cover { transition: none; }
  .reading-progress span, .article-toc button, .article-back-link, .article-like-button { transition: none; }
}
</style>
