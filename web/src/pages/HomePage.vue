<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import OceanIcon from "../components/OceanIcon.vue";
import { fetchAboutProfile, type AboutProfile } from "../api/about";
import { fetchArticles, type Article, type ArticleListStats } from "../api/articles";
import { fetchSiteSettings, type SiteSettings } from "../api/site-settings";
import { fetchVisitorLocation, type VisitorLocation } from "../api/visitor-location";
import { fetchNotes, fetchSeries, type Note, type Series } from "../api/content";
import { fetchGallery } from "../api/gallery";
import { type IconName } from "../icons";

const fallbackSettings: SiteSettings = {
  site_subtitle: "自由、梦想、伙伴，这里记录我向前航行的每一步。",
  hero_image_url: "https://images.hdqwalls.com/download/one-piece-anime-artwork-i6-2560x1440.jpg",
  nav_brand: "某某某的个人空间",
  dashboard_show_entry: true,
  dashboard_years: [2024, 2025, 2026],
  icp_filing_number: null,
  police_filing_number: null,
  site_launched_on: "2026-01-01",
  owner_avatar_url: `${import.meta.env.BASE_URL}owner-avatar.jpg`,
  owner_location_name: "未设置站长地址",
  owner_latitude: null,
  owner_longitude: null,
  visual_assets: [],
  quotes: [
    {
      author: "路飞",
      text: "我是要成为海贼王的男人。",
    }
  ],
};

const fallbackProfile: AboutProfile = {
  id: 0,
  display_name: "站长",
  role: "全栈开发者 / 独立创作者",
  headline: "把复杂问题拆成清晰产品，也把沿途思考写成长期记录。",
  bio: "这里收纳技术实践、项目复盘、个人档案和正在建设中的博客系统。前台负责阅读体验，后台负责内容维护，后端负责把文章、资料和视觉资产稳定送达。",
  avatar_url: `${import.meta.env.BASE_URL}owner-avatar.jpg`,
  resume_url: "",
  resume_filename: "",
  status_text: "持续记录中，欢迎交流",
  email: null,
  location_name: "位置待维护",
  location_longitude: null,
  location_latitude: null,
  metrics: [],
  work_experiences: [],
  project_experiences: [],
  skills: [],
  social_links: [],
  interests: ["写作", "产品", "前端", "后端"],
  site_title: "关于本站",
  site_description: "",
  site_launched_at: "持续迭代中",
  site_stack: ["Vue 3", "TypeScript", "FastAPI", "SQLAlchemy", "MySQL"],
  site_repository_url: null,
  updated_at: new Date().toISOString(),
};

const fallbackArticleStats: ArticleListStats = {
  categories: [],
  tags: [],
  months: [],
};

const route = useRoute();
const isHome = computed(() => route.path === "/");
defineOptions({ name: "HomePage" });
const settings = ref<SiteSettings>(fallbackSettings);
const homeArticles = ref<Article[]>([]);
const homeArticleStats = ref<ArticleListStats>(fallbackArticleStats);
const homeArticleTotal = ref(0);
const homeArticlesLoading = ref(false);
const homeArticlesStatus = ref("最近文章");
const homeProfile = ref<AboutProfile>(fallbackProfile);
const homeSeries = ref<Series[]>([]);
const homeNotes = ref<Note[]>([]);
const homeGalleryEntryVisible = ref(true);
const homeDiscoveryRoot = ref<HTMLElement | null>(null);
const activeQuoteIndex = ref(0);
const typedCharacters = ref(0);
const scrollProgress = ref(0);
const heroParallax = ref(0);
const visitorLocation = ref<VisitorLocation | null>(null);
const visitorLocationStatus = ref("正在查询访客位置");
const clockNow = ref(new Date());
const commandLinks = [
  {
    label: "全部文章",
    caption: "按时间回看全部记录",
    to: { path: "/articles", query: { view: "archive" } },
    tone: "brass",
    icon: "archive" as IconName,
  },
  {
    label: "文章大屏",
    caption: "查看全站航行数据",
    to: "/dashboard",
    tone: "tide",
    icon: "views" as IconName,
  },
  {
    label: "3D 展厅",
    caption: "漫游人物档案",
    to: "/gallery",
    tone: "sage",
    icon: "gallery" as IconName,
  },
  {
    label: "留言板",
    caption: "留下你的航海信号",
    to: "/guestbook",
    tone: "coral",
    icon: "comment" as IconName,
  },
];

let quoteTimer: number | undefined;
let switchTimer: number | undefined;
let clockTimer: number | undefined;
let scrollFrame: number | undefined;
let cardObserver: IntersectionObserver | undefined;
let discoveryObserver: IntersectionObserver | undefined;
let homeSession = 0;

const activeQuote = computed(
  () => settings.value.quotes[activeQuoteIndex.value] ?? fallbackSettings.quotes[0],
);
const ownerAvatarUrl = computed(
  () => settings.value.owner_avatar_url || fallbackSettings.owner_avatar_url,
);
const ownerLocationName = computed(
  () => settings.value.owner_location_name || fallbackSettings.owner_location_name,
);
const typedQuote = computed(() => activeQuote.value.text.slice(0, typedCharacters.value));
const featuredArticle = computed(() => homeArticles.value[0] ?? null);
const secondaryArticles = computed(() => homeArticles.value.slice(1, 4));
const articleCategories = computed(() => homeArticleStats.value.categories.slice(0, 5));
const articleTags = computed(() => homeArticleStats.value.tags.slice(0, 12));
const featuredSeries = computed(() => homeSeries.value.slice(0, 2));
const latestNotes = computed(() => homeNotes.value.slice(0, 3));
const visibleCommandLinks = computed(() =>
  commandLinks.filter((command) => {
    if (command.to === "/gallery") return homeGalleryEntryVisible.value;
    if (command.to === "/dashboard") return settings.value.dashboard_show_entry;
    return true;
  }),
);
const currentTimeText = computed(() =>
  new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(clockNow.value),
);
const currentTimeCharacters = computed(() => currentTimeText.value.split(""));
const currentDateText = computed(() =>
  new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(clockNow.value),
);
const siteRunningDaysText = computed(() => {
  const [year, month, day] = settings.value.site_launched_on.split("-").map(Number);
  const launchedOn = Date.UTC(year, month - 1, day);
  const launchedDate = new Date(launchedOn);
  const validDate =
    Number.isInteger(year) &&
    Number.isInteger(month) &&
    Number.isInteger(day) &&
    launchedDate.getUTCFullYear() === year &&
    launchedDate.getUTCMonth() === month - 1 &&
    launchedDate.getUTCDate() === day;

  if (!validDate) return "1";

  const today = Date.UTC(
    clockNow.value.getFullYear(),
    clockNow.value.getMonth(),
    clockNow.value.getDate(),
  );
  return String(Math.max(1, Math.floor((today - launchedOn) / 86_400_000) + 1));
});
const latestArticleDate = computed(() =>
  featuredArticle.value
    ? formatArticleDate(featuredArticle.value)
    : homeArticlesLoading.value
      ? "读取中"
      : "等待首篇文章",
);
const writingStatusText = computed(() => {
  if (homeArticleTotal.value > 0) return `已收录 ${homeArticleTotal.value} 篇文章`;
  if (homeArticlesLoading.value) return "正在整理最近内容";
  return "持续记录技术与生活";
});
const visitorLocationText = computed(() => {
  if (!visitorLocation.value?.location_available) {
    return visitorLocationStatus.value;
  }

  return [visitorLocation.value.city, visitorLocation.value.region, visitorLocation.value.country]
    .filter(Boolean)
    .join(" · ");
});
const visitorIpText = computed(() => visitorLocation.value?.ip ?? "IP 查询中");
const distanceText = computed(() => {
  const distance = visitorLocation.value?.distance_km;
  if (distance === null || distance === undefined) {
    return settings.value.owner_latitude === null ? "站长坐标待维护" : "距离测算中";
  }

  return distance >= 100
    ? `你距离站长约 ${Math.round(distance)} 公里`
    : `你距离站长约 ${distance.toFixed(1)} 公里`;
});
function formatArticleDate(article: Article) {
  const value = article.published_at ?? article.created_at;
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
  })
    .format(new Date(value))
    .replace("/", ".");
}

