<script setup lang="ts">
import {
  computed,
  nextTick,
  onActivated,
  onBeforeUnmount,
  onDeactivated,
  onMounted,
  ref,
  watch,
} from "vue";
import { onBeforeRouteLeave, useRoute } from "vue-router";

import { fetchArticles, type Article, type ArticleListStats } from "../api/articles";
import { fetchSiteSettings, type SiteSettings, type VisualAssetItem } from "../api/site-settings";

type ArticleView = "archive" | "tags" | "categories";

const route = useRoute();
const articles = ref<Article[]>([]);
const loading = ref(true);
const loadingMore = ref(false);
const errorText = ref("");
const loadMoreError = ref("");
const activeCategory = ref("");
const activeTag = ref("");
const pageRoot = ref<HTMLElement | null>(null);
const loadMoreSentinel = ref<HTMLElement | null>(null);
const visibleArticleIds = ref<Set<number>>(new Set());
const showBackToTop = ref(false);
const archiveVisualAssets = ref<VisualAssetItem[]>([]);
const activeVisualAssetIndex = ref(0);
let revealFrame: number | undefined;
let visualAssetTimer: number | undefined;
let savedScrollY = 0;
let hasBeenDeactivated = false;
let pageObserver: IntersectionObserver | undefined;
let pageIsActive = false;
const pageSize = 20;
const visualAssetRotationMs = 6000;
const currentPage = ref(0);
const totalArticles = ref(0);
const allPagesLoaded = ref(false);
const articleStats = ref<ArticleListStats>(createEmptyArticleStats());
const views: Array<{ key: ArticleView; label: string; caption: string }> = [
  { key: "archive", label: "全部文章", caption: "按发表时间回看全部记录" },
  { key: "tags", label: "标签", caption: "沿主题找到相关记录" },
  { key: "categories", label: "分类", caption: "从内容方向切入阅读" },
];

const currentView = computed<ArticleView>(() => {
  const view = route.query.view;
  return view === "tags" || view === "categories" ? view : "archive";
});
const pageTitle = computed(
  () => views.find((view) => view.key === currentView.value)?.label ?? "全部文章",
);
const pageCaption = computed(
  () => views.find((view) => view.key === currentView.value)?.caption ?? "按发表时间回看全部记录",
);
const categories = computed(() => articleStats.value.categories.map((category) => category.name));
const tags = computed(() => articleStats.value.tags.map((tag) => tag.name).slice(0, 16));
const categoryCountMap = computed(() =>
  new Map(articleStats.value.categories.map((category) => [category.name, category.count])),
);
const allArticleTotal = computed(() =>
  articleStats.value.categories.reduce((total, category) => total + category.count, 0) || totalArticles.value,
);
const tagCountMap = computed(() =>
  new Map(articleStats.value.tags.map((tag) => [tag.name, tag.count])),
);
const monthCountMap = computed(() =>
  new Map(articleStats.value.months.map((month) => [month.key, month.count])),
);
const publishedYears = computed(
  () => new Set(articleStats.value.months.map((month) => Number(month.key.slice(0, 4)))).size,
);
const hasMoreArticles = computed(() => !allPagesLoaded.value && articles.value.length < totalArticles.value);
const archiveVisualStyle = computed(() => {
  if (!archiveVisualAssets.value.length) {
    return {
      "--archive-visual-opacity": "0",
    };
  }
  return {
    "--archive-visual-opacity": "1",
  };
});
const routeMarkers = computed(() =>
  Array.from({ length: Math.max(8, Math.ceil(articles.value.length / 8)) }, (_, index) => ({
    id: index + 1,
    top: `${42 + index * 86}rem`,
    side: index % 2 === 0 ? "left" : "right",
    label: String(index + 1).padStart(2, "0"),
  })),
);

function archiveDate(article: Article) {
  return article.published_at ?? article.created_at;
}

const visibleArticles = computed(() => {
  return articles.value
    .filter(
      (article) =>
        (!activeCategory.value || article.category === activeCategory.value) &&
        (!activeTag.value || article.tags.includes(activeTag.value)),
    )
    .sort(
      (left, right) =>
        Date.parse(archiveDate(right)) - Date.parse(archiveDate(left)) || right.id - left.id,
    );
});
const archiveGroups = computed(() => {
  const groups = new Map<string, Article[]>();
  visibleArticles.value.forEach((article) => {
    const date = new Date(archiveDate(article));
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
    groups.set(key, [...(groups.get(key) ?? []), article]);
  });
  return [...groups.entries()].map(([key, entries]) => ({
    key,
    entries,
    total: monthCountMap.value.get(key) ?? entries.length,
    label: new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "long" }).format(
      new Date(`${key}-01T12:00:00`),
    ),
  }));
});

function createEmptyArticleStats(): ArticleListStats {
  return {
    categories: [],
    tags: [],
    months: [],
  };
}

function getArticleQueryParams(page: number) {
  return {
    page,
    page_size: pageSize,
    category: activeCategory.value || undefined,
    tag: activeTag.value || undefined,
  };
}

function formatDay(value: string) {
  return new Intl.DateTimeFormat("zh-CN", { month: "2-digit", day: "2-digit" })
    .format(new Date(value))
    .replace("/", ".");
}

function formatFullDate(value: string | null) {
  if (!value) return "时间待定";
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(value));
}

function clearFilters() {
  activeCategory.value = "";
  activeTag.value = "";
  void loadArticles();
}

function syncFiltersFromRoute() {
  activeTag.value = typeof route.query.tag === "string" ? route.query.tag : "";
  activeCategory.value = typeof route.query.category === "string" ? route.query.category : "";
}

function selectCategory(category: string) {
  activeCategory.value = category;
  activeTag.value = "";
  void loadArticles();
}

function selectTag(tag: string) {
  activeTag.value = tag;
  activeCategory.value = "";
  void loadArticles();
}

function getVisualAssetLayerStyle(asset: VisualAssetItem) {
  const visualOpacity = Number.isFinite(asset.opacity) ? asset.opacity : 0.68;
  return {
    "--archive-visual-image": `url("${asset.image_url.replace(/"/g, "%22")}")`,
    "--archive-visual-layer-opacity": String(Math.min(0.88, Math.max(0, visualOpacity * 0.82))),
  };
}

function pickArchiveVisualAssets(settings: SiteSettings) {
  const enabledAssets = settings.visual_assets.filter(
    (asset) => asset.enabled && asset.image_url && asset.usage === "background",
  );
  const seenAssets = new Set<string>();
  const uniqueAssets = enabledAssets.filter((asset) => {
    const identity = `${asset.key}:${asset.image_url}`;
    if (seenAssets.has(identity)) return false;
    seenAssets.add(identity);
    return true;
  });
  const shuffledAssets = [...uniqueAssets];

  for (let index = shuffledAssets.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [shuffledAssets[index], shuffledAssets[swapIndex]] = [
      shuffledAssets[swapIndex],
      shuffledAssets[index],
    ];
  }

  return shuffledAssets;
}

