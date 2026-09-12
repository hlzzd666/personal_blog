<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { CalendarDays, RefreshCw, Maximize, Minimize, X, ArrowUpRight, LoaderCircle, Search } from "lucide-vue-next";
import DashboardChart, { type ChartSelection } from "../components/DashboardChart.vue";
import DashboardMerry from "../components/DashboardMerry.vue";
import { lengthIndex, summarizeArticles, type DashboardArticle } from "../dashboard/data";
import { dashboardChartOptions } from "../dashboard/charts";
import { fetchDailyVisitorStats, fetchDashboardArticles, type DailyVisitorStats } from "../api/dashboard";
import { fetchSiteSettings } from "../api/site-settings";
import "../dashboard/dashboard.css";

const router = useRouter();
const base = import.meta.env.BASE_URL;
const root = ref<HTMLElement>();
const designWidth = 1672;
const designHeight = 941;
const screenScale = ref(Math.min(window.innerWidth / designWidth, window.innerHeight / designHeight));
let viewportObserver: ResizeObserver | undefined;
const year = ref(2026);
const loading = ref(false);
const error = ref("");
const fullscreen = ref(false);
const articles = ref<DashboardArticle[]>([]);
const seriesNames = ref<string[]>([]);
const visitorStats = ref<DailyVisitorStats | null>(null);
const visitorError = ref(false);
const refreshedAt = ref("");
const reducedMotion = ref(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
let loadId = 0;
const today = computed(() => new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Shanghai", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date()));
const years = ref<number[]>([]);
const summary = computed(() => summarizeArticles(articles.value, year.value, today.value, seriesNames.value));
const options = computed(() => dashboardChartOptions(summary.value, year.value, reducedMotion.value, visitorStats.value));
const visitorEmpty = computed(() => !visitorStats.value || visitorStats.value.days.every((item) => item.visits === 0));
const number = (value: number) => value.toLocaleString("en-US");
const metrics = computed(() => [
  { label: "文章总数", value: number(summary.value.items.length), sub: `截至 ${Number(summary.value.cutoff.slice(5, 7))} 月 ${Number(summary.value.cutoff.slice(8, 10))} 日` },
  { label: "本年发布", value: number(summary.value.annual.length), sub: `${Number(summary.value.cutoff.slice(5, 7))} 月已发布 ${summary.value.months[summary.value.months.length - 1]?.value ?? 0} 篇` },
  { label: "专题航线", value: String(summary.value.seriesCount), sub: `已收录 ${summary.value.seriesArticleCount} 篇文章` },
  { label: "累计字数", value: summary.value.words >= 10000 ? `${(summary.value.words / 10000).toFixed(1)}万` : number(summary.value.words), sub: "文章正文统计" },
  { label: "文章阅读", value: number(summary.value.totalViews), sub: `篇均阅读 ${summary.value.averageViews}` },
  { label: "文章获赞", value: number(summary.value.totalLikes), sub: `篇均获赞 ${summary.value.averageLikes}` },
]);

const dialog = ref<HTMLDialogElement>();
const detailTitle = ref("");
const detailArticles = ref<DashboardArticle[]>([]);
const detailSearch = ref("");
const visibleDetails = computed(() => detailArticles.value.filter((item) => item.title.toLowerCase().includes(detailSearch.value.toLowerCase())));
let restoreFocus: HTMLElement | null = null;
function showDetails(title: string, items: DashboardArticle[]) {
  detailTitle.value = title; detailArticles.value = [...items].sort((a, b) => b.published.localeCompare(a.published)); detailSearch.value = "";
  restoreFocus = document.activeElement as HTMLElement | null;
  dialog.value?.showModal();
}
function closeDetails() { dialog.value?.close(); restoreFocus?.focus(); }
function focusPrevious() { restoreFocus?.focus(); }
function selectChart(kind: string, selection: ChartSelection) {
  const source = summary.value.items;
  if (kind === "monthly") return showDetails(`${year.value} 年 ${selection.name}发布`, summary.value.annual.filter((item) => Number(item.published.slice(5, 7)) === Number.parseInt(selection.name)));
  if (kind === "categories") return showDetails(selection.name, source.filter((item) => item.category === selection.name));
  if (kind === "series") return showDetails(selection.name, source.filter((item) => item.series === selection.name));
  if (kind === "tags") return showDetails(selection.name, source.filter((item) => item.tags.includes(selection.name)));
  if (kind === "lengths") return showDetails(selection.name, source.filter((item) => lengthIndex(item.words) === summary.value.lengths.findIndex((length) => length.name === selection.name)));
  if (kind === "calendar" && Array.isArray(selection.value)) {
    const date = String(selection.value[0]);
    return showDetails(`${date} 发布`, source.filter((item) => item.published === date));
  }
}
function openArticle(item: DashboardArticle) {
  closeDetails();
  void router.push(`/articles/${encodeURIComponent(item.slug)}`);
}

async function refresh() {
  const current = ++loadId;
  error.value = ""; visitorError.value = false; loading.value = true;
  try {
    const settings = await fetchSiteSettings();
    if (current !== loadId) return;
    if (!years.value.length || !settings.dashboard_years.includes(year.value)) {
      year.value = settings.dashboard_years[settings.dashboard_years.length - 1]!;
    }
    years.value = settings.dashboard_years;
    let visitorRequestFailed = false;
    const [result, visitors] = await Promise.all([
      fetchDashboardArticles(),
      fetchDailyVisitorStats().catch((reason) => {
        console.error("访客统计加载失败", reason);
        visitorRequestFailed = true;
        return null;
      }),
    ]);
    if (current !== loadId) return;
    articles.value = result.items; seriesNames.value = result.seriesNames;
    visitorStats.value = visitors; visitorError.value = visitorRequestFailed;
    refreshedAt.value = new Intl.DateTimeFormat("sv-SE", { timeZone: "Asia/Shanghai", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).format(new Date()).replace(/-/g, ".");
  } catch (reason) {
    if (current !== loadId) return;
    console.error("文章大屏数据加载失败", reason);
    articles.value = []; seriesNames.value = []; visitorStats.value = null;
    error.value = reason instanceof Error ? reason.message : "文章数据加载失败，请重试。";
  } finally { if (current === loadId) loading.value = false; }
}
async function toggleFullscreen() {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await root.value?.requestFullscreen();
  } catch { error.value = "浏览器未允许全屏，请使用浏览器的全屏功能。"; }
}
const updateFullscreen = () => { fullscreen.value = !!document.fullscreenElement; };
const updateMotion = () => { reducedMotion.value = motion.matches; };
onMounted(() => {
  void refresh();
  document.addEventListener("fullscreenchange", updateFullscreen); motion.addEventListener("change", updateMotion);
  viewportObserver = new ResizeObserver(([entry]) => {
    if (!entry) return;
    screenScale.value = Math.min(entry.contentRect.width / designWidth, entry.contentRect.height / designHeight);
  });
  if (root.value) viewportObserver.observe(root.value);
});
onBeforeUnmount(() => { loadId++; viewportObserver?.disconnect(); document.removeEventListener("fullscreenchange", updateFullscreen); motion.removeEventListener("change", updateMotion); });
</script>

<template>
  <div ref="root" class="dashboard-viewport" :style="{ '--dashboard-scale': screenScale, '--dashboard-width': `${designWidth}px`, '--dashboard-height': `${designHeight}px`, '--dashboard-ocean': `url('${base}dashboard/background.webp')` }">
    <main class="article-dashboard" :class="{ 'is-loading': loading }" :aria-busy="loading" :style="{ '--dashboard-merry-ocean': `url('${base}dashboard/merry-reference-sea.webp')` }">
      <header class="dashboard-header">
        <RouterLink class="dashboard-brand" to="/" title="返回博客首页" aria-label="返回博客首页">
          <img :src="`${base}dashboard/compass.png`" width="51" height="54" alt="" />
          <span><h1>文章航行总览</h1><small>写作与知识积累</small></span>
        </RouterLink>
        <div class="dashboard-header-actions">
          <div v-if="years.length <= 4" class="dashboard-years" role="group" aria-label="统计年度">
            <button v-for="value in years" :key="value" :class="{ active: year === value }" :aria-pressed="year === value" @click="year = value">{{ value }}</button>
          </div>
          <select v-else v-model="year" class="dashboard-year-select" aria-label="统计年度"><option v-for="value in years" :key="value" :value="value">{{ value }} 年</option></select>
          <div class="dashboard-date"><CalendarDays :size="20" /><span>{{ year }}.01.01 - {{ summary.cutoff.replace(/-/g, '.') }}</span></div>
          <button class="dashboard-tool" :disabled="loading" title="刷新数据" aria-label="刷新数据" @click="refresh"><RefreshCw :size="25" :class="{ 'dashboard-spin': loading }" /></button>
          <button class="dashboard-tool" :title="fullscreen ? '退出全屏' : '全屏'" :aria-label="fullscreen ? '退出全屏' : '全屏'" @click="toggleFullscreen"><Minimize v-if="fullscreen" :size="26" /><Maximize v-else :size="26" /></button>
        </div>
      </header>

      <section class="dashboard-metrics" aria-label="文章核心指标">
        <div v-for="metric in metrics" :key="metric.label" class="dashboard-metric"><h2>{{ metric.label }}</h2><strong>{{ loading ? '—' : metric.value }}</strong><span>{{ metric.sub }}</span></div>
      </section>

      <div class="dashboard-main">
        <div class="dashboard-left">
          <section class="dashboard-panel monthly-panel">
            <header><button @click="showDetails(`${year} 年发布文章`, summary.annual)"><h2>月度发文</h2></button><small>本年 {{ summary.annual.length }} 篇</small></header>
            <DashboardChart :option="options.monthly!" label="月度文章发布数量柱状图" :empty="!summary.annual.length" @select="selectChart('monthly', $event)" />
            <small v-if="year === Number(today.slice(0, 4))" class="current-month">{{ Number(today.slice(5, 7)) }}月进行中</small>
          </section>
          <section class="dashboard-panel categories-panel"><header><button @click="showDetails('文章分类', summary.items)"><h2>文章分类</h2></button></header><DashboardChart :option="options.categories!" label="文章分类占比环形图" :empty="!summary.items.length" @select="selectChart('categories', $event)" /></section>
        </div>

        <div class="dashboard-center">
          <section class="dashboard-panel merry-panel"><header><h2>梅利号</h2><small>GOING MERRY</small></header><DashboardMerry /></section>
          <section class="dashboard-panel series-panel"><header><button @click="showDetails('专题文章', summary.items.filter(item => item.series))"><h2>专题文章量</h2></button><small>{{ summary.seriesCount }} 个专题 · 已收录 {{ summary.seriesArticleCount }} 篇</small></header><DashboardChart :option="options.series!" label="专题文章数量条形图" :empty="!summary.series.length" @select="selectChart('series', $event)" /></section>
        </div>

        <div class="dashboard-right">
          <section class="dashboard-panel tags-panel"><header><button @click="showDetails('技术标签', summary.items)"><h2>技术标签</h2></button><small>文章可含多个标签</small></header><DashboardChart :option="options.tags!" label="技术标签文章数矩形树图" :empty="!summary.tags.length" @select="selectChart('tags', $event)" /></section>
          <section class="dashboard-panel visitor-panel"><header><h2>访客统计</h2><small>近 7 日 · 今日 {{ visitorStats?.today_visits ?? '—' }} 次</small></header><DashboardChart :option="options.visitors!" label="近七日每日访问次数柱状图" :empty="visitorEmpty" :empty-text="visitorError ? '访客数据加载失败' : '近 7 日暂无访问记录'" /></section>
        </div>
      </div>

      <div class="dashboard-bottom">
        <section class="dashboard-panel lengths-panel"><header><button @click="showDetails('文章篇幅', summary.items)"><h2>文章篇幅</h2></button><small>篇</small></header><DashboardChart :option="options.lengths!" label="文章字数分布条形图" :empty="!summary.items.length" @select="selectChart('lengths', $event)" /></section>
        <section class="dashboard-panel calendar-panel"><header><button @click="showDetails(`${year} 年发布文章`, summary.annual)"><h2>文章发布日历</h2></button><small>{{ year }} 年 · 发布 {{ summary.annual.length }} 篇 · 发布日 {{ summary.dates.length }} 天</small></header><DashboardChart :option="options.calendar!" label="年度文章发布日历热力图" @select="selectChart('calendar', $event)" /><div class="calendar-legend" aria-hidden="true"><span>少</span><i v-for="color in ['#d9e9e8','#b6d6d3','#8ebfbc','#5e9fa2','#297c86']" :key="color" :style="{ backgroundColor: color }"></i><span>多</span></div></section>
        <section class="dashboard-panel recent-panel"><header><h2>最近文章更新</h2></header><div class="recent-articles"><button v-for="article in summary.recent" :key="article.id" @click="openArticle(article)"><span class="article-kind" :class="{ revision: article.updated.slice(0, 10) > article.published }">{{ article.updated.slice(0, 10) > article.published ? '修订' : '新文' }}</span><span class="recent-title">{{ article.title }}</span><time>{{ article.updated.slice(5, 10).replace('-', '.') }}</time></button><span v-if="!summary.recent.length" class="recent-empty">暂无文章更新</span></div></section>
      </div>

      <footer class="dashboard-footer"><span>航行仍在继续，记录每一次抵达。</span><span>统计截至 {{ refreshedAt }} · 本站文章</span></footer>
      <div v-if="loading" class="dashboard-loading" role="status"><LoaderCircle :size="22" class="dashboard-spin" />正在汇总文章</div>
      <div v-if="error" class="dashboard-error" role="alert"><span>{{ error }}</span><button @click="refresh">重试</button><button class="dashboard-tool" title="关闭提示" aria-label="关闭提示" @click="error = ''"><X :size="17" /></button></div>

      <dialog ref="dialog" class="dashboard-dialog" aria-labelledby="dashboard-detail-title" @click="event => { if (event.target === dialog) closeDetails(); }" @close="focusPrevious">
        <header><div><h2 id="dashboard-detail-title">{{ detailTitle }}</h2><small>{{ detailArticles.length }} 篇 · 本站文章</small></div><button class="dashboard-tool" aria-label="关闭文章明细" @click="closeDetails"><X :size="24" /></button></header>
        <label class="detail-search"><Search :size="18" /><input v-model="detailSearch" placeholder="搜索文章标题" aria-label="搜索明细文章" /></label>
        <div class="detail-list"><article v-for="article in visibleDetails" :key="article.id"><div><RouterLink :to="`/articles/${article.slug}`" @click="closeDetails">{{ article.title }}<ArrowUpRight :size="15" /></RouterLink><p>{{ article.category }} · {{ article.published }} · {{ number(article.words) }} 字</p></div><span>{{ number(article.views) }} 阅读<br />{{ number(article.likes) }} 获赞</span></article><p v-if="!visibleDetails.length" class="detail-empty">没有符合条件的文章</p></div>
        <footer><RouterLink to="/articles" @click="closeDetails">浏览本站文章<ArrowUpRight :size="16" /></RouterLink><button @click="closeDetails">关闭</button></footer>
      </dialog>
    </main>
  </div>
</template>