function formatFullDate(value: string | null) {
  if (!value) return "时间待定";
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

function noteExcerpt(markdown: string) {
  return markdown
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/[#>*_`[\]()!-]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 88);
}

function createEmptyArticleStats(): ArticleListStats {
  return {
    categories: [],
    tags: [],
    months: [],
  };
}

async function loadSettings() {
  try {
    settings.value = await fetchSiteSettings();
  } catch {
    settings.value = fallbackSettings;
  }
}

async function loadHomeArticles(session: number) {
  homeArticlesLoading.value = true;
  homeArticlesStatus.value = "最近文章";
  try {
    const result = await fetchArticles({ page: 1, page_size: 6 });
    if (session !== homeSession || !isHome.value) return;
    homeArticles.value = result.items;
    homeArticleStats.value = result.stats;
    homeArticleTotal.value = result.total;
    homeArticlesStatus.value = result.total ? "最近文章" : "等待第一篇文章";
  } catch {
    if (session !== homeSession || !isHome.value) return;
    homeArticles.value = [];
    homeArticleStats.value = createEmptyArticleStats();
    homeArticleTotal.value = 0;
    homeArticlesStatus.value = "最近文章";
  } finally {
    if (session === homeSession && isHome.value) {
      homeArticlesLoading.value = false;
    }
  }
}

async function loadHomeProfile(session: number) {
  try {
    const profile = await fetchAboutProfile();
    if (session !== homeSession || !isHome.value) return;
    homeProfile.value = profile;
  } catch {
    if (session !== homeSession || !isHome.value) return;
    homeProfile.value = fallbackProfile;
  }
}

async function loadHomeSeriesAndNotes(session: number) {
  const [seriesResult, notesResult] = await Promise.allSettled([
    fetchSeries(),
    fetchNotes({ page: 1, page_size: 3 }),
  ]);
  if (session !== homeSession || !isHome.value) return;
  homeSeries.value = seriesResult.status === "fulfilled" ? seriesResult.value.items : [];
  homeNotes.value = notesResult.status === "fulfilled" ? notesResult.value.items : [];
}

async function loadHomeContent(session: number) {
  await Promise.allSettled([
    loadHomeArticles(session),
    loadHomeProfile(session),
    loadHomeGalleryVisibility(session),
  ]);
}

async function loadHomeGalleryVisibility(session: number) {
  try {
    const result = await fetchGallery();
    if (session === homeSession && isHome.value) {
      homeGalleryEntryVisible.value = result.settings.show_entry;
    }
  } catch {
    homeGalleryEntryVisible.value = true;
  }
}

function observeHomeDiscovery(session: number) {
  discoveryObserver?.disconnect();
  if (!homeDiscoveryRoot.value || typeof IntersectionObserver === "undefined") {
    void loadHomeSeriesAndNotes(session);
    return;
  }
  discoveryObserver = new IntersectionObserver(
    (entries) => {
      if (!entries.some((entry) => entry.isIntersecting)) return;
      discoveryObserver?.disconnect();
      void loadHomeSeriesAndNotes(session).then(async () => {
        await nextTick();
        if (session === homeSession && isHome.value) observeCards();
      });
    },
    { rootMargin: "320px 0px" },
  );
  discoveryObserver.observe(homeDiscoveryRoot.value);
}

async function loadVisitorLocation() {
  try {
    visitorLocation.value = await fetchVisitorLocation();
    visitorLocationStatus.value = visitorLocation.value.location_available
      ? "位置已同步"
      : "位置暂不可用";
  } catch {
    visitorLocationStatus.value = "位置查询失败";
  }
}

function startTypingCycle() {
  window.clearInterval(quoteTimer);
  window.clearTimeout(switchTimer);

  typedCharacters.value = 0;
  quoteTimer = window.setInterval(() => {
    if (typedCharacters.value >= activeQuote.value.text.length) {
      window.clearInterval(quoteTimer);
      switchTimer = window.setTimeout(() => {
        activeQuoteIndex.value = (activeQuoteIndex.value + 1) % settings.value.quotes.length;
        startTypingCycle();
      }, 2600);
      return;
    }
    typedCharacters.value += 1;
  }, 130);
}

function startClock() {
  clockNow.value = new Date();
  window.clearInterval(clockTimer);
  clockTimer = window.setInterval(() => {
    clockNow.value = new Date();
  }, 1000);
}

function handleScroll() {
  const currentY = window.scrollY;
  if (scrollFrame !== undefined) {
    return;
  }

  scrollFrame = window.requestAnimationFrame(() => {
    const scrollableHeight = document.documentElement.scrollHeight - window.innerHeight;
    scrollProgress.value = scrollableHeight > 0 ? Math.min(currentY / scrollableHeight, 1) : 0;
    heroParallax.value = Math.min(currentY * 0.08, 64);
    scrollFrame = undefined;
  });
}

function observeCards() {
  const board = document.querySelector<HTMLElement>(".home-content-flow");
  if (!board) return;

  board.classList.add("cards-motion-ready");
  cardObserver ??= new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const card = entry.target as HTMLElement;
        card.classList.toggle("card-in-view", entry.isIntersecting);
        if (!entry.isIntersecting || card.classList.contains("card-visible")) return;

        card.classList.add("card-revealing", "card-visible");
        const handleRevealEnd = (event: AnimationEvent) => {
          if (event.target !== card) return;
          card.classList.remove("card-revealing");
          card.removeEventListener("animationend", handleRevealEnd);
        };
        card.addEventListener("animationend", handleRevealEnd);
      });
    },
    { threshold: 0.18, rootMargin: "0px 0px -6% 0px" },
  );

  board
    .querySelectorAll<HTMLElement>(".home-reveal:not([data-reveal-observed])")
    .forEach((item, index) => {
      item.dataset.revealObserved = "true";
      item.style.setProperty("--reveal-delay", `${(index % 4) * 55}ms`);
      cardObserver?.observe(item);
    });
}

async function initializeHome() {
  const session = ++homeSession;
  await loadSettings();
  if (session !== homeSession || !isHome.value) return;

  void loadVisitorLocation();
  void loadHomeContent(session).then(async () => {
    await nextTick();
    if (session === homeSession && isHome.value) {
      observeCards();
    }
  });
  startClock();
  startTypingCycle();
  await nextTick();
  if (session !== homeSession || !isHome.value) return;

  observeCards();
  observeHomeDiscovery(session);
  window.addEventListener("scroll", handleScroll, { passive: true });
  handleScroll();
}

function disposeHome() {
  homeSession += 1;
  window.removeEventListener("scroll", handleScroll);
  window.clearInterval(quoteTimer);
  window.clearTimeout(switchTimer);
  window.clearInterval(clockTimer);
  quoteTimer = undefined;
  switchTimer = undefined;
  clockTimer = undefined;
  if (scrollFrame !== undefined) {
    window.cancelAnimationFrame(scrollFrame);
    scrollFrame = undefined;
  }
  cardObserver?.disconnect();
  cardObserver = undefined;
  discoveryObserver?.disconnect();
  discoveryObserver = undefined;
}

onMounted(() => {
  if (isHome.value) {
    void initializeHome();
  }
});

watch(isHome, (home) => {
  disposeHome();
  if (home) {
    void initializeHome();
  }
});

onBeforeUnmount(() => {
  disposeHome();
});
</script>