function shouldRotateVisualAssets() {
  return (
    archiveVisualAssets.value.length > 1 &&
    !window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

function stopVisualAssetRotation() {
  if (visualAssetTimer === undefined) return;
  window.clearInterval(visualAssetTimer);
  visualAssetTimer = undefined;
}

function startVisualAssetRotation() {
  stopVisualAssetRotation();
  if (!shouldRotateVisualAssets()) return;

  visualAssetTimer = window.setInterval(() => {
    activeVisualAssetIndex.value = (activeVisualAssetIndex.value + 1) % archiveVisualAssets.value.length;
  }, visualAssetRotationMs);
}

function handleVisualAssetVisibilityChange() {
  if (document.hidden) {
    stopVisualAssetRotation();
    return;
  }
  startVisualAssetRotation();
}

async function loadVisualAsset() {
  try {
    const settings = await fetchSiteSettings();
    archiveVisualAssets.value = pickArchiveVisualAssets(settings);
    activeVisualAssetIndex.value = 0;
    if (archiveVisualAssets.value.length) {
      startVisualAssetRotation();
      return;
    }
  } catch {
    // Ignore visual asset loading failures and keep the fallback background.
  }
  stopVisualAssetRotation();
  archiveVisualAssets.value = [];
  activeVisualAssetIndex.value = 0;
}

async function loadArticles() {
  loading.value = true;
  errorText.value = "";
  loadMoreError.value = "";
  currentPage.value = 0;
  totalArticles.value = 0;
  articleStats.value = createEmptyArticleStats();
  allPagesLoaded.value = false;
  articles.value = [];
  try {
    const result = await fetchArticles(getArticleQueryParams(1));
    articles.value = result.items;
    currentPage.value = result.page;
    totalArticles.value = result.total;
    articleStats.value = result.stats;
    allPagesLoaded.value = result.items.length >= result.total;
    await nextTick();
    revealVisibleEntries();
  } catch {
    errorText.value = "文章航线暂时无法读取，请稍后再试。";
  } finally {
    loading.value = false;
    await nextTick();
    observeLoadMoreSentinel();
  }
}

async function loadMoreArticles() {
  if (loading.value || loadingMore.value || !hasMoreArticles.value) return;

  loadingMore.value = true;
  loadMoreError.value = "";
  try {
    const result = await fetchArticles(getArticleQueryParams(currentPage.value + 1));
    const loadedIds = new Set(articles.value.map((article) => article.id));
    const nextArticles = result.items.filter((article) => !loadedIds.has(article.id));

    articles.value = [...articles.value, ...nextArticles];
    currentPage.value = result.page;
    totalArticles.value = result.total;
    articleStats.value = result.stats;
    allPagesLoaded.value = nextArticles.length === 0 || articles.value.length >= result.total;
    await nextTick();
    revealVisibleEntries();
  } catch {
    loadMoreError.value = "后续文章暂时无法读取。";
  } finally {
    loadingMore.value = false;
  }
}

function revealVisibleEntries() {
  if (revealFrame !== undefined) return;
  revealFrame = window.requestAnimationFrame(() => {
    showBackToTop.value = window.scrollY > window.innerHeight * 0.85;
    const scrollShift = Math.min(window.scrollY * 0.045, 72);
    pageRoot.value?.style.setProperty("--archive-scroll-shift", `${scrollShift}px`);
    pageRoot.value?.style.setProperty(
      "--archive-counter-shift",
      `${Math.max(-42, scrollShift * -0.58)}px`,
    );

    const nextVisibleIds = new Set(visibleArticleIds.value);
    document.querySelectorAll<HTMLElement>("[data-archive-entry]").forEach((entry) => {
      const bounds = entry.getBoundingClientRect();
      if (bounds.top <= window.innerHeight * 0.92 && bounds.bottom >= 0) {
        nextVisibleIds.add(Number(entry.dataset.articleId));
      }
    });
    if (nextVisibleIds.size !== visibleArticleIds.value.size) {
      visibleArticleIds.value = nextVisibleIds;
    }
    revealFrame = undefined;
  });
}

function scrollToTop() {
  const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
  window.scrollTo({ top: 0, behavior });
}

function addPageListeners() {
  window.addEventListener("scroll", revealVisibleEntries, { passive: true });
  window.addEventListener("resize", handlePageResize);
}

function removePageListeners() {
  window.removeEventListener("scroll", revealVisibleEntries);
  window.removeEventListener("resize", handlePageResize);
  if (revealFrame !== undefined) {
    window.cancelAnimationFrame(revealFrame);
    revealFrame = undefined;
  }
}

function handlePageResize() {
  revealVisibleEntries();
  observeLoadMoreSentinel();
}

function observeLoadMoreSentinel() {
  pageObserver?.disconnect();
  if (!pageIsActive || !loadMoreSentinel.value || !hasMoreArticles.value) return;

  pageObserver = new IntersectionObserver(
    (entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        void loadMoreArticles();
      }
    },
    { rootMargin: "0px 0px 420px" },
  );
  pageObserver.observe(loadMoreSentinel.value);
}

onMounted(() => {
  document.addEventListener("visibilitychange", handleVisualAssetVisibilityChange);
  syncFiltersFromRoute();
  void loadArticles();
  void loadVisualAsset();
});

onActivated(async () => {
  pageIsActive = true;
  startVisualAssetRotation();
  addPageListeners();
  if (!hasBeenDeactivated) {
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
    revealVisibleEntries();
    observeLoadMoreSentinel();
    return;
  }

  await nextTick();
  window.requestAnimationFrame(() => {
    window.scrollTo({ top: savedScrollY, left: 0, behavior: "auto" });
    revealVisibleEntries();
    observeLoadMoreSentinel();
  });
});

onDeactivated(() => {
  hasBeenDeactivated = true;
  pageIsActive = false;
  pageObserver?.disconnect();
  pageObserver = undefined;
  stopVisualAssetRotation();
  removePageListeners();
});

onBeforeRouteLeave(() => {
  savedScrollY = window.scrollY;
});

watch([activeCategory, activeTag, currentView], async () => {
  await nextTick();
  revealVisibleEntries();
  observeLoadMoreSentinel();
});
watch(
  () => [route.query.tag, route.query.category],
  () => {
    syncFiltersFromRoute();
    void loadArticles();
  },
);
onBeforeUnmount(() => {
  pageObserver?.disconnect();
  document.removeEventListener("visibilitychange", handleVisualAssetVisibilityChange);
  stopVisualAssetRotation();
  removePageListeners();
});
</script>

<template>
  <div ref="pageRoot" class="article-page" :style="archiveVisualStyle">
    <div class="sea-chart-motion" aria-hidden="true">
      <span class="chart-bearing chart-bearing-one"></span>
      <span class="chart-bearing chart-bearing-two"></span>
      <span class="chart-ping"></span>
      <span class="chart-current chart-current-one"></span>
      <span class="chart-current chart-current-two"></span>
      <span class="chart-current chart-current-three"></span>
      <span class="chart-signal chart-signal-one"></span>
      <span class="chart-signal chart-signal-two"></span>
    </div>
    <div class="archive-visual-stack" aria-hidden="true">
      <div
        v-for="(asset, index) in archiveVisualAssets"
        :key="`${asset.key}-${asset.image_url}`"
        :class="['archive-visual-layer', { active: index === activeVisualAssetIndex }]"
        :style="getVisualAssetLayerStyle(asset)"
      ></div>
    </div>
    <div class="archive-route-field" aria-hidden="true">
      <svg class="archive-route-map" viewBox="0 0 1440 1900" preserveAspectRatio="xMidYMin meet">
        <path
          class="route-base route-coral"
          pathLength="100"
          d="M-120 435 C 170 265, 310 600, 585 440 S 965 170, 1180 375 S 1490 645, 1580 450"
        />
        <path
          class="route-flow route-coral"
          pathLength="100"
          d="M-120 435 C 170 265, 310 600, 585 440 S 965 170, 1180 375 S 1490 645, 1580 450"
        />
        <path
          class="route-base route-cyan"
          pathLength="100"
          d="M-160 1420 C 165 1180, 385 1515, 665 1340 S 1040 1035, 1270 1270 S 1515 1580, 1620 1370"
        />
        <path
          class="route-flow route-cyan"
          pathLength="100"
          d="M-160 1420 C 165 1180, 385 1515, 665 1340 S 1040 1035, 1270 1270 S 1515 1580, 1620 1370"
        />
        <g class="route-fix route-fix-one" transform="translate(584 440)">
          <path d="M-12 0H12M0-12V12" />
          <circle r="5" />
        </g>
        <g class="route-fix route-fix-two" transform="translate(1268 1270)">
          <path d="M-12 0H12M0-12V12" />
          <circle r="5" />
        </g>
      </svg>
      <div
        v-for="marker in routeMarkers"
        :key="marker.id"
        :class="['archive-route-marker', marker.side]"
        :style="{ top: marker.top }"
      >
        <svg class="route-marker-trail" viewBox="0 0 560 150" preserveAspectRatio="none">
          <path class="route-marker-ghost" d="M-18 126 C 124 142, 182 14, 342 44 S 452 118, 578 22" />
          <path class="route-marker-flow" d="M-18 126 C 124 142, 182 14, 342 44 S 452 118, 578 22" />
          <circle class="route-marker-fix" cx="342" cy="44" r="7" />
        </svg>
        <span class="route-marker-orbit" aria-hidden="true"></span>
        <span class="route-marker-line" aria-hidden="true"></span>
        <span class="route-marker-readout">FIX {{ marker.label }} / CURRENT</span>
      </div>
      <span class="chart-depth-band chart-depth-band-one"></span>
      <span class="chart-depth-band chart-depth-band-two"></span>
      <span class="chart-depth-band chart-depth-band-three"></span>
      <span class="chart-sweep"></span>
      <span class="chart-readout chart-readout-one"><b>SECTOR 07</b><i></i><b>COURSE 118</b></span>
      <span class="chart-readout chart-readout-two"><b>DEPTH 042</b><i></i><b>TIDE +02</b></span>
      <span class="chart-readout chart-readout-three"><b>SIGNAL LIVE</b><i></i><b>WAVE 031</b></span>
    </div>
    <header class="archive-masthead">
      <div class="archive-masthead-copy">
        <RouterLink class="article-back-link" to="/">返回首页</RouterLink>
        <p class="archive-eyebrow">
          <span aria-hidden="true"></span> LOGBOOK / {{ currentView.toUpperCase() }}
        </p>
        <h1>{{ pageTitle }}</h1>
        <p class="archive-description">
          {{ pageCaption }}。每篇文章都保留在它最初抵达这条航线的日期。
        </p>
      </div>
      <dl class="archive-ledger" aria-label="归档统计">
        <div>
          <dt>记录总数</dt>
          <dd>{{ totalArticles }}</dd>
        </div>
        <div>
          <dt>航行年份</dt>
          <dd>{{ publishedYears || "-" }}</dd>
        </div>
        <div>
          <dt>当前筛选</dt>
          <dd>{{ activeCategory || activeTag || "全部" }}</dd>
        </div>
      </dl>
    </header>

    <main class="archive-workspace">
      <div class="archive-control-bar">
        <nav class="archive-view-switcher" aria-label="文章组织方式">
          <RouterLink
            v-for="view in views"
            :key="view.key"
            :class="{ active: currentView === view.key }"
            :to="{ path: '/articles', query: { view: view.key } }"
          >
            {{ view.label }}
          </RouterLink>
        </nav>
        <div class="archive-locate-meter" aria-label="文章定位统计">
          <span>
            <b>{{ totalArticles }}</b>
            <small>总记录</small>
          </span>
        </div>
      </div>

      <div class="archive-layout">
        <aside class="archive-filter-rail">
          <div class="filter-rail-heading">
            <p>航线筛选</p>
            <button v-if="activeCategory || activeTag" type="button" @click="clearFilters">
              重置
            </button>
          </div>
          <section v-if="currentView !== 'tags'" class="filter-group">
            <p>分类</p>
            <button
              :class="{ active: !activeCategory }"
              type="button"
              @click="clearFilters"
            >
              全部分类 <small>{{ allArticleTotal }}</small>
            </button>
            <button
              v-for="category in categories"
              :key="category"
              :class="{ active: activeCategory === category }"
              type="button"
              @click="selectCategory(category)"
            >
              {{ category }} <small>{{ categoryCountMap.get(category) ?? 0 }}</small>
            </button>
          </section>
          <section v-if="currentView !== 'categories'" class="filter-group filter-tags">
            <p>标签</p>
            <button
              v-for="tag in tags"
              :key="tag"
              :class="{ active: activeTag === tag }"
              type="button"
              @click="selectTag(tag)"
            >
              # {{ tag }} <small>{{ tagCountMap.get(tag) ?? 0 }}</small>
            </button>
          </section>
        </aside>

        <section class="archive-results" aria-live="polite">
          <div v-if="loading" class="article-empty-state">正在校准航线……</div>
          <div v-else-if="errorText" class="article-empty-state">{{ errorText }}</div>
          <div v-else-if="!articles.length" class="article-empty-state">
            还没有文章，下一次靠岸会从这里开始。
          </div>
          <template v-else>
            <div v-if="!visibleArticles.length" class="article-empty-state">
              这条筛选航线上还没有匹配的记录。
            </div>
            <div v-else class="archive-groups">
              <section v-for="group in archiveGroups" :key="group.key" class="archive-month-group">
                <header class="archive-month-heading">
                  <p>{{ group.label }}</p>
                  <div class="archive-month-count" aria-label="本月文章统计">
                    <strong>{{ group.total }}</strong>
                    <span>本月总数</span>
                  </div>
                </header>
                <div class="archive-timeline">
                  <article
                    v-for="article in group.entries"
                    :key="article.id"
                    :class="['archive-entry', { visible: visibleArticleIds.has(article.id) }]"
                    :data-article-id="article.id"
                    data-archive-entry
                  >
                    <time :datetime="archiveDate(article)">{{
                      formatDay(archiveDate(article))
                    }}</time>
                    <span class="archive-node" aria-hidden="true"></span>
                    <div class="archive-entry-body">
                      <div class="archive-entry-meta">
                        <span>{{ article.category }}</span>
                        <span>{{ formatFullDate(archiveDate(article)) }}</span>
                      </div>
                      <h2>
                        <RouterLink :to="{ path: `/articles/${article.slug}` }">
                          {{ article.title }}
                        </RouterLink>
                      </h2>
                      <p>{{ article.summary || "这段航行还没有摘要，打开文章查看完整记录。" }}</p>
                      <footer>
                        <span>
                          {{ article.views }} 次阅读 <i aria-hidden="true"></i>
                          {{ article.likes }} 个喜欢
                        </span>
                        <span class="article-tags">
                          <b v-for="tag in article.tags" :key="tag">#{{ tag }}</b>
                        </span>
                      </footer>
                    </div>
                  </article>
                </div>
              </section>
            </div>
            <div ref="loadMoreSentinel" class="archive-load-more" aria-live="polite">
              <span v-if="loadingMore">正在继续读取航行记录…</span>
              <button v-else-if="loadMoreError" type="button" @click="loadMoreArticles">
                {{ loadMoreError }} 点击重试
              </button>
              <span v-else-if="hasMoreArticles">继续向下查看更多记录</span>
              <span v-else>已抵达最早文章</span>
            </div>
          </template>
        </section>
      </div>
    </main>
    <button
      v-show="showBackToTop"
      class="archive-back-to-top"
      type="button"
      aria-label="回到顶部"
      title="回到顶部"
      @click="scrollToTop"
    >
      <span aria-hidden="true">↑</span>
    </button>
  </div>
</template>

<style scoped>
.article-page {
  --archive-scroll-shift: 0px;
  --archive-counter-shift: 0px;
  --archive-visual-image: none;
  --archive-visual-opacity: 0;
  --archive-visual-layer-opacity: 0;
  --archive-ink: #f4f3e9;
  --archive-signal: #f7c951;
  --archive-current: #86d3c6;
  --archive-coral: #e38363;
  --archive-steel: rgba(207, 225, 217, 0.18);
  position: relative;
  isolation: isolate;
  min-height: 100vh;
  overflow: clip;
  padding: 7.5rem 0 7rem;
  color: var(--archive-ink);
  background:
    radial-gradient(circle at 72% 10%, rgba(247, 201, 81, 0.12), transparent 18rem),
    radial-gradient(circle at 18% 62%, rgba(134, 211, 198, 0.11), transparent 25rem),
    radial-gradient(circle at 50% 0%, rgba(255, 255, 255, 0.03), transparent 28rem),
    linear-gradient(118deg, rgba(112, 63, 49, 0.22) 0, rgba(112, 63, 49, 0) 31%),
    linear-gradient(180deg, #061d28 0%, #0a2c35 43%, #071c27 100%);
}
.article-page::before {
  content: "";
  position: absolute;
  z-index: -3;
  top: 6rem;
  left: -16%;
  width: 76%;
  height: 34rem;
  clip-path: polygon(0 8%, 88% 0, 100% 72%, 16% 100%);
  background:
    radial-gradient(ellipse at 26% 30%, rgba(231, 139, 102, 0.18), transparent 54%),
    linear-gradient(122deg, rgba(137, 76, 58, 0.3), rgba(24, 79, 78, 0.08) 72%);
  opacity: 0.72;
  transform: translate3d(0, var(--archive-counter-shift), 0);
  animation: chart-sheet-drift 19s ease-in-out infinite alternate;
}
.article-page::after {
  content: "";
  position: absolute;
  z-index: -1;
  top: 0;
  right: -22%;
  width: 68%;
  height: 34rem;
  border-bottom: 1px solid rgba(134, 211, 198, 0.16);
  transform: rotate(-8deg);
  animation: horizon-drift 14s ease-in-out infinite alternate;
}
.sea-chart-motion {
  position: absolute;
  z-index: -4;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  opacity: 0.82;
  animation: atmosphere-drift 32s ease-in-out infinite alternate;
}
.archive-visual-stack {
  position: fixed;
  inset: 0;
  z-index: -5;
  pointer-events: none;
  opacity: var(--archive-visual-opacity, 0);
}
.archive-visual-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image: var(--archive-visual-image, none);
  background-position: center top;
  background-repeat: no-repeat;
  background-size: cover;
  opacity: 0;
  filter: saturate(1.08) contrast(1.03) brightness(1.04);
  transform: translate3d(0, calc(var(--archive-scroll-shift) * -0.18), 0) scale(1.02);
  transition:
    opacity 1.6s cubic-bezier(0.25, 1, 0.5, 1),
    transform 8s linear;
}
.archive-visual-layer.active {
  opacity: var(--archive-visual-layer-opacity, 0);
  transform: translate3d(0, calc(var(--archive-scroll-shift) * -0.18), 0) scale(1.045);
}
.archive-visual-layer::after {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(6, 18, 26, 0.72) 0%, rgba(6, 18, 26, 0.34) 46%, rgba(6, 18, 26, 0.62) 100%),
    linear-gradient(180deg, rgba(6, 18, 26, 0.14) 0%, rgba(6, 18, 26, 0.42) 54%, rgba(6, 18, 26, 0.86) 100%);
}
.sea-chart-motion::before,
.sea-chart-motion::after {
  content: "";
  position: fixed;
  inset: -12%;
  pointer-events: none;
}
.sea-chart-motion::before {
  background:
    radial-gradient(ellipse at 18% 22%, rgba(247, 201, 81, 0.08), transparent 20rem),
    radial-gradient(ellipse at 82% 42%, rgba(134, 211, 198, 0.1), transparent 27rem),
    linear-gradient(118deg, transparent 0 42%, rgba(244, 243, 233, 0.035) 42.2%, transparent 43%);
  opacity: 0.68;
  transform: translate3d(0, 0, 0);
  animation: atmosphere-drift 26s cubic-bezier(0.25, 1, 0.5, 1) infinite alternate;
}
.sea-chart-motion::after {
  background:
    linear-gradient(160deg, transparent 0 44%, rgba(134, 211, 198, 0.075) 48%, transparent 56%),
    radial-gradient(ellipse at 65% 78%, rgba(244, 243, 233, 0.045), transparent 28rem);
  opacity: 0.45;
  transform: translate3d(0, -8%, 0);
  animation: atmosphere-scan 12s linear infinite;
}
.chart-current {
  position: absolute;
  left: -12%;
  display: block;
  width: 124%;
  height: 8rem;
  background:
    linear-gradient(90deg, transparent, rgba(134, 211, 198, 0.18), transparent);
  opacity: 0.45;
  transform: rotate(-8deg) translateX(-5%);
  animation: current-slip 18s cubic-bezier(0.25, 1, 0.5, 1) infinite alternate;
}
.chart-current-one {
  top: 20rem;
}
.chart-current-two {
  top: 62rem;
  opacity: 0.32;
  animation-delay: -6s;
}
.chart-current-three {
  top: 108rem;
  opacity: 0.24;
  animation-delay: -11s;
}
.chart-signal {
  position: fixed;
  right: 7%;
  display: grid;
  width: 9rem;
  height: 6.5rem;
  opacity: 0.58;
}
.chart-signal::before,
.chart-signal::after {
  content: "";
  display: block;
  align-self: end;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--archive-signal), transparent);
  transform-origin: right;
  animation: signal-blink 2.8s ease-in-out infinite;
}
.chart-signal::after {
  align-self: start;
  width: 62%;
  justify-self: end;
  animation-delay: -1.4s;
}
.chart-signal-one {
  top: 28rem;
}
.chart-signal-two {
  top: 86rem;
  right: auto;
  left: 8%;
  color: var(--archive-current);
  animation-delay: -2s;
}
.archive-route-field {
  position: absolute;
  z-index: 0;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  transform: translate3d(0, var(--archive-scroll-shift), 0);
}
.archive-route-map {
  display: block;
  width: 100%;
  height: auto;
  overflow: visible;
}
.archive-route-marker {
  position: absolute;
  isolation: isolate;
  display: flex;
  align-items: center;
  width: min(22rem, 24vw);
  height: 5rem;
  color: rgba(112, 201, 191, 0.44);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.55rem;
  letter-spacing: 0.13em;
  opacity: 0.9;
  animation: route-marker-drift 12s ease-in-out infinite alternate;
}
.archive-route-marker.left {
  left: 4%;
}
.archive-route-marker.right {
  right: 4%;
  flex-direction: row-reverse;
  color: rgba(247, 201, 81, 0.38);
  animation-delay: -5s;
}
.route-marker-trail {
  position: absolute;
  z-index: 0;
  top: -3.8rem;
  left: -4rem;
  width: min(36rem, 46vw);
  height: 10rem;
  overflow: visible;
}
.archive-route-marker.right .route-marker-trail {
  transform: scaleX(-1);
}
.route-marker-ghost,
.route-marker-flow,
.route-marker-fix {
  fill: none;
  stroke: currentColor;
  vector-effect: non-scaling-stroke;
}
.route-marker-ghost {
  stroke-width: 1;
  stroke-dasharray: 8 14;
  opacity: 0.68;
}
.route-marker-flow {
  stroke-width: 1.5;
  stroke-dasharray: 6 142;
  stroke-linecap: round;
  filter: drop-shadow(0 0 0.36rem currentColor);
  opacity: 0.92;
  animation: route-marker-flow 7.2s linear infinite;
}
.route-marker-fix {
  stroke-width: 1.2;
  opacity: 0.82;
  transform-origin: center;
  animation: route-marker-fix 4.6s ease-in-out infinite;
}
.route-marker-orbit {
  position: relative;
  z-index: 1;
  display: block;
  width: 0.58rem;
  height: 0.58rem;
  border: 1px solid currentColor;
  border-radius: 50%;
  box-shadow: 0 0 0 0.34rem color-mix(in srgb, currentColor 16%, transparent);
  animation: route-marker-pulse 4.6s ease-in-out infinite;
}
.route-marker-orbit::before,
.route-marker-orbit::after {
  content: "";
  position: absolute;
  background: currentColor;
}
.route-marker-orbit::before {
  top: 50%;
  right: -0.35rem;
  left: -0.35rem;
  height: 1px;
}
.route-marker-orbit::after {
  top: -0.35rem;
  bottom: -0.35rem;
  left: 50%;
  width: 1px;
}
.route-marker-line {
  position: relative;
  z-index: 1;
  display: block;
  width: clamp(4rem, 11vw, 9rem);
  height: 1px;
  margin: 0 0.8rem;
  background: linear-gradient(90deg, currentColor, transparent);
}
.archive-route-marker.right .route-marker-line {
  background: linear-gradient(90deg, transparent, currentColor);
}
.route-marker-readout {
  position: relative;
  z-index: 1;
  white-space: nowrap;
  text-shadow: 0 0 0.7rem rgba(112, 201, 191, 0.15);
}
.route-base,
.route-flow {
  fill: none;
  vector-effect: non-scaling-stroke;
}
.route-base {
  stroke: currentColor;
  stroke-width: 1;
  stroke-dasharray: 1.2 2.2;
  opacity: 0.28;
}
.route-flow {
  stroke: currentColor;
  stroke-width: 2;
  stroke-dasharray: 7 93;
  stroke-linecap: round;
  filter: drop-shadow(0 0 0.45rem currentColor);
  animation: route-current 11s linear infinite;
}
.route-coral {
  color: #e38363;
}
.route-cyan {
  color: #70c9bf;
}
.route-cyan.route-flow {
  animation-duration: 15s;
  animation-direction: reverse;
}
.route-fix {
  color: #f7c951;
  opacity: 0.48;
  animation: route-fix-pulse 4.8s ease-in-out infinite;
}
.route-fix path,
.route-fix circle {
  fill: none;
  stroke: currentColor;
  stroke-width: 1;
  vector-effect: non-scaling-stroke;
}
.route-fix-two {
  color: #86d3c6;
  animation-delay: -2.4s;
}
.chart-depth-band {
  position: absolute;
  display: block;
  opacity: 0.52;
}
.chart-depth-band-one {
  top: 39rem;
  right: -11%;
  width: 69%;
  height: 22rem;
  clip-path: polygon(7% 0, 100% 14%, 91% 100%, 0 77%);
  background:
    repeating-linear-gradient(
      164deg,
      transparent 0 1.35rem,
      rgba(229, 131, 99, 0.09) 1.4rem 1.46rem
    ),
    rgba(108, 64, 54, 0.12);
  animation: depth-band-one 17s ease-in-out infinite alternate;
}
.chart-depth-band-two {
  bottom: 7rem;
  left: -9%;
  width: 74%;
  height: 27rem;
  clip-path: polygon(0 17%, 90% 0, 100% 78%, 18% 100%);
  background:
    repeating-linear-gradient(
      17deg,
      transparent 0 1.8rem,
      rgba(112, 201, 191, 0.08) 1.85rem 1.92rem
    ),
    rgba(20, 80, 81, 0.16);
  transform: translate3d(0, var(--archive-counter-shift), 0);
  animation: depth-band-two 21s ease-in-out infinite alternate;
}
.chart-depth-band-three {
  top: 94rem;
  right: -18%;
  width: 58%;
  height: 18rem;
  clip-path: polygon(12% 0, 100% 22%, 88% 100%, 0 72%);
  background:
    repeating-linear-gradient(144deg, transparent 0 1.1rem, rgba(247, 201, 81, 0.07) 1.15rem 1.2rem),
    linear-gradient(120deg, rgba(247, 201, 81, 0.08), rgba(134, 211, 198, 0.06));
  opacity: 0.34;
  animation: depth-band-three 18s ease-in-out infinite alternate;
}
.chart-sweep {
  position: absolute;
  top: -22rem;
  right: -15%;
  left: -15%;
  height: 18rem;
  background: linear-gradient(
    180deg,
    transparent,
    rgba(247, 201, 81, 0.055) 45%,
    rgba(227, 131, 99, 0.075) 52%,
    transparent
  );
  transform: rotate(-6deg);
  animation: chart-sweep 19s 2s linear infinite;
}
.chart-readout {
  position: absolute;
  display: flex;
  gap: 0.7rem;
  align-items: center;
  color: rgba(244, 243, 233, 0.22);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.56rem;
  letter-spacing: 0.14em;
  white-space: nowrap;
  animation: readout-drift 10s ease-in-out infinite alternate;
}
.chart-readout b {
  font-weight: 500;
}
.chart-readout i {
  width: 2.5rem;
  height: 1px;
  background: currentColor;
}
.chart-readout-one {
  top: 34rem;
  right: 4%;
}
.chart-readout-two {
  bottom: 14rem;
  left: 3%;
  animation-delay: -4.5s;
}
.chart-readout-three {
  top: 84rem;
  right: 10%;
  color: rgba(134, 211, 198, 0.24);
  animation-delay: -7.5s;
}
.chart-bearing {
  position: absolute;
  display: block;
  border: 1px solid rgba(247, 201, 81, 0.16);
  border-radius: 50%;
}
.chart-bearing::before,
.chart-bearing::after {
  content: "";
  position: absolute;
  inset: 12%;
  border: 1px dashed rgba(134, 211, 198, 0.13);
  border-radius: inherit;
}
.chart-bearing::after {
  inset: 32%;
  border-style: solid;
}
.chart-bearing-one {
  top: 5rem;
  right: -8rem;
  width: 30rem;
  height: 30rem;
  animation: bearing-turn 46s linear infinite;
}
.chart-bearing-two {
  bottom: 8%;
  left: -10rem;
  width: 25rem;
  height: 25rem;
  animation: bearing-turn 62s linear infinite reverse;
}
.chart-ping {
  position: absolute;
  top: 17rem;
  right: 16%;
  width: 0.48rem;
  height: 0.48rem;
  border: 1px solid #f7c951;
  border-radius: 50%;
  box-shadow: 0 0 1rem rgba(247, 201, 81, 0.55);
  animation: chart-ping 4.2s ease-out infinite;
}
.archive-masthead,
.archive-workspace {
  position: relative;
  z-index: 1;
  width: min(1180px, calc(100% - 3rem));
  margin: 0 auto;
}
.archive-masthead {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 27rem;
  gap: 4rem;
  align-items: end;
  padding: 3.65rem 0 3rem;
  border-bottom: 1px solid rgba(207, 225, 217, 0.2);
}
.archive-masthead::before {
  content: "";
  position: absolute;
  right: 1.4rem;
  bottom: -1px;
  width: min(28rem, 42vw);
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--archive-coral), var(--archive-signal));
  box-shadow: 0 0 1.1rem rgba(247, 201, 81, 0.48);
  transform-origin: right;
  animation: masthead-signal 4.8s 0.7s cubic-bezier(0.25, 1, 0.5, 1) infinite;
}
.archive-masthead::after {
  content: "";
  position: absolute;
  right: -0.04em;
  bottom: -0.16em;
  z-index: -1;
  color: rgba(244, 243, 233, 0.035);
  font-family: var(--display-font);
  font-size: clamp(7rem, 17vw, 17rem);
  line-height: 0.8;
  pointer-events: none;
}
.archive-masthead-copy {
  position: relative;
  padding-right: 1rem;
  animation: masthead-rise 0.85s cubic-bezier(0.2, 0.76, 0.26, 1) both;
}
.archive-masthead-copy::after {
  content: "";
  position: absolute;
  right: 0;
  top: 0.35rem;
  width: 0.2rem;
  height: 3.8rem;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(247, 201, 81, 0.72), rgba(134, 211, 198, 0.08));
  box-shadow: 0 0 1rem rgba(247, 201, 81, 0.32);
}
.article-back-link {
  display: inline-flex;
  gap: 0.45rem;
  align-items: center;
  color: #f7c951;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.8rem;
  text-decoration: none;
}
.article-back-link::before {
  content: "←";
  font-size: 1rem;
  transition: transform 0.2s ease;
}
.article-back-link:hover::before {
  transform: translateX(-0.25rem);
}
.archive-eyebrow {
  display: flex;
  gap: 0.55rem;
  align-items: center;
  margin: 3.4rem 0 1rem;
  color: #f7c951;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.15em;
}
.archive-eyebrow span {
  width: 0.48rem;
  height: 0.48rem;
  border: 1px solid #f7c951;
  border-radius: 50%;
  box-shadow: 0 0 0 0.24rem rgba(247, 201, 81, 0.1);
  animation: eyebrow-ping 2.8s ease-out infinite;
}
.archive-masthead h1 {
  margin: 0;
  font-size: clamp(3rem, 6vw, 5.25rem);
  line-height: 1;
  text-shadow:
    0 0.8rem 2.2rem rgba(0, 0, 0, 0.24),
    0.08em 0.06em 0 rgba(227, 131, 99, 0.18);
  animation: title-settle 0.9s 0.1s cubic-bezier(0.2, 0.76, 0.26, 1) both;
}
.archive-description {
  max-width: 35rem;
  margin: 1.35rem 0 0;
  color: rgba(244, 243, 233, 0.72);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.96rem;
  line-height: 1.9;
}
.archive-ledger {
  position: relative;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  border-radius: 1rem;
  margin: 0;
  overflow: hidden;
  background: rgba(207, 225, 217, 0.18);
  border: 1px solid rgba(207, 225, 217, 0.24);
  box-shadow:
    0 1.2rem 3rem rgba(2, 16, 22, 0.22),
    inset 0.2rem 0 0 rgba(227, 131, 99, 0.42);
  backdrop-filter: blur(0.65rem);
  animation: ledger-arrive 0.75s 0.28s cubic-bezier(0.2, 0.76, 0.26, 1) both;
}
.archive-ledger::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(120deg, transparent, rgba(244, 243, 233, 0.08), transparent),
    repeating-linear-gradient(90deg, transparent 0 2.4rem, rgba(134, 211, 198, 0.045) 2.45rem 2.5rem);
  opacity: 0.32;
  transform: translateX(-42%);
  animation: ledger-glint 7s 1.1s cubic-bezier(0.25, 1, 0.5, 1) infinite;
  pointer-events: none;
}
.archive-ledger div {
  position: relative;
  min-width: 0;
  padding: 1rem 0.85rem;
  background: rgba(9, 43, 56, 0.82);
  transition:
    background-color 0.22s ease,
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1);
}
.archive-ledger div:nth-child(1) {
  animation: ledger-cell 0.55s 0.42s ease both;
}
.archive-ledger div:nth-child(2) {
  animation: ledger-cell 0.55s 0.52s ease both;
}
.archive-ledger div:nth-child(3) {
  animation: ledger-cell 0.55s 0.62s ease both;
}
.archive-ledger dt {
  color: rgba(244, 243, 233, 0.48);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.67rem;
  white-space: nowrap;
}
.archive-ledger dd {
  overflow: hidden;
  margin: 0.45rem 0 0;
  color: #f7c951;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 1.05rem;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@media (hover: hover) and (pointer: fine) {
  .archive-ledger div:hover {
    background: rgba(14, 60, 69, 0.9);
    transform: translateY(-0.12rem);
  }
}
.archive-workspace {
  position: relative;
  z-index: 1;
  padding-top: 1.9rem;
}
.archive-control-bar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-height: 3.8rem;
  border-bottom: 1px solid rgba(207, 225, 217, 0.15);
  animation: control-unfold 0.7s 0.45s ease both;
}
.archive-control-bar::before {
  content: "";
  position: absolute;
  inset: 0 auto -1px 0;
  width: 7.5rem;
  border-bottom: 1px solid rgba(247, 201, 81, 0.62);
  opacity: 0.7;
  transform: translateX(calc(var(--archive-scroll-shift) * 0.36));
}
.archive-locate-meter {
  display: inline-grid;
  align-items: center;
  min-width: 5.6rem;
  padding: 0.48rem 0.76rem;
  border: 1px solid rgba(134, 211, 198, 0.18);
  border-radius: 0.65rem;
  background:
    linear-gradient(90deg, rgba(247, 201, 81, 0.08), rgba(134, 211, 198, 0.06)),
    rgba(6, 29, 40, 0.34);
  font-family: "Noto Sans SC", sans-serif;
}
.archive-locate-meter span {
  display: grid;
  gap: 0.08rem;
}
.archive-locate-meter b {
  color: #f7c951;
  font-size: 0.96rem;
  line-height: 1;
}
.archive-locate-meter small {
  color: rgba(244, 243, 233, 0.48);
  font-size: 0.58rem;
  white-space: nowrap;
}
.archive-view-switcher {
  display: flex;
  align-self: stretch;
  gap: 1.5rem;
}
.archive-view-switcher a {
  position: relative;
  display: grid;
  place-items: center;
  min-width: 3rem;
  color: rgba(244, 243, 233, 0.48);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.82rem;
  font-weight: 700;
  text-decoration: none;
  transition:
    color 0.18s ease,
    transform 0.18s cubic-bezier(0.22, 1, 0.36, 1);
}
.archive-view-switcher a::after {
  content: "";
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 100%;
  height: 2px;
  background: #f7c951;
  transform: scaleX(0);
  transform-origin: center;
  transition: transform 0.2s ease;
}
.archive-view-switcher a:hover,
.archive-view-switcher a.active {
  color: #f7c951;
}
.archive-view-switcher a:hover {
  transform: translateY(-0.12rem);
}
.archive-view-switcher a.active::after {
  transform: scaleX(1);
}
.archive-layout {
  display: grid;
  grid-template-columns: 15rem minmax(0, 1fr);
  gap: 2.6rem;
  padding-top: 2.5rem;
}
.archive-filter-rail {
  position: sticky;
  top: 6.2rem;
  align-self: start;
  max-height: calc(100vh - 7.4rem);
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 1.15rem 1.1rem;
  border: 1px solid rgba(207, 225, 217, 0.12);
  border-radius: 1.3rem;
  background:
    linear-gradient(180deg, rgba(9, 43, 56, 0.32), rgba(9, 43, 56, 0.12)),
    rgba(7, 29, 40, 0.12);
  box-shadow:
    0 1.5rem 2.8rem rgba(1, 10, 14, 0.1),
    inset 0 0 0 1px rgba(244, 243, 233, 0.03);
  backdrop-filter: blur(6px);
  scrollbar-color: rgba(134, 211, 198, 0.38) transparent;
  scrollbar-width: thin;
  animation: rail-rise 0.75s 0.6s ease both;
}
.archive-filter-rail::-webkit-scrollbar {
  width: 5px;
}
.archive-filter-rail::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(247, 201, 81, 0.55), rgba(134, 211, 198, 0.42));
}
.archive-filter-rail::-webkit-scrollbar-track {
  background: transparent;
}
.archive-filter-rail::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  background:
    linear-gradient(90deg, rgba(9, 43, 56, 0.2), rgba(9, 43, 56, 0.02)),
    repeating-linear-gradient(180deg, transparent 0 2.2rem, rgba(134, 211, 198, 0.018) 2.25rem 2.3rem);
  opacity: 0.45;
  border-radius: inherit;
}
.archive-filter-rail::after {
  content: "";
  position: absolute;
  top: 0;
  right: -1px;
  width: 1px;
  height: 4rem;
  background: linear-gradient(transparent, #e38363, #f7c951, transparent);
  box-shadow: 0 0 0.8rem rgba(227, 131, 99, 0.45);
  animation: rail-scan 8s 1.2s ease-in-out infinite;
}
.filter-rail-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2.2rem;
}
.filter-rail-heading p,
.filter-group > p {
  margin: 0;
  color: #f7c951;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.14em;
}
.filter-rail-heading button {
  padding: 0;
  border: 0;
  color: rgba(244, 243, 233, 0.56);
  background: none;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.7rem;
  cursor: pointer;
  transition:
    color 0.18s ease,
    transform 0.18s cubic-bezier(0.22, 1, 0.36, 1);
}
.filter-rail-heading button:hover,
.filter-rail-heading button:focus-visible {
  color: #f7c951;
  transform: translateX(-0.18rem);
}
.filter-group + .filter-group {
  margin-top: 2.4rem;
}
.filter-group > p {
  margin-bottom: 0.8rem;
  color: rgba(244, 243, 233, 0.58);
  letter-spacing: 0.08em;
}
.filter-group button {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 2rem;
  padding: 0.45rem 0.7rem 0.45rem 0.95rem;
  border: 1px solid transparent;
  border-radius: 999px;
  color: rgba(244, 243, 233, 0.82);
  background: transparent;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.82rem;
  text-align: left;
  cursor: pointer;
  transition:
    color 0.18s ease,
    border-color 0.18s ease,
    background-color 0.18s ease,
    text-shadow 0.18s ease,
    transform 0.18s cubic-bezier(0.22, 1, 0.36, 1);
}
.filter-group button::before {
  content: "";
  position: absolute;
  top: 50%;
  left: -0.75rem;
  width: 0.28rem;
  height: 0.28rem;
  border: 1px solid currentColor;
  border-radius: 50%;
  opacity: 0;
  transform: translateY(-50%) scale(0.45);
  transition:
    opacity 0.18s ease,
    transform 0.18s cubic-bezier(0.22, 1, 0.36, 1);
}
.filter-group button:hover,
.filter-group button.active {
  color: #f7c951;
  text-shadow: 0 0 0.7rem rgba(247, 201, 81, 0.22);
  border-color: rgba(247, 201, 81, 0.28);
  background: rgba(247, 201, 81, 0.045);
}
.filter-group button:hover::before,
.filter-group button.active::before {
  opacity: 1;
  transform: translateY(-50%) scale(1);
}
.filter-group:not(.filter-tags) button:hover,
.filter-group:not(.filter-tags) button.active {
  transform: translateX(0.2rem);
}
.filter-group small {
  color: rgba(244, 243, 233, 0.5);
  font-size: 0.65rem;
}
.filter-tags button {
  display: inline-flex;
  gap: 0.32rem;
  width: auto;
  margin-right: 0.7rem;
  transition:
    color 0.18s ease,
    transform 0.18s ease,
    text-shadow 0.18s ease;
}
.filter-tags button::before {
  content: none;
}
.filter-tags button:hover,
.filter-tags button.active {
  transform: translateY(-0.08rem);
  text-shadow: 0 0 0.65rem rgba(247, 201, 81, 0.32);
}
.archive-results {
  position: relative;
  isolation: isolate;
  padding: 0.9rem 0 0.15rem;
  border-radius: 1.4rem;
  background:
    linear-gradient(180deg, rgba(7, 29, 40, 0.18), rgba(7, 29, 40, 0.04)),
    rgba(7, 29, 40, 0.025);
  box-shadow:
    0 1.6rem 2.8rem rgba(1, 10, 14, 0.07),
    inset 0 0 0 1px rgba(244, 243, 233, 0.025);
  backdrop-filter: blur(3px);
}
.archive-results::before {
  content: "";
  position: absolute;
  inset: -1.5rem -2rem -2.5rem;
  z-index: -2;
  background:
    linear-gradient(90deg, rgba(5, 25, 35, 0.08), rgba(8, 38, 48, 0.12), transparent 86%),
    radial-gradient(circle at 18% 18%, rgba(244, 243, 233, 0.035), transparent 18rem);
  opacity: 0.48;
  pointer-events: none;
}
.archive-results::after {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  left: 5.35rem;
  z-index: -1;
  width: 8rem;
  background: linear-gradient(90deg, rgba(247, 201, 81, 0.045), transparent);
  opacity: 0.48;
  pointer-events: none;
}
.archive-groups {
  display: grid;
  gap: 3rem;
}
.archive-month-group {
  position: relative;
  isolation: isolate;
  padding-top: 0.1rem;
}
.archive-month-group::before {
  content: "";
  position: absolute;
  z-index: -1;
  inset: -0.8rem -2.2rem;
  clip-path: polygon(0 9%, 100% 0, 96% 91%, 5% 100%);
  background: linear-gradient(
    102deg,
    transparent 7%,
    rgba(227, 131, 99, 0.045) 46%,
    rgba(112, 201, 191, 0.04) 58%,
    transparent 92%
  );
  opacity: 0.5;
  transform: translateX(-3%);
  animation: month-current 12s ease-in-out infinite alternate;
}
.archive-month-group::after {
  content: "";
  position: absolute;
  z-index: -2;
  top: 3.2rem;
  right: 6%;
  width: 10rem;
  aspect-ratio: 1;
  border: 1px solid rgba(134, 211, 198, 0.08);
  border-radius: 50%;
  opacity: 0.8;
  transform: rotate(0deg);
  animation: month-orbit 22s linear infinite;
}
.archive-month-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  padding: 0 0.2rem 1rem;
  border-bottom: 1px solid rgba(207, 225, 217, 0.18);
  animation: month-heading-in 0.65s ease both;
}
.archive-month-heading p {
  margin: 0;
  color: #f4f3e9;
  font-size: 1.35rem;
}
.archive-month-count {
  display: grid;
  grid-template-columns: auto auto;
  gap: 0.1rem 0.55rem;
  align-items: baseline;
  justify-content: end;
  min-width: 6.4rem;
  padding: 0.48rem 0.68rem;
  border: 1px solid rgba(134, 211, 198, 0.2);
  border-radius: 0.75rem;
  background:
    linear-gradient(135deg, rgba(134, 211, 198, 0.1), rgba(247, 201, 81, 0.05)),
    rgba(6, 29, 40, 0.38);
  font-family: "Noto Sans SC", sans-serif;
}
.archive-month-count strong {
  color: #f7c951;
  font-size: 1rem;
  line-height: 1;
}
.archive-month-count span {
  color: rgba(134, 211, 198, 0.86);
  font-size: 0.64rem;
}
.archive-timeline {
  position: relative;
  overflow: hidden;
  padding-top: 0.15rem;
}
.archive-timeline::before {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  left: 5.35rem;
  width: 1px;
  background: rgba(247, 201, 81, 0.32);
}
.archive-timeline::after {
  content: "";
  position: absolute;
  top: -5rem;
  left: 5.35rem;
  width: 1px;
  height: 5rem;
  background: linear-gradient(transparent, #f7c951, transparent);
  box-shadow: 0 0 0.8rem rgba(247, 201, 81, 0.75);
  animation: timeline-scan 7s 1.1s ease-in-out infinite;
}
.archive-entry {
  position: relative;
  display: grid;
  grid-template-columns: 4.3rem 2.1rem minmax(0, 1fr);
  margin: 0.95rem 0;
  padding: 1.4rem 1.2rem 1.35rem 0.95rem;
  border: 1px solid rgba(207, 225, 217, 0.12);
  border-radius: 1.2rem;
  background:
    linear-gradient(145deg, rgba(9, 43, 56, 0.48), rgba(6, 24, 34, 0.28)),
    rgba(9, 43, 56, 0.1);
  box-shadow:
    0 0.9rem 2rem rgba(1, 10, 14, 0.1),
    inset 0 0 0 1px rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(5px);
  opacity: 0;
  transform: translate3d(1.35rem, 0.65rem, 0);
  transition:
    opacity 0.65s ease,
    transform 0.65s cubic-bezier(0.2, 0.76, 0.26, 1),
    border-color 0.35s ease,
    background-color 0.35s ease;
}
.archive-entry.visible {
  opacity: 1;
  transform: translate3d(0, 0, 0);
}
.archive-entry::before {
  content: "";
  position: absolute;
  inset: 0.45rem 0.45rem 0.45rem 0.45rem;
  z-index: -1;
  border-left: 1px solid rgba(247, 201, 81, 0.24);
  background:
    linear-gradient(90deg, rgba(247, 201, 81, 0.08), rgba(134, 211, 198, 0.08), transparent 82%),
    repeating-linear-gradient(90deg, transparent 0 3.8rem, rgba(244, 243, 233, 0.022) 3.85rem 3.9rem);
  opacity: 0;
  transform: translateX(-0.4rem) scaleX(0.92);
  transform-origin: left;
  transition:
    opacity 0.35s ease,
    transform 0.45s cubic-bezier(0.25, 1, 0.5, 1);
}
.archive-entry::after {
  content: "READ";
  position: absolute;
  top: 1.4rem;
  right: 0.6rem;
  color: rgba(134, 211, 198, 0.28);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.58rem;
  letter-spacing: 0.16em;
  opacity: 0;
  transform: translateX(0.7rem);
  transition:
    opacity 0.22s ease,
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1);
}
.archive-entry:hover::before,
.archive-entry:focus-within::before {
  opacity: 1;
  transform: translateX(0) scaleX(1);
}
.archive-entry:hover::after,
.archive-entry:focus-within::after {
  opacity: 1;
  transform: translateX(0);
}
.archive-entry:hover {
  border-color: rgba(134, 211, 198, 0.34);
  background:
    linear-gradient(145deg, rgba(12, 58, 66, 0.56), rgba(6, 26, 36, 0.38)),
    rgba(5, 22, 30, 0.08);
  transform: translate3d(0.1rem, -0.18rem, 0);
}
.archive-entry time {
  padding-top: 0.15rem;
  color: #f7c951;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.74rem;
  font-weight: 700;
  transition:
    color 0.3s ease,
    text-shadow 0.3s ease;
}
.archive-node {
  position: relative;
  z-index: 1;
  width: 0.65rem;
  height: 0.65rem;
  margin: 0.18rem auto 0;
  border: 2px solid #f7c951;
  border-radius: 50%;
  background: #061d28;
  box-shadow: 0 0 0 0.35rem rgba(247, 201, 81, 0.08);
  transition:
    transform 0.35s ease,
    background-color 0.35s ease,
    box-shadow 0.35s ease;
}
.archive-node::after {
  content: "";
  position: absolute;
  inset: -0.48rem;
  border: 1px solid rgba(247, 201, 81, 0.35);
  border-radius: 50%;
  opacity: 0;
}
.archive-entry:hover .archive-node,
.archive-entry:focus-within .archive-node {
  background: #f7c951;
  box-shadow: 0 0 1.2rem rgba(247, 201, 81, 0.65);
  transform: scale(1.22);
}
.archive-entry:hover .archive-node::after,
.archive-entry:focus-within .archive-node::after {
  animation: node-ripple 1.8s ease-out infinite;
}
.archive-entry:hover time,
.archive-entry:focus-within time {
  color: #fff0a7;
  text-shadow: 0 0 0.8rem rgba(247, 201, 81, 0.45);
}
.archive-entry-body {
  min-width: 0;
  padding-left: 0.3rem;
  transition: transform 0.4s cubic-bezier(0.2, 0.76, 0.26, 1);
}
.archive-entry:hover .archive-entry-body,
.archive-entry:focus-within .archive-entry-body {
  transform: translateX(0.35rem);
}
.archive-entry-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
  color: rgba(244, 243, 233, 0.58);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.71rem;
}
.archive-entry-meta span:first-child {
  color: #9ae6da;
  text-shadow: 0 0 0.7rem rgba(134, 211, 198, 0.16);
}
.archive-entry h2 {
  margin: 0.5rem 0 0.45rem;
  font-size: clamp(1.4rem, 2.6vw, 2.05rem);
  line-height: 1.2;
}
.archive-entry h2 a {
  position: relative;
  color: #fff9e9;
  text-decoration: none;
  text-shadow:
    0 0.1rem 0.3rem rgba(0, 0, 0, 0.28),
    0.06em 0.05em 0 rgba(5, 25, 35, 0.35);
  transition:
    color 0.18s ease,
    text-shadow 0.22s ease;
}
.archive-entry h2 a:hover {
  color: #f7c951;
  text-shadow: 0 0 1rem rgba(247, 201, 81, 0.22);
}
.archive-entry-body > p {
  max-width: 43rem;
  margin: 0;
  color: rgba(244, 243, 233, 0.84);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.86rem;
  line-height: 1.75;
  text-shadow: 0 0.08rem 0.25rem rgba(0, 0, 0, 0.2);
}
.archive-entry footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  margin-top: 1rem;
  color: rgba(244, 243, 233, 0.62);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.7rem;
  padding-right: 0.7rem;
}
.archive-entry footer i {
  display: inline-block;
  width: 0.2rem;
  height: 0.2rem;
  margin: 0 0.35rem;
  border-radius: 50%;
  background: #86d3c6;
  vertical-align: middle;
}
.article-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  color: #9ae6da;
}
.article-tags b {
  position: relative;
  font-weight: 500;
  transition:
    color 0.18s ease,
    transform 0.18s cubic-bezier(0.22, 1, 0.36, 1);
}
.article-tags b:hover {
  color: #fff0a7;
  transform: translateY(-0.08rem);
}
.article-empty-state {
  position: relative;
  display: grid;
  min-height: 22rem;
  place-items: center;
  color: rgba(244, 243, 233, 0.55);
  font-family: "Noto Sans SC", sans-serif;
}
.article-empty-state::before {
  content: "";
  width: 3.8rem;
  aspect-ratio: 1;
  margin-bottom: -5.6rem;
  border: 1px solid rgba(247, 201, 81, 0.38);
  border-radius: 50%;
  box-shadow: inset 0 0 0 1rem rgba(134, 211, 198, 0.035);
  animation: empty-radar 2.2s linear infinite;
}
.archive-load-more {
  position: relative;
  display: grid;
  min-height: 7rem;
  margin-top: 2.4rem;
  place-items: center;
  color: rgba(134, 211, 198, 0.82);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
}
.archive-load-more::before {
  content: "";
  width: min(11rem, 52%);
  height: 1px;
  margin-bottom: -2.5rem;
  background: linear-gradient(90deg, transparent, rgba(247, 201, 81, 0.55), transparent);
  animation: load-line 2.8s cubic-bezier(0.25, 1, 0.5, 1) infinite alternate;
}
.archive-load-more::after {
  content: "";
  width: 0.42rem;
  aspect-ratio: 1;
  margin-top: -2.35rem;
  border-radius: 50%;
  background: #f7c951;
  box-shadow: 0 0 1rem rgba(247, 201, 81, 0.56);
  animation: load-beacon 1.8s ease-in-out infinite;
}
.archive-load-more button {
  padding: 0.45rem 0.75rem;
  border: 1px solid rgba(247, 201, 81, 0.4);
  border-radius: 999px;
  color: #f7c951;
  background: rgba(6, 29, 40, 0.62);
  font: inherit;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    background-color 0.2s ease,
    transform 0.2s cubic-bezier(0.22, 1, 0.36, 1);
}
.archive-load-more button:hover,
.archive-load-more button:focus-visible {
  border-color: #f7c951;
  background: rgba(247, 201, 81, 0.12);
  transform: translateY(-0.08rem);
}
.archive-back-to-top {
  position: fixed;
  right: clamp(1rem, 2.5vw, 2.4rem);
  bottom: clamp(1rem, 3vw, 2.4rem);
  z-index: 12;
  display: grid;
  width: 3.1rem;
  height: 3.1rem;
  place-items: center;
  border: 1px solid rgba(247, 201, 81, 0.48);
  border-radius: 50%;
  color: #f7c951;
  background: rgba(6, 29, 40, 0.76);
  box-shadow: 0 0.8rem 2rem rgba(0, 0, 0, 0.24);
  backdrop-filter: blur(10px);
  cursor: pointer;
  transition:
    opacity 0.28s ease,
    transform 0.28s cubic-bezier(0.2, 0.76, 0.26, 1),
    border-color 0.2s ease,
    background-color 0.2s ease;
}
.archive-back-to-top span {
  display: block;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 1.25rem;
  line-height: 1;
  transform: translateY(0.06rem);
}
.archive-back-to-top:hover,
.archive-back-to-top:focus-visible {
  border-color: #fff0a7;
  background: rgba(22, 67, 72, 0.94);
  transform: translateY(-0.25rem);
}
.archive-back-to-top:focus-visible {
  outline: 2px solid rgba(134, 211, 198, 0.82);
  outline-offset: 3px;
}
@keyframes route-marker-drift {
  from {
    transform: translateX(-0.8rem);
  }
  to {
    transform: translateX(0.8rem);
  }
}
@keyframes route-marker-pulse {
  0%,
  100% {
    opacity: 0.36;
    transform: scale(0.88);
  }
  50% {
    opacity: 0.9;
    transform: scale(1.1);
  }
}
@keyframes route-marker-flow {
  to {
    stroke-dashoffset: -148;
  }
}
@keyframes route-marker-fix {
  0%,
  100% {
    opacity: 0.25;
    transform: scale(0.7);
  }
  50% {
    opacity: 0.9;
    transform: scale(1.35);
  }
}
@keyframes chart-drift {
  to {
    background-position:
      2rem 2rem,
      5rem 5rem,
      5rem 5rem;
  }
}
@keyframes atmosphere-drift {
  from {
    opacity: 0.48;
    transform: translate3d(-1.5rem, 0, 0);
  }
  to {
    opacity: 0.72;
    transform: translate3d(1.5rem, 1rem, 0);
  }
}
@keyframes atmosphere-scan {
  from {
    transform: translate3d(0, -18%, 0);
  }
  to {
    transform: translate3d(0, 18%, 0);
  }
}
@keyframes current-slip {
  from {
    transform: rotate(-8deg) translateX(-5%);
  }
  to {
    transform: rotate(-8deg) translateX(5%);
  }
}
@keyframes signal-blink {
  0%,
  100% {
    opacity: 0.2;
    transform: scaleX(0.45);
  }
  45%,
  62% {
    opacity: 0.95;
    transform: scaleX(1);
  }
}
@keyframes chart-sheet-drift {
  from {
    transform: translate3d(-1rem, var(--archive-counter-shift), 0);
  }
  to {
    transform: translate3d(2rem, calc(var(--archive-counter-shift) + 1rem), 0);
  }
}
@keyframes horizon-drift {
  from {
    transform: rotate(-8deg) translateX(0);
  }
  to {
    transform: rotate(-6deg) translateX(-4rem);
  }
}
@keyframes bearing-turn {
  to {
    transform: rotate(360deg);
  }
}
@keyframes chart-ping {
  0% {
    box-shadow: 0 0 0 0 rgba(247, 201, 81, 0.45);
  }
  70%,
  100% {
    box-shadow: 0 0 0 2.6rem rgba(247, 201, 81, 0);
  }
}
@keyframes route-current {
  to {
    stroke-dashoffset: -100;
  }
}
@keyframes route-fix-pulse {
  0%,
  100% {
    opacity: 0.28;
    filter: drop-shadow(0 0 0 transparent);
  }
  50% {
    opacity: 0.82;
    filter: drop-shadow(0 0 0.55rem currentColor);
  }
}
@keyframes depth-band-one {
  from {
    transform: translate3d(0, -1rem, 0) rotate(-1deg);
  }
  to {
    transform: translate3d(-2.5rem, 1.5rem, 0) rotate(1deg);
  }
}
@keyframes depth-band-two {
  from {
    transform: translate3d(-1.5rem, var(--archive-counter-shift), 0);
  }
  to {
    transform: translate3d(2rem, calc(var(--archive-counter-shift) - 1rem), 0);
  }
}
@keyframes depth-band-three {
  from {
    transform: translate3d(1rem, -0.6rem, 0) rotate(1deg);
  }
  to {
    transform: translate3d(-2rem, 0.9rem, 0) rotate(-1deg);
  }
}
@keyframes chart-sweep {
  from {
    transform: translateY(-15rem) rotate(-6deg);
  }
  to {
    transform: translateY(165rem) rotate(-6deg);
  }
}
@keyframes readout-drift {
  from {
    opacity: 0.28;
    transform: translateX(-0.8rem);
  }
  to {
    opacity: 0.72;
    transform: translateX(0.8rem);
  }
}
@keyframes masthead-signal {
  0%,
  100% {
    opacity: 0.25;
    transform: scaleX(0.28);
  }
  42%,
  62% {
    opacity: 1;
    transform: scaleX(1);
  }
}
@keyframes masthead-rise {
  from {
    opacity: 0;
    transform: translateY(1.4rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
@keyframes eyebrow-ping {
  0% {
    box-shadow: 0 0 0 0 rgba(247, 201, 81, 0.28);
  }
  70%,
  100% {
    box-shadow: 0 0 0 0.72rem rgba(247, 201, 81, 0);
  }
}
@keyframes title-settle {
  from {
    opacity: 0;
    transform: translateY(1rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
@keyframes ledger-arrive {
  from {
    opacity: 0;
    transform: translateX(1.4rem);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
@keyframes ledger-glint {
  0%,
  35% {
    opacity: 0;
    transform: translateX(-58%);
  }
  52% {
    opacity: 0.42;
  }
  82%,
  100% {
    opacity: 0;
    transform: translateX(58%);
  }
}
@keyframes ledger-cell {
  from {
    background-color: rgba(247, 201, 81, 0.12);
  }
  to {
    background-color: rgba(9, 43, 56, 0.82);
  }
}
@keyframes control-unfold {
  from {
    opacity: 0;
    clip-path: inset(0 100% 0 0);
  }
  to {
    opacity: 1;
    clip-path: inset(0);
  }
}
@keyframes rail-rise {
  from {
    opacity: 0;
    transform: translateY(1rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
@keyframes rail-scan {
  0%,
  10% {
    transform: translateY(-4rem);
    opacity: 0;
  }
  20%,
  72% {
    opacity: 1;
  }
  90%,
  100% {
    transform: translateY(29rem);
    opacity: 0;
  }
}
@keyframes month-heading-in {
  from {
    opacity: 0;
    transform: translateX(0.8rem);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
@keyframes month-current {
  from {
    opacity: 0.3;
    transform: translateX(-3%);
  }
  to {
    opacity: 0.78;
    transform: translateX(3%);
  }
}
@keyframes month-orbit {
  to {
    transform: rotate(360deg);
  }
}
@keyframes timeline-scan {
  0% {
    transform: translateY(-5rem);
    opacity: 0;
  }
  12% {
    opacity: 1;
  }
  72% {
    opacity: 1;
  }
  100% {
    transform: translateY(42rem);
    opacity: 0;
  }
}
@keyframes node-ripple {
  from {
    opacity: 0.8;
    transform: scale(0.45);
  }
  to {
    opacity: 0;
    transform: scale(1.8);
  }
}
@keyframes empty-radar {
  to {
    transform: rotate(360deg);
  }
}
@keyframes load-line {
  from {
    opacity: 0.38;
    transform: scaleX(0.62);
  }
  to {
    opacity: 0.9;
    transform: scaleX(1);
  }
}
@keyframes load-beacon {
  0%,
  100% {
    opacity: 0.35;
    transform: translateY(0) scale(0.78);
  }
  50% {
    opacity: 1;
    transform: translateY(-0.12rem) scale(1);
  }
}
@media (max-width: 900px) {
  .article-page {
    padding-top: 8.5rem;
  }
  .archive-masthead {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  .archive-ledger {
    max-width: 31rem;
  }
  .archive-layout {
    gap: 2rem;
  }
}
@media (max-width: 680px) {
  .article-page {
    padding-top: 9.5rem;
  }
  .archive-route-field {
    opacity: 0.78;
  }
  .chart-readout {
    display: none;
  }
  .chart-current {
    width: 150%;
    height: 6rem;
    opacity: 0.25;
  }
  .chart-signal,
  .chart-depth-band-three {
    display: none;
  }
  .chart-depth-band-one {
    top: 31rem;
    width: 88%;
  }
  .chart-depth-band-two {
    width: 92%;
  }
  .archive-route-marker {
    width: 12rem;
    opacity: 0.58;
  }
  .route-marker-trail {
    width: 21rem;
  }
  .route-marker-readout {
    display: none;
  }
  .archive-masthead,
  .archive-workspace {
    width: min(100% - 2rem, 42rem);
  }
  .archive-masthead {
    padding-top: 1.8rem;
  }
  .archive-eyebrow {
    margin-top: 2.6rem;
  }
  .archive-ledger {
    grid-template-columns: repeat(2, 1fr);
  }
  .archive-ledger div:last-child {
    grid-column: 1 / -1;
  }
  .archive-control-bar {
    align-items: flex-start;
    flex-direction: column;
    padding: 0.8rem 0;
  }
  .archive-locate-meter {
    width: 100%;
    justify-content: start;
  }
  .archive-view-switcher {
    min-height: 2.4rem;
  }
  .archive-layout {
    grid-template-columns: 1fr;
    padding-top: 1.6rem;
  }
  .archive-filter-rail {
    position: static;
    display: grid;
    grid-template-columns: 1fr;
    max-height: none;
    overflow: visible;
    overscroll-behavior: auto;
    padding: 0 0 1.4rem;
    border-right: 0;
    border-bottom: 1px solid rgba(207, 225, 217, 0.14);
  }
  .archive-filter-rail::before {
    inset: -0.7rem -0.7rem 0;
    border-right: 1px solid rgba(207, 225, 217, 0.08);
  }
  .archive-filter-rail::after {
    top: auto;
    right: auto;
    bottom: -1px;
    left: 0;
    width: 4rem;
    height: 1px;
    animation-name: rail-scan-mobile;
  }
  .filter-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.2rem 0.75rem;
  }
  .filter-group + .filter-group {
    margin-top: 1.5rem;
  }
  .filter-group > p {
    width: 100%;
  }
  .filter-group button {
    width: auto;
  }
  .archive-month-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .archive-month-count {
    justify-content: start;
  }
  .filter-group button:hover,
  .filter-group button.active {
    padding-left: 0;
  }
  .archive-groups {
    gap: 2.4rem;
  }
  .archive-month-group::before {
    inset: -0.6rem -0.8rem;
  }
  .archive-timeline::before {
    left: 4.4rem;
  }
  .archive-entry {
    grid-template-columns: 3.4rem 2rem minmax(0, 1fr);
  }
  .archive-entry time {
    font-size: 0.65rem;
  }
  .archive-entry footer {
    align-items: flex-start;
    flex-direction: column;
  }
}
@keyframes rail-scan-mobile {
  0%,
  10% {
    transform: translateX(-4rem);
    opacity: 0;
  }
  20%,
  72% {
    opacity: 1;
  }
  90%,
  100% {
    transform: translateX(calc(100vw - 6rem));
    opacity: 0;
  }
}
@media (prefers-reduced-motion: reduce) {
  .article-page::before,
  .article-page::after,
  .archive-visual-stack,
  .archive-visual-layer,
  .sea-chart-motion,
  .sea-chart-motion::before,
  .sea-chart-motion::after,
  .chart-current,
  .chart-signal::before,
  .chart-signal::after,
  .chart-bearing,
  .chart-ping,
  .route-flow,
  .route-fix,
  .chart-depth-band,
  .chart-sweep,
  .chart-readout,
  .archive-route-marker,
  .route-marker-flow,
  .route-marker-fix,
  .route-marker-orbit,
  .archive-masthead-copy,
  .archive-masthead::before,
  .archive-masthead h1,
  .archive-eyebrow span,
  .archive-ledger,
  .archive-ledger::before,
  .archive-ledger div,
  .archive-control-bar,
  .archive-filter-rail,
  .archive-filter-rail::after,
  .archive-month-group::before,
  .archive-month-group::after,
  .archive-month-heading,
  .archive-timeline::after,
  .archive-node::after,
  .article-empty-state::before,
  .archive-load-more::before,
  .archive-load-more::after {
    animation: none;
  }
  .archive-route-field,
  .archive-visual-stack,
  .archive-visual-layer,
  .archive-visual-layer.active,
  .article-page::before,
  .chart-depth-band-two,
  .chart-depth-band-three,
  .sea-chart-motion::before,
  .sea-chart-motion::after,
  .chart-current {
    transform: none;
  }
  .article-back-link::before,
  .archive-visual-layer,
  .archive-view-switcher a::after,
  .archive-view-switcher a,
  .filter-group button,
  .filter-group button::before,
  .filter-rail-heading button,
  .archive-ledger div,
  .archive-entry,
  .archive-entry::before,
  .archive-entry::after,
  .archive-entry time,
  .archive-node,
  .archive-entry-body,
  .archive-entry h2 a,
  .article-tags b {
    transition: none;
  }
  .archive-entry {
    opacity: 1;
    transform: none;
  }
}
</style>