<template>
  <div
    v-if="isHome"
    class="page-shell"
    :style="{ '--home-background-image': `url(${settings.hero_image_url})` }"
  >
    <section id="hero" class="hero">
      <div class="hero-overlay">
        <div class="hero-copy" :style="{ transform: `translate3d(0, ${heroParallax}px, 0)` }">
          <p class="hero-subtitle">{{ settings.site_subtitle }}</p>
          <div class="quote-box">
            <p class="quote-line">{{ typedQuote }}<span class="cursor">|</span></p>
            <p class="quote-author">{{ activeQuote.author }}</p>
          </div>
        </div>
        <a class="scroll-indicator" href="#articles" aria-label="继续往下看" title="继续往下看">
          <span class="scroll-arrow" aria-hidden="true"></span>
        </a>
      </div>
    </section>

    <main class="content-shell">
      <section id="articles" class="content-section cards-section">
        <div class="compact-board-heading text-left">
          <h2>航海日志</h2>
          <span>{{ homeArticlesStatus }} · {{ homeArticleTotal }} 篇记录</span>
        </div>

        <div class="home-content-flow">
          <div class="home-lead-row">
            <RouterLink
              v-if="featuredArticle"
              class="home-featured-log home-reveal"
              :to="{ path: `/articles/${featuredArticle.slug}` }"
            >
              <div class="home-panel-heading">
                <strong>最新文章</strong>
                <time><OceanIcon name="time" :size="18" />{{ formatFullDate(featuredArticle.published_at ?? featuredArticle.created_at) }}</time>
              </div>
              <h3>{{ featuredArticle.title }}</h3>
              <p>{{ featuredArticle.summary || "打开文章查看完整记录。" }}</p>
              <span class="home-featured-meta"><OceanIcon name="views" :size="18" />{{ featuredArticle.views }} 阅读 <i></i> {{ featuredArticle.likes }} 喜欢</span>
            </RouterLink>
            <article v-else class="home-featured-log home-reveal">
              <div class="home-panel-heading"><strong>最新文章</strong></div>
              <h3>{{ homeArticlesLoading ? "正在整理最近内容" : homeArticlesStatus }}</h3>
              <p>有新文章时会出现在这里。</p>
              <RouterLink :to="{ path: '/articles', query: { view: 'archive' } }">进入全部文章</RouterLink>
            </article>

            <aside class="home-voyage-status home-reveal" aria-label="航行状态">
              <div class="home-status-heading">
                <span class="signal-light" aria-hidden="true"></span>
                <h3>航行状态</h3>
              </div>
              <strong class="home-writing-status">{{ writingStatusText }}</strong>
              <div class="home-clock-line">
                <strong class="time-digits" :aria-label="currentTimeText">
                  <span
                    v-for="(character, index) in currentTimeCharacters"
                    :key="`${index}-${character}`"
                    aria-hidden="true"
                    :style="{ '--digit-index': index }"
                  >{{ character }}</span>
                </strong>
                <span>{{ currentDateText }}</span>
              </div>
              <div class="home-status-grid">
                <span><b>{{ siteRunningDaysText }}</b> 天运行</span>
                <span><b>{{ homeArticleTotal }}</b> 篇记录</span>
                <span><b>{{ latestArticleDate }}</b> 最近更新</span>
              </div>
              <div class="home-visitor-line">
                <span><OceanIcon name="location" :size="18" />欢迎靠岸 · {{ visitorLocationText }}</span>
                <small>{{ distanceText }} · {{ visitorIpText }}</small>
              </div>
            </aside>
          </div>

          <section class="home-next-stops home-reveal" aria-labelledby="home-next-stops-title">
            <div class="home-next-stops-heading"><p class="panel-kicker">继续航行</p><h3 id="home-next-stops-title">下一站</h3><small>从这里选择你的阅读方式</small></div>
            <RouterLink
              v-for="command in visibleCommandLinks"
              :key="command.label"
              :class="`tone-${command.tone}`"
              :to="command.to"
            >
              <OceanIcon class="home-route-icon" :name="command.icon" :size="30" />
              <span><strong>{{ command.label }}</strong><small>{{ command.caption }}</small></span>
            </RouterLink>
          </section>

          <div class="home-reading-layout">
            <section class="home-reading-feed home-reveal" aria-labelledby="home-reading-title">
              <div class="home-section-heading">
                <div><p class="panel-kicker">航海日志</p><h3 id="home-reading-title">最近记录</h3></div>
                <RouterLink :to="{ path: '/articles', query: { view: 'archive' } }">全部文章</RouterLink>
              </div>
              <RouterLink
                v-for="(article, index) in secondaryArticles"
                :key="article.id"
                class="home-article-row"
                :to="{ path: `/articles/${article.slug}` }"
              >
                <span class="home-article-index">{{ String(index + 1).padStart(2, "0") }}</span>
                <time><OceanIcon name="time" :size="16" />{{ formatArticleDate(article) }}</time>
                <div><strong>{{ article.title }}</strong><small>{{ article.category }}</small></div>
                <span class="home-article-likes">{{ article.likes }} 喜欢</span>
              </RouterLink>
              <p v-if="!secondaryArticles.length" class="compact-empty">更多文章正在靠岸。</p>
            </section>

            <aside class="home-index-panel home-reveal" aria-label="文章索引">
              <div class="home-section-heading"><div><p class="panel-kicker">航线索引</p><h3>分类与标签</h3></div><RouterLink :to="{ path: '/articles', query: { view: 'categories' } }">全部分类</RouterLink></div>
              <div v-if="articleCategories.length" class="home-category-lines">
                <RouterLink v-for="category in articleCategories" :key="category.name" :to="{ path: '/articles', query: { view: 'categories', category: category.name } }">
                  <span>{{ category.name }}</span><b>{{ category.count }}</b>
                </RouterLink>
              </div>
              <p v-else class="compact-empty">分类等待文章写入。</p>
              <div v-if="articleTags.length" class="home-tag-line">
                <RouterLink v-for="tag in articleTags.slice(0, 8)" :key="tag.name" :to="{ path: '/articles', query: { view: 'tags', tag: tag.name } }">#{{ tag.name }}</RouterLink>
              </div>
            </aside>
          </div>

          <div ref="homeDiscoveryRoot" class="home-lower-deck">
            <div class="home-discovery-layout">
              <section class="home-signal-panel home-reveal">
                <div class="home-section-heading"><h3>专题航线</h3><RouterLink to="/series">全部专题</RouterLink></div>
                <div v-if="featuredSeries.length" class="home-signal-list">
                  <RouterLink v-for="(series, index) in featuredSeries" :key="series.id" :to="`/series/${series.slug}`">
                    <span>{{ String(index + 1).padStart(2, "0") }}</span><strong>{{ series.title }}</strong><small>{{ series.description || "进入专题连续阅读" }}</small>
                  </RouterLink>
                </div>
                <p v-else class="compact-empty">专题航线正在整理中。</p>
              </section>
              <section class="home-signal-panel home-reveal">
                <div class="home-section-heading"><h3>最近动态</h3><RouterLink to="/notes">全部动态</RouterLink></div>
                <div v-if="latestNotes.length" class="home-signal-list home-note-list">
                  <RouterLink v-for="note in latestNotes" :key="note.id" :to="`/notes/${note.slug}`">
                    <span class="signal-light" aria-hidden="true"></span><strong>{{ noteExcerpt(note.content_markdown) }}</strong>
                  </RouterLink>
                </div>
                <p v-else class="compact-empty">最近还没有新的动态信号。</p>
              </section>
              <section class="home-signal-panel home-guestbook-panel home-reveal">
                <div class="home-section-heading"><h3>留言航标</h3><RouterLink to="/guestbook">进入留言板</RouterLink></div>
                <p>把想说的话留在这段航程里，审核通过后会成为日志的一部分。</p>
                <RouterLink class="home-guestbook-action" to="/guestbook"><OceanIcon name="comment" :size="22" />留下第一枚航标</RouterLink>
              </section>
            </div>

            <RouterLink class="home-profile-strip home-reveal" to="/about">
              <span class="home-profile-avatar">
                <img :src="ownerAvatarUrl" alt="站长头像" />
              </span>
              <span class="home-profile-copy"><span class="home-profile-name">关于 · {{ homeProfile.display_name }}</span><strong>{{ homeProfile.role }}</strong><small>{{ homeProfile.headline }}</small></span>
              <span class="home-profile-facts"><b>驻泊地 · {{ ownerLocationName }}</b><small>{{ settings.nav_brand }}</small></span>
              <span class="home-profile-action">查看档案</span>
            </RouterLink>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.page-shell {
  color: #fef9ef;
  background:
    linear-gradient(rgba(7, 18, 29, 0.4), rgba(7, 18, 29, 0.86)),
    var(--home-background-image);
  background-attachment: fixed;
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
}

.hero {
  position: relative;
  overflow: hidden;
  min-height: 100vh;
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
}

.hero-overlay {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  padding: 6.5rem 1.5rem 3rem;
  text-align: center;
}

.hero-copy {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.3rem;
  width: 100%;
  transition: transform 0.12s linear;
  will-change: transform;
}

.hero-copy > * {
  animation: hero-rise 0.9s both;
}

.hero-copy > :nth-child(1) {
  animation-delay: 0.1s;
}

.hero-copy > :nth-child(2) {
  animation-delay: 0.22s;
}

.hero-subtitle {
  margin: 0;
  max-width: 40rem;
  font-size: 1.35rem;
  line-height: 1.8;
  color: rgba(255, 248, 233, 0.9);
  text-shadow: 0 0.5rem 1.5rem rgba(0, 0, 0, 0.28);
}

.quote-box {
  min-height: 5.4rem;
  padding: 1rem 1.4rem;
  border-block: 1px solid rgba(255, 249, 239, 0.16);
  background: linear-gradient(90deg, transparent, rgba(7, 19, 31, 0.34), transparent);
}

.quote-line {
  margin: 0;
  font-size: 1.65rem;
  font-weight: 600;
  line-height: 1.55;
  text-shadow: 0 0.45rem 1.2rem rgba(0, 0, 0, 0.35);
}

.cursor {
  display: inline-block;
  margin-left: 0.2rem;
  animation: blink 0.95s steps(1) infinite;
}

.quote-author {
  display: inline-block;
  margin-top: 0.65rem;
  color: #ffd36f;
  font-size: 0.95rem;
}

.scroll-indicator {
  display: inline-grid;
  place-items: center;
  margin-top: 0;
  margin-bottom: 6rem;
  color: #ffffff;
  text-decoration: none;
  animation: hero-rise 0.9s both;
  transition: color 0.25s ease;
}

.scroll-indicator:hover {
  color: #ffd36f;
}

.scroll-arrow {
  margin-top: 0;
  width: 0.7rem;
  height: 0.7rem;
  border-right: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  transform: translateY(-0.28rem) rotate(45deg);
  animation: arrow-settle 0.8s cubic-bezier(0.22, 1, 0.36, 1) 1.4s both;
}

.content-shell {
  --home-ink: #fff8e6;
  --home-muted: rgba(255, 248, 230, 0.66);
  --home-soft: rgba(255, 248, 230, 0.38);
  --home-brass: #f7c951;
  --home-coral: #e66f52;
  --home-tide: #83d7cb;
  --home-sage: #c8d9a4;
  --home-deep: #061722;
  --home-panel: rgba(5, 21, 31, 0.74);
  --card-line: rgba(166, 224, 218, 0.2);
  --card-line-strong: rgba(247, 201, 81, 0.46);
  --card-ease: cubic-bezier(0.22, 1, 0.36, 1);
  position: relative;
  overflow: hidden;
  isolation: isolate;
  background:
    repeating-linear-gradient(
      90deg,
      rgba(255, 248, 230, 0.035) 0 1px,
      transparent 1px 5.5rem
    ),
    repeating-linear-gradient(
      0deg,
      rgba(131, 215, 203, 0.028) 0 1px,
      transparent 1px 4.25rem
    ),
    linear-gradient(152deg, #061722 0%, #092331 42%, #171e26 70%, #31221d 100%);
}

.content-shell::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -2;
  pointer-events: none;
  background:
    linear-gradient(118deg, transparent 0 28%, rgba(247, 201, 81, 0.06) 28.2% 28.5%, transparent 28.7% 100%),
    linear-gradient(64deg, transparent 0 46%, rgba(131, 215, 203, 0.08) 46.2% 46.45%, transparent 46.7% 100%),
    repeating-linear-gradient(
      134deg,
      transparent 0 4.6rem,
      rgba(255, 248, 230, 0.026) 4.65rem 4.72rem,
      transparent 4.78rem 9.4rem
    );
  mask-image: linear-gradient(180deg, transparent, #000 7rem, #000 88%, transparent);
}

.content-shell::after {
  content: "";
  position: absolute;
  top: 12rem;
  right: -10%;
  z-index: -1;
  width: 120%;
  height: 1px;
  pointer-events: none;
  background: linear-gradient(90deg, transparent, rgba(247, 201, 81, 0.55), transparent);
  box-shadow:
    0 12rem 0 rgba(131, 215, 203, 0.18),
    0 27rem 0 rgba(230, 111, 82, 0.14),
    0 44rem 0 rgba(200, 217, 164, 0.16);
  transform: rotate(-7deg);
  animation: chart-current-drift 16s ease-in-out infinite alternate;
}

.content-section {
  position: relative;
  z-index: 1;
  max-width: 1180px;
  margin: 0 auto;
  padding: 6.8rem 1.5rem;
}

.section-heading {
  max-width: 42rem;
}

.section-heading h2 {
  margin: 0;
  font-family: var(--display-font);
  font-size: 2.75rem;
  line-height: 1.16;
}

.section-heading p:last-child {
  margin: 1rem 0 0;
  color: rgba(255, 249, 239, 0.72);
  line-height: 1.85;
}


.panel-kicker {
  margin: 0 0 0.75rem;
  color: var(--home-brass);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.18em;
}

.panel-kicker {
  margin-bottom: 0.85rem;
  color: var(--home-tide);
}

.visitor-panel {
  min-height: 19rem;
  background:
    linear-gradient(150deg, rgba(131, 215, 203, 0.16), transparent 55%),
    rgba(7, 26, 36, 0.78);
}

.signal-light {
  display: inline-block;
  width: 0.45rem;
  aspect-ratio: 1;
  border-radius: 50%;
  background: var(--home-brass);
  box-shadow: 0 0 0 0.35rem rgba(247, 201, 81, 0.13);
  animation: signal-pulse 2.7s ease-in-out infinite;
}

.visitor-panel h3 {
  position: relative;
  z-index: 1;
  margin: 1.25rem 0 0;
  font-family: var(--display-font);
  font-size: 1.55rem;
}

.compact-empty {
  position: relative;
  z-index: 1;
  margin: 1rem 0 0;
  color: var(--home-muted);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.82rem;
}

@keyframes chart-current-drift {
  from {
    transform: rotate(-7deg) translateX(-2rem);
  }
  to {
    transform: rotate(-5deg) translateX(2rem);
  }
}

@keyframes hero-rise {
  from {
    opacity: 0;
    transform: translateY(1.2rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes arrow-settle {
  from {
    transform: translateY(-0.35rem) rotate(45deg);
  }
  to {
    transform: translateY(0) rotate(45deg);
  }
}

@keyframes signal-pulse {
  0%,
  100% {
    opacity: 0.65;
    box-shadow: 0 0 0 0.2rem rgba(255, 211, 111, 0.08);
  }
  50% {
    opacity: 1;
    box-shadow: 0 0 0 0.45rem rgba(255, 211, 111, 0.18);
  }
}

@keyframes blink {
  0%,
  50% {
    opacity: 1;
  }
  50.01%,
  100% {
    opacity: 0;
  }
}

@media (max-width: 980px) {
  .hero-subtitle {
    font-size: 1.1rem;
  }

  .quote-line {
    font-size: 1.25rem;
  }

  .section-heading h2 {
    font-size: 2rem;
  }

}

@media (max-width: 640px) {
  .content-section {
    padding: 4.8rem 1rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero-copy > *,
  .scroll-arrow,
  .content-shell::after,
  .signal-light {
    animation: none;
  }

  .hero-copy > * {
    opacity: 1;
  }


  .scroll-indicator {
    transition: none;
  }
}

.content-shell {
  --home-ink: #fff8e6;
  --home-muted: rgba(255, 248, 230, 0.66);
  --home-soft: rgba(255, 248, 230, 0.38);
  --home-brass: #f7c951;
  --home-coral: #e66f52;
  --home-tide: #83d7cb;
  --home-sage: #c8d9a4;
  --home-deep: #061722;
  --home-panel: rgba(7, 26, 36, 0.76);
  position: relative;
  overflow: hidden;
  isolation: isolate;
  background: transparent;
}

.content-shell::before {
  content: none;
}

.content-shell::after {
  content: none;
}

.content-section {
  position: relative;
  z-index: 1;
  max-width: 1180px;
  margin: 0 auto;
  padding: 4rem 1.25rem 5.4rem;
}

.cards-section {
  min-height: auto;
}

.compact-board-heading {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.5rem 1rem;
  align-items: end;
  margin-bottom: 1.35rem;
  text-align: left;
}

.compact-board-heading h2 {
  margin: 0;
  font-family: var(--display-font);
  font-size: clamp(1.9rem, 3vw, 2.55rem);
  font-weight: 900;
  line-height: 1.08;
  text-shadow: 0 0.6rem 2rem rgba(0, 0, 0, 0.3);
}

.compact-board-heading span {
  max-width: 31rem;
  color: var(--home-muted);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.82rem;
  line-height: 1.7;
}

.span-6 {
  grid-column: span 6;
}

.card-kicker {
  margin: 0 0 0.58rem;
  color: var(--card-accent);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.67rem;
  font-weight: 900;
  letter-spacing: 0.13em;
  line-height: 1.25;
  text-transform: uppercase;
  text-shadow: 0 0 0.9rem rgba(var(--card-glow), 0.24);
}

.intro-card {
  --card-glow: 230, 111, 82;
  --card-accent: var(--home-brass);
  min-height: 9rem;
  padding: 1.08rem 1.15rem;
  border-color: rgba(230, 151, 112, 0.3);
  background:
    linear-gradient(145deg, rgba(230, 111, 82, 0.16), transparent 58%),
    linear-gradient(165deg, rgba(247, 201, 81, 0.06), transparent 62%),
    rgba(5, 21, 31, 0.79);
}

.intro-card h3 {
  max-width: 24rem;
  font-size: 1.34rem;
}

.intro-card > p:last-child {
  max-width: 35rem;
}

.time-digits {
  display: inline-flex;
  align-items: baseline;
  color: var(--home-ink);
  font-family: var(--display-font);
  font-size: clamp(1.25rem, 2.4vw, 1.78rem);
  line-height: 1;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  text-shadow:
    0 0 0.7rem rgba(247, 201, 81, 0.16),
    0 0.2rem 0.6rem rgba(0, 0, 0, 0.24);
}

.time-digits span {
  display: inline-block;
  animation: time-digit-float 3.6s ease-in-out infinite;
  animation-delay: calc(var(--digit-index) * 45ms);
}

.tone-tide {
  --card-glow: 131, 215, 203;
  --card-accent: var(--home-tide);
}

.tone-coral {
  --card-glow: 230, 111, 82;
  --card-accent: var(--home-coral);
}

.tone-brass {
  --card-glow: 247, 201, 81;
  --card-accent: var(--home-brass);
}

.tone-sage {
  --card-glow: 200, 217, 164;
  --card-accent: var(--home-sage);
}

.signal-light {
  display: inline-block;
  width: 0.44rem;
  aspect-ratio: 1;
  border-radius: 50%;
  background: var(--home-brass);
  box-shadow: 0 0 0 0.25rem rgba(247, 201, 81, 0.1);
  animation: signal-pulse 2.7s ease-in-out infinite;
}

.home-profile-avatar {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 3rem;
  aspect-ratio: 1;
  box-sizing: border-box;
  overflow: hidden;
  padding: 0.16rem;
  border: 1px solid rgba(247, 201, 81, 0.55);
  border-radius: 50%;
  color: var(--home-brass);
  background:
    linear-gradient(90deg, transparent 49%, rgba(247, 201, 81, 0.26) 49% 51%, transparent 51%),
    linear-gradient(0deg, transparent 49%, rgba(131, 215, 203, 0.2) 49% 51%, transparent 51%),
    rgba(255, 248, 230, 0.06);
  font-family: var(--display-font);
  font-size: 1.2rem;
  line-height: 1;
}

.home-profile-avatar img {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.project-list {
  display: grid;
  gap: 0.5rem;
}

.project-list div {
  display: grid;
  grid-template-columns: 1.6rem minmax(0, 1fr) auto;
  gap: 0.42rem;
  align-items: center;
  padding-bottom: 0.42rem;
  border-bottom: 1px solid rgba(255, 248, 230, 0.1);
  transition:
    transform 140ms var(--card-ease),
    border-color 180ms ease,
    background-color 180ms ease;
}

.project-list div:last-child {
  border-bottom: 0;
}

.project-list span {
  color: var(--home-coral);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.66rem;
  font-weight: 800;
}

.project-list strong {
  overflow: hidden;
  font-family: var(--display-font);
  font-size: 0.9rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-list small {
  overflow: hidden;
  max-width: 5.5rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.site-card {
  --card-glow: 200, 217, 164;
  --card-accent: var(--home-sage);
  gap: 0.55rem;
  background:
    linear-gradient(145deg, rgba(200, 217, 164, 0.12), transparent 58%),
    rgba(5, 21, 31, 0.79);
}

.site-card > strong {
  overflow: hidden;
  color: var(--home-ink);
  font-family: var(--display-font);
  font-size: 1.06rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}


.home-note-list {
  display: grid;
  gap: 0.42rem;
  margin-top: 0.8rem;
}

.home-note-list > a {
  display: grid;
  grid-template-columns: 0.65rem minmax(0, 1fr);
  gap: 0.55rem;
  align-items: center;
  min-height: 2.25rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid rgba(255, 248, 230, 0.1);
  color: var(--home-ink);
  font: 500 0.74rem "Noto Sans SC", sans-serif;
  text-decoration: none;
}

.home-note-list i {
  width: 0.44rem;
  aspect-ratio: 1;
  border-radius: 50%;
  background: var(--home-coral);
  box-shadow: 0 0 0 0.22rem rgba(230, 111, 82, 0.1);
  transition: transform 140ms var(--card-ease), box-shadow 180ms ease;
}

.home-note-list span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compact-empty {
  margin: 0.5rem 0 0;
  color: var(--home-muted);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.76rem;
  line-height: 1.5;
}

@media (hover: hover) and (pointer: fine) {

  .project-list div:hover {
    border-color: rgba(131, 215, 203, 0.34);
    background-color: rgba(131, 215, 203, 0.07);
    transform: translateY(-0.1rem);
  }

  .home-note-list > a:hover i,
  .home-note-list > a:focus-visible i {
    transform: scale(1.18);
    box-shadow: 0 0 0 0.4rem rgba(230, 111, 82, 0.1);
  }
}

@keyframes time-digit-float {
  0%,
  82%,
  100% {
    opacity: 1;
    transform: translateY(0);
  }
  88% {
    opacity: 0.84;
    transform: translateY(-0.08em);
  }
  94% {
    opacity: 1;
    transform: translateY(0.02em);
  }
}

@media (max-width: 1120px) {

  .span-6 {
    grid-column: span 6;
  }
}

@media (max-width: 760px) {
  .content-section {
    padding: 3.5rem 1rem 4rem;
  }

  .compact-board-heading {
    grid-template-columns: 1fr;
  }

  .compact-board-heading span {
    max-width: none;
  }


  .span-6,
  .intro-card,
  .skills-card,
  .project-card,
  .site-card {
    grid-column: span 2;
  }

  .project-list div {
    grid-template-columns: 1.5rem minmax(0, 1fr);
  }

  .project-list small {
    grid-column: 2;
    max-width: none;
  }
}

@media (max-width: 340px) {


  .span-6 {
    grid-column: span 1;
  }

  .compact-board-heading h2 {
    font-size: 1.65rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .content-shell::after,
  .time-digits span,
  .signal-light {
    animation: none;
  }


  .project-list div {
    transition: none;
  }


  .home-note-list i {
    transition: none;
  }
}

/* 首页内容区采用编辑式信息流，避免多个独立卡片争夺视觉焦点。 */
.home-content-flow {
  --flow-line: rgba(255, 248, 230, 0.16);
  --flow-soft: rgba(255, 248, 230, 0.58);
  display: grid;
  gap: 4.4rem;
}

.home-reveal {
  opacity: 1;
  transform: translate3d(0, 0, 0);
}

.cards-motion-ready .home-reveal:not(.card-visible) {
  opacity: 0;
  transform: translate3d(0, 1.2rem, 0);
}

.cards-motion-ready .home-reveal.card-visible {
  animation: home-flow-reveal 580ms var(--card-ease) var(--reveal-delay, 0ms) backwards;
}

.home-lead-row {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(19rem, 0.65fr);
  min-width: 0;
  border-top: 1px solid var(--flow-line);
  border-bottom: 1px solid var(--flow-line);
}

.home-featured-log {
  position: relative;
  display: flex;
  min-width: 0;
  min-height: 20rem;
  flex-direction: column;
  justify-content: flex-end;
  padding: 2.3rem 2.2rem 2.25rem 0;
  color: var(--home-ink);
  text-decoration: none;
}

.home-featured-log::before {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 100%;
  pointer-events: none;
  background: radial-gradient(ellipse at 16% 54%, rgba(230, 111, 82, 0.14), transparent 58%);
  opacity: 0.78;
  transform: translateX(-2%);
  transition: transform 520ms var(--card-ease), opacity 260ms ease;
}

.home-featured-log > * {
  position: relative;
  z-index: 1;
}

.home-featured-log h3 {
  max-width: 40rem;
  margin: 0.75rem 0 0;
  font-family: var(--display-font);
  font-size: clamp(2.5rem, 5vw, 4.75rem);
  font-weight: 900;
  line-height: 1.05;
}

.home-featured-log p {
  max-width: 38rem;
  margin: 1rem 0 0;
  color: var(--home-muted);
  font-size: 0.86rem;
  line-height: 1.8;
}

.home-featured-meta {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-top: 1.55rem;
  color: var(--home-soft);
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.66rem;
}

.home-featured-meta i {
  width: 2rem;
  height: 1px;
  background: var(--home-coral);
}

.home-voyage-status {
  display: grid;
  align-content: end;
  gap: 0.75rem;
  min-width: 0;
  padding: 2rem 0 2.25rem 2rem;
  border-left: 1px solid var(--flow-line);
}

.home-status-heading {
  display: flex;
  gap: 0.55rem;
  align-items: center;
}

.home-writing-status {
  overflow: hidden;
  color: var(--home-ink);
  font-family: var(--display-font);
  font-size: 1.3rem;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-clock-line {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem 0.8rem;
  align-items: baseline;
}

.home-clock-line > span {
  color: var(--home-muted);
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.64rem;
}

.home-panel-heading time,
.home-article-row time,
.home-visitor-line > span {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.home-status-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.65rem;
  padding-top: 0.85rem;
  border-top: 1px solid var(--flow-line);
}

.home-status-grid span,
.home-visitor-line {
  min-width: 0;
  color: var(--home-soft);
  font-size: 0.63rem;
  line-height: 1.55;
}

.home-status-grid b {
  display: block;
  overflow: hidden;
  margin-bottom: 0.15rem;
  color: var(--home-sage);
  font-family: var(--display-font);
  font-size: 1rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-visitor-line {
  display: grid;
  gap: 0.15rem;
  padding-top: 0.85rem;
  border-top: 1px solid var(--flow-line);
}

.home-visitor-line span {
  overflow: hidden;
  color: var(--home-tide);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-visitor-line small {
  overflow: hidden;
  color: var(--home-soft);
  font-size: 0.6rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-reading-layout,
.home-discovery-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(18rem, 0.55fr);
  gap: 3.5rem;
  min-width: 0;
}

.home-discovery-layout {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 2.5rem;
}

.home-section-heading {
  display: flex;
  gap: 1rem;
  align-items: baseline;
  justify-content: space-between;
  min-width: 0;
  padding-bottom: 0.9rem;
  border-bottom: 1px solid var(--flow-line);
}

.home-section-heading > div {
  min-width: 0;
}

.home-section-heading h3 {
  margin: 0.35rem 0 0;
  font-family: var(--display-font);
  font-size: 1.7rem;
  line-height: 1.2;
}

.home-section-heading > a {
  flex: 0 0 auto;
  color: var(--home-muted);
  font-size: 0.67rem;
  text-decoration: none;
  transition: color 180ms ease, transform 180ms var(--card-ease);
}

.home-article-row {
  position: relative;
  display: grid;
  grid-template-columns: 2.2rem 6.5rem minmax(0, 1fr) auto;
  gap: 0.85rem;
  align-items: center;
  min-width: 0;
  min-height: 5.6rem;
  padding: 0.85rem 0;
  border-bottom: 1px solid var(--flow-line);
  color: var(--home-ink);
  text-decoration: none;
  transition: transform 200ms var(--card-ease), color 180ms ease, background-color 180ms ease;
}

.home-article-row::before {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  left: -0.75rem;
  width: 2px;
  background: var(--home-brass);
  opacity: 0;
  transform: scaleY(0.35);
  transition: opacity 180ms ease, transform 220ms var(--card-ease);
}

.home-article-index,
.home-article-row time,
.home-article-likes {
  color: var(--home-soft);
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.61rem;
}

.home-article-index { color: var(--home-coral); }

.home-article-row > div {
  display: grid;
  gap: 0.3rem;
  min-width: 0;
}

.home-article-row strong,
.home-article-row small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-article-row strong {
  font-family: var(--display-font);
  font-size: 1.06rem;
}

.home-article-row small { color: var(--home-muted); font-size: 0.66rem; }

.home-index-panel {
  min-width: 0;
  padding-left: 2rem;
  border-left: 1px solid var(--flow-line);
}

.home-category-lines {
  display: grid;
  margin-top: 0.45rem;
}

.home-category-lines a {
  display: flex;
  gap: 1rem;
  justify-content: space-between;
  min-width: 0;
  padding: 0.7rem 0;
  border-bottom: 1px solid rgba(255, 248, 230, 0.1);
  color: var(--home-muted);
  font-size: 0.75rem;
  text-decoration: none;
  transition: color 180ms ease, transform 180ms var(--card-ease);
}

.home-category-lines a span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.home-category-lines b { color: var(--home-brass); font-family: "IBM Plex Mono", monospace; font-size: 0.65rem; }

.home-tag-line {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem 0.7rem;
  margin-top: 1.25rem;
}

.home-tag-line a {
  color: var(--home-tide);
  font-size: 0.68rem;
  text-decoration: none;
  transition: color 180ms ease, transform 180ms var(--card-ease);
}

.home-signal-panel {
  min-width: 0;
  padding-top: 1rem;
  border-top: 2px solid var(--home-tide);
}

.home-signal-panel:last-child { border-color: var(--home-coral); }

.home-signal-list {
  display: grid;
  margin-top: 0.4rem;
}

.home-signal-list > a {
  display: grid;
  grid-template-columns: 2.1rem minmax(0, 0.8fr) minmax(0, 1.2fr);
  gap: 0.7rem;
  align-items: center;
  min-width: 0;
  min-height: 3.6rem;
  padding: 0.65rem 0;
  border-bottom: 1px solid var(--flow-line);
  color: var(--home-ink);
  text-decoration: none;
  transition: color 180ms ease, transform 180ms var(--card-ease), background-color 180ms ease;
}

.home-signal-list > a > span:first-child {
  color: var(--home-brass);
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.7rem;
}

.home-signal-list strong,
.home-signal-list small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-signal-list strong { font-family: var(--display-font); font-size: 0.92rem; }
.home-signal-list small { color: var(--home-muted); font-size: 0.65rem; }
.home-signal-list .signal-light { display: block; width: 0.46rem; }

.home-profile-strip {
  display: grid;
  grid-template-columns: auto minmax(0, 1.35fr) minmax(0, 0.9fr) auto;
  gap: 1rem;
  align-items: center;
  min-width: 0;
  padding: 1.25rem 0;
  border-top: 1px solid var(--flow-line);
  border-bottom: 1px solid var(--flow-line);
  color: var(--home-ink);
  text-decoration: none;
  transition: transform 200ms var(--card-ease), border-color 200ms ease;
}

.home-profile-copy,
.home-profile-facts {
  display: grid;
  gap: 0.25rem;
  min-width: 0;
}

.home-profile-copy strong,
.home-profile-copy small,
.home-profile-facts b,
.home-profile-facts small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-profile-copy strong { font-family: var(--display-font); font-size: 1.05rem; }
.home-profile-copy small,
.home-profile-facts small { color: var(--home-muted); font-size: 0.66rem; }
.home-profile-facts b { color: var(--home-sage); font-size: 0.74rem; }
.home-profile-action { color: var(--home-brass); font-size: 0.68rem; white-space: nowrap; transition: transform 180ms var(--card-ease); }

@media (hover: hover) and (pointer: fine) {
  .home-featured-log:hover::before,
  .home-featured-log:focus-visible::before { opacity: 1; transform: translateX(0); }
  .home-section-heading > a:hover,
  .home-section-heading > a:focus-visible { color: var(--home-brass); transform: translateX(0.15rem); }
  .home-article-row:hover,
  .home-article-row:focus-visible { background: rgba(255, 248, 230, 0.035); transform: translateX(0.35rem); }
  .home-article-row:hover::before,
  .home-article-row:focus-visible::before { opacity: 1; transform: scaleY(1); }
  .home-category-lines a:hover,
  .home-category-lines a:focus-visible { color: var(--home-ink); transform: translateX(0.3rem); }
  .home-tag-line a:hover,
  .home-tag-line a:focus-visible { color: var(--home-brass); transform: translateY(-0.1rem); }
  .home-signal-list > a:hover,
  .home-signal-list > a:focus-visible { background: rgba(255, 248, 230, 0.035); transform: translateX(0.3rem); }
  .home-profile-strip:hover .home-profile-action,
  .home-profile-strip:focus-visible .home-profile-action { transform: translateX(0.2rem); }
  .home-profile-strip:hover,
  .home-profile-strip:focus-visible { border-color: rgba(247, 201, 81, 0.42); }
}

@keyframes home-flow-reveal {
  from { opacity: 0; transform: translate3d(0, 1.2rem, 0); }
  70% { opacity: 1; transform: translate3d(0, -0.12rem, 0); }
  to { opacity: 1; transform: translate3d(0, 0, 0); }
}

@media (max-width: 900px) {
  .home-lead-row { grid-template-columns: minmax(0, 1fr); }
  .home-voyage-status { padding: 1.5rem 0 1.7rem; border-top: 1px solid var(--flow-line); border-left: 0; }
  .home-reading-layout { grid-template-columns: minmax(0, 1fr); gap: 2.8rem; }
  .home-index-panel { padding-left: 0; border-top: 1px solid var(--flow-line); border-left: 0; padding-top: 1.5rem; }
}

@media (max-width: 620px) {
  .home-content-flow { gap: 3rem; }
  .home-featured-log { min-height: 17rem; padding: 1.7rem 0; }
  .home-featured-log h3 { font-size: clamp(2.15rem, 12vw, 3.3rem); }
  .home-status-grid { gap: 0.4rem; }
  .home-article-row { grid-template-columns: 1.8rem minmax(0, 1fr) auto; gap: 0.55rem; }
  .home-article-row time { grid-column: 2; grid-row: 2; }
  .home-article-row > div { grid-column: 2; grid-row: 1; }
  .home-article-likes { grid-column: 3; grid-row: 1 / span 2; }
  .home-signal-panel { padding-top: 0.8rem; }
  .home-signal-list > a { grid-template-columns: 1.4rem minmax(0, 1fr); }
  .home-signal-list > a small { grid-column: 2; }
  .home-profile-strip { grid-template-columns: auto minmax(0, 1fr) auto; }
  .home-profile-facts { display: none; }
  .home-profile-strip > i { font-size: 0.62rem; }
}

@media (prefers-reduced-motion: reduce) {
  .cards-motion-ready .home-reveal,
  .home-featured-log::before,
  .home-section-heading > a,
  .home-article-row,
  .home-article-row::before,
  .home-category-lines a,
  .home-tag-line a,
  .home-signal-list > a,
  .home-profile-strip,
  .home-profile-action {
    animation: none;
    transition: none;
  }
}

/* 2026 首页内容区：紧凑的航海日志工作台。 */
.content-section {
  max-width: 1220px;
  padding: 3rem 1.5rem 5rem;
}

.compact-board-heading {
  display: flex;
  gap: 1rem;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding: 0 0.15rem;
}

.compact-board-heading h2 {
  font-size: 1.55rem;
  line-height: 1.2;
}

.compact-board-heading span {
  color: rgba(255, 248, 230, 0.62);
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.68rem;
}

.home-content-flow {
  --flow-line: rgba(213, 240, 235, 0.16);
  --flow-line-active: rgba(131, 215, 203, 0.52);
  --flow-glass: rgba(5, 20, 29, 0.68);
  --flow-glass-strong: rgba(5, 20, 29, 0.82);
  display: grid;
  gap: 1rem;
  overflow: clip;
}

.home-featured-log,
.home-voyage-status,
.home-reading-feed,
.home-index-panel,
.home-signal-panel,
.home-profile-strip {
  border: 1px solid var(--flow-line);
  border-radius: 6px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.055), transparent 38%),
    var(--flow-glass);
  box-shadow:
    0 1.25rem 3.5rem rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.045);
  backdrop-filter: blur(15px) saturate(112%);
}

.home-reveal {
  --reveal-x: 0;
  --reveal-y: 1.15rem;
  --reveal-scale: 0.985;
}

.home-voyage-status.home-reveal,
.home-index-panel.home-reveal,
.home-profile-strip.home-reveal {
  --reveal-x: 1rem;
  --reveal-y: 0;
}

.cards-motion-ready .home-reveal:not(.card-visible) {
  opacity: 0;
  transform: translate3d(var(--reveal-x), var(--reveal-y), 0) scale(var(--reveal-scale));
}

.cards-motion-ready .home-reveal.card-visible {
  animation: home-console-reveal 620ms var(--card-ease) var(--reveal-delay, 0ms) backwards;
}

.home-lead-row {
  grid-template-columns: minmax(0, 1.45fr) minmax(19rem, 0.72fr);
  gap: 1rem;
  border: 0;
}

.home-featured-log {
  min-height: 19rem;
  overflow: hidden;
  justify-content: flex-end;
  padding: 2rem;
}

.home-featured-log::before {
  right: -8%;
  bottom: -42%;
  left: 26%;
  width: auto;
  height: 20rem;
  background: radial-gradient(circle, rgba(230, 111, 82, 0.18), transparent 66%);
  opacity: 0.68;
  transform: translate3d(0, 0.7rem, 0);
}

.home-panel-heading,
.home-status-heading {
  display: flex;
  gap: 0.6rem;
  align-items: center;
}

.home-panel-heading {
  justify-content: space-between;
  margin-bottom: auto;
  padding-bottom: 1.4rem;
  border-bottom: 1px solid rgba(213, 240, 235, 0.12);
}

.home-panel-heading strong,
.home-panel-heading time,
.home-profile-name {
  color: var(--home-brass);
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.65rem;
  font-weight: 700;
}

.home-panel-heading time {
  color: var(--home-muted);
  font-weight: 500;
}

.home-featured-log h3 {
  max-width: 42rem;
  margin: 1.7rem 0 0;
  font-size: clamp(2rem, 4.2vw, 3.8rem);
  line-height: 1.08;
}

.home-featured-log p {
  display: -webkit-box;
  overflow: hidden;
  max-width: 42rem;
  margin-top: 0.8rem;
  color: rgba(255, 248, 230, 0.7);
  line-height: 1.65;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.home-featured-meta {
  margin-top: 1.1rem;
}

.home-voyage-status {
  align-content: start;
  gap: 0.75rem;
  padding: 1.35rem;
  border-left: 1px solid var(--flow-line);
}

.home-status-heading {
  justify-content: space-between;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(213, 240, 235, 0.12);
}

.home-status-heading h3,
.home-section-heading h3 {
  margin: 0;
  font-family: var(--display-font);
  font-size: 1rem;
  line-height: 1.3;
}

.home-writing-status {
  margin-top: 0.2rem;
  font-size: 1.15rem;
}

.home-clock-line {
  gap: 0.45rem 0.7rem;
}

.home-clock-line .time-digits {
  font-size: clamp(1.55rem, 3vw, 2.15rem);
}

.home-status-grid {
  gap: 0;
  padding-top: 0.75rem;
}

.home-status-grid span {
  padding: 0 0.55rem;
  border-left: 1px solid rgba(213, 240, 235, 0.12);
}

.home-status-grid span:first-child {
  padding-left: 0;
  border-left: 0;
}

.home-status-grid b {
  font-size: 0.94rem;
}

.home-visitor-line {
  margin-top: auto;
  padding-top: 0.75rem;
}

.home-reading-layout {
  grid-template-columns: minmax(0, 1.55fr) minmax(17rem, 0.62fr);
  gap: 1rem;
}

.home-reading-feed,
.home-index-panel,
.home-signal-panel {
  min-width: 0;
  padding: 1.25rem;
}

.home-index-panel {
  border-left: 1px solid var(--flow-line);
}

.home-section-heading {
  min-height: 2.15rem;
  padding-bottom: 0.75rem;
}

.home-section-heading > a {
  color: rgba(255, 248, 230, 0.62);
}

.home-article-row {
  grid-template-columns: 2rem 4.6rem minmax(0, 1fr) auto;
  min-height: 4.65rem;
  padding: 0.62rem 0;
}

.home-article-row strong {
  font-size: 0.96rem;
}

.home-category-lines a {
  padding: 0.55rem 0;
}

.home-tag-line {
  gap: 0.4rem;
  margin-top: 0.9rem;
}

.home-tag-line a {
  padding: 0.25rem 0.42rem;
  border: 1px solid rgba(131, 215, 203, 0.18);
  border-radius: 4px;
  background: rgba(131, 215, 203, 0.055);
}

.home-lower-deck {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(17rem, 0.72fr);
  gap: 1rem;
  min-width: 0;
}

.home-discovery-layout {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.home-signal-panel {
  border-top: 1px solid var(--flow-line);
}

.home-signal-panel:last-child {
  border-color: var(--flow-line);
}

.home-signal-list > a {
  grid-template-columns: 1.6rem minmax(0, 0.8fr) minmax(0, 1.2fr);
  min-height: 3.35rem;
  padding: 0.5rem 0;
}

.home-profile-strip {
  position: relative;
  grid-template-columns: auto minmax(0, 1fr);
  grid-template-rows: auto auto auto;
  align-content: center;
  padding: 1.25rem;
  border-top: 1px solid var(--flow-line);
  border-bottom: 1px solid var(--flow-line);
}

.home-profile-strip .home-profile-avatar {
  grid-row: 1 / span 2;
}

.home-profile-copy {
  gap: 0.3rem;
}

.home-profile-copy small {
  display: -webkit-box;
  overflow: hidden;
  white-space: normal;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.home-profile-facts {
  grid-column: 1 / -1;
  padding-top: 0.85rem;
  border-top: 1px solid rgba(213, 240, 235, 0.12);
}

.home-profile-action {
  position: absolute;
  right: 1.25rem;
  bottom: 1.25rem;
}

@media (hover: hover) and (pointer: fine) {
  .home-featured-log,
  .home-voyage-status,
  .home-reading-feed,
  .home-index-panel,
  .home-signal-panel,
  .home-profile-strip {
    transition:
      transform 280ms var(--card-ease),
      border-color 240ms ease,
      box-shadow 280ms ease,
      background-color 240ms ease;
  }

  .home-featured-log:hover,
  .home-featured-log:focus-visible,
  .home-voyage-status:hover,
  .home-reading-feed:hover,
  .home-index-panel:hover,
  .home-signal-panel:hover,
  .home-profile-strip:hover,
  .home-profile-strip:focus-visible {
    border-color: var(--flow-line-active);
    box-shadow:
      0 1.65rem 4rem rgba(0, 0, 0, 0.27),
      0 0 1.5rem rgba(131, 215, 203, 0.07),
      inset 0 1px 0 rgba(255, 255, 255, 0.07);
    transform: translateY(-0.22rem);
  }

  .home-featured-log:hover::before,
  .home-featured-log:focus-visible::before {
    opacity: 0.95;
    transform: translate3d(0, 0, 0);
  }

  .home-tag-line a:hover,
  .home-tag-line a:focus-visible {
    border-color: rgba(247, 201, 81, 0.5);
    background: rgba(247, 201, 81, 0.09);
  }
}

@keyframes home-console-reveal {
  from {
    opacity: 0;
    transform: translate3d(var(--reveal-x), var(--reveal-y), 0) scale(var(--reveal-scale));
    filter: blur(5px);
  }
  72% {
    opacity: 1;
    filter: blur(0);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0) scale(1);
    filter: blur(0);
  }
}

@media (max-width: 960px) {
  .home-lead-row,
  .home-reading-layout,
  .home-lower-deck {
    grid-template-columns: minmax(0, 1fr);
  }

  .home-profile-strip {
    grid-template-columns: auto minmax(0, 1.2fr) minmax(13rem, 0.8fr) auto;
    grid-template-rows: auto;
  }

  .home-profile-strip .home-profile-avatar {
    grid-row: auto;
  }

  .home-profile-facts {
    grid-column: auto;
    padding-top: 0;
    border-top: 0;
  }

  .home-profile-action {
    position: static;
  }
}

@media (max-width: 680px) {
  .content-section {
    padding: 2.2rem 0.8rem 3.6rem;
  }

  .compact-board-heading {
    align-items: flex-end;
  }

  .compact-board-heading h2 {
    font-size: 1.35rem;
  }

  .home-content-flow {
    gap: 0.7rem;
  }

  .home-lead-row,
  .home-reading-layout,
  .home-lower-deck,
  .home-discovery-layout {
    gap: 0.7rem;
  }

  .home-featured-log {
    min-height: 15.5rem;
    padding: 1.15rem;
  }

  .home-featured-log::before {
    display: none;
  }

  .home-featured-log {
    overflow: clip;
  }

  .home-featured-log::after {
    display: none;
  }

  .home-featured-log h3 {
    margin-top: 1.15rem;
    font-size: 2rem;
  }

  .home-voyage-status,
  .home-reading-feed,
  .home-index-panel,
  .home-signal-panel,
  .home-profile-strip {
    padding: 1rem;
  }

  .home-article-row {
    grid-template-columns: 1.5rem minmax(0, 1fr) auto;
  }

  .home-article-row time {
    grid-column: 2;
  }

  .home-discovery-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .home-profile-strip {
    grid-template-columns: auto minmax(0, 1fr) auto;
  }

  .home-profile-facts {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .cards-motion-ready .home-reveal,
  .home-featured-log,
  .home-voyage-status,
  .home-reading-feed,
  .home-index-panel,
  .home-signal-panel,
  .home-profile-strip {
    animation: none;
    transition: none;
    filter: none;
  }
}
</style>

<style scoped>
/* 重新组织首屏之后的内容，不改变 hero 区域。 */
.home-next-stops {
  display: grid;
  grid-template-columns: minmax(10rem, .8fr) repeat(auto-fit, minmax(9.5rem, 1fr));
  gap: 0;
  overflow: hidden;
  border: 1px solid var(--flow-line);
  border-radius: 8px;
  background: var(--flow-glass);
  box-shadow: 0 1.25rem 3.5rem rgba(0,0,0,.2), inset 0 1px 0 rgba(255,255,255,.045);
  backdrop-filter: blur(15px) saturate(112%);
}
.home-next-stops-heading {
  display: grid;
  align-content: center;
  gap: .25rem;
  min-height: 5.4rem;
  padding: .9rem 1rem;
  border-right: 1px solid var(--flow-line);
}
.home-next-stops-heading .panel-kicker { margin: 0; color: var(--home-tide); font-size: .63rem; }
.home-next-stops-heading h3 { margin: 0; color: var(--home-ink); font-family: var(--display-font); font-size: 1.05rem; }
.home-next-stops-heading small { color: var(--home-soft); font-size: .62rem; }
.home-next-stops > a {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: .65rem;
  align-items: center;
  min-height: 5.4rem;
  padding: .7rem .8rem;
  border-right: 1px solid var(--flow-line);
  color: var(--home-ink);
  text-decoration: none;
  transition: background-color 180ms ease, transform 180ms var(--card-ease);
}
.home-next-stops > a:last-child { border-right: 0; }
.home-next-stops > a > span { display: grid; gap: .2rem; min-width: 0; }
.home-next-stops strong { font-size: .84rem; }
.home-next-stops small { color: var(--home-muted); font-size: .62rem; line-height: 1.45; }
.home-next-stops .home-route-icon { width: 1.6rem; flex: 0 0 auto; }
.home-next-stops .tone-brass .home-route-icon { color: var(--home-brass); }
.home-next-stops .tone-tide .home-route-icon { color: var(--home-tide); }
.home-next-stops .tone-sage .home-route-icon { color: var(--home-sage); }
.home-next-stops .tone-coral .home-route-icon { color: var(--home-coral); }
.home-section-heading > div { display: grid; gap: .25rem; }
.home-section-heading .panel-kicker { margin: 0; color: var(--home-tide); font-size: .6rem; }
.home-lower-deck { grid-template-columns: minmax(0, 1fr); }
.home-discovery-layout { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.home-guestbook-panel { border-color: rgba(230,111,82,.28); }
.home-guestbook-panel > p { max-width: 22rem; margin: .95rem 0 1.15rem; color: var(--home-muted); font-size: .8rem; line-height: 1.7; }
.home-guestbook-action { display: inline-flex; gap: .4rem; align-items: center; color: var(--home-brass); font-size: .76rem; font-weight: 800; text-decoration: none; }
.home-guestbook-action:hover, .home-guestbook-action:focus-visible { color: var(--home-coral); }
@media (hover: hover) and (pointer: fine) {
  .home-next-stops > a:hover, .home-next-stops > a:focus-visible { background: rgba(131,215,203,.08); transform: translateY(-.12rem); }
}
@media (max-width: 960px) { .home-discovery-layout { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 680px) {
  .home-next-stops { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .home-next-stops-heading { grid-column: 1 / -1; min-height: 3.7rem; border-right: 0; border-bottom: 1px solid var(--flow-line); }
  .home-next-stops > a { min-height: 4.35rem; border-bottom: 1px solid var(--flow-line); }
  .home-next-stops > a:nth-last-child(-n + 2) { border-bottom: 0; }
  .home-next-stops > a:nth-child(odd) { border-right: 0; }
  .home-discovery-layout { grid-template-columns: minmax(0, 1fr); }
}
@media (max-width: 440px) {
  .home-next-stops { grid-template-columns: minmax(0, 1fr); }
  .home-next-stops > a, .home-next-stops > a:nth-child(odd) { border-right: 0; border-bottom: 1px solid var(--flow-line); }
  .home-next-stops > a:last-child { border-bottom: 0; }
}
@media (prefers-reduced-motion: reduce) { .home-next-stops > a, .home-guestbook-action { transition: none; } }
</style>
