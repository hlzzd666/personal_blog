<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { fetchSiteSettings, type SiteSettings } from "./api/site-settings";
import { fetchVisitorLocation, type VisitorLocation } from "./api/visitor-location";

const fallbackSettings: SiteSettings = {
  site_subtitle: "自由、梦想、伙伴，这里记录我向前航行的每一步。",
  hero_image_url: "https://images.hdqwalls.com/download/one-piece-anime-artwork-i6-2560x1440.jpg",
  nav_brand: "某某某的个人空间",
  owner_avatar_url: "/owner-avatar.jpg",
  owner_location_name: "未设置站长地址",
  owner_latitude: null,
  owner_longitude: null,
  quotes: [
    {
      author: "路飞",
      text: "我是要成为海贼王的男人。",
    },
    {
      author: "希鲁鲁克",
      text: "人被世人遗忘的时候，才是真正的死亡。",
    },
    {
      author: "罗宾",
      text: "我想活下去。",
    },
  ],
};

const route = useRoute();
const settings = ref<SiteSettings>(fallbackSettings);
const navVisible = ref(true);
const navRevealing = ref(false);
const activeQuoteIndex = ref(0);
const typedCharacters = ref(0);
const scrollProgress = ref(0);
const heroParallax = ref(0);
const visibleSections = ref<Record<string, boolean>>({});
const currentPosition = ref<GeolocationCoordinates | null>(null);
const locationStatus = ref("等待定位授权");
const visitorLocation = ref<VisitorLocation | null>(null);
const visitorLocationStatus = ref("正在查询访客位置");
const featureCards = [
  {
    tag: "CURRENT WATCH",
    title: "最新文章",
    text: "把最近完成的思考放在甲板中央，适合承接文章列表、分类筛选和推荐阅读。",
  },
  {
    tag: "SEA CHART",
    title: "精选专题",
    text: "把长期写作主题整理成清晰航线，让访客更快找到技术、生活或项目系列。",
  },
  {
    tag: "SUPPLY BOX",
    title: "站内导航",
    text: "预留搜索、标签、归档和热门入口，成为向下浏览后的内容补给点。",
  },
];
const logItems = [
  "确定首页视觉与博客主题，让访问者一眼进入航海日志氛围。",
  "文章模块接入后，这里展示最新里程碑和阶段进展。",
  "后续扩展成真实的成长、项目、学习时间线。",
];
const voyageStats = [
  { label: "航线", value: "03", detail: "内容方向" },
  { label: "日志", value: "03", detail: "阶段记录" },
  { label: "状态", value: "ON", detail: "持续航行" },
];

let quoteTimer: number | undefined;
let switchTimer: number | undefined;
let navRevealTimer: number | undefined;
let locationWatchId: number | undefined;
let lastScrollY = 0;
let scrollFrame: number | undefined;
let sectionObserver: IntersectionObserver | undefined;

const activeQuote = computed(() => settings.value.quotes[activeQuoteIndex.value] ?? fallbackSettings.quotes[0]);
const typedQuote = computed(() => activeQuote.value.text.slice(0, typedCharacters.value));
const latitudeText = computed(() => {
  if (!currentPosition.value) {
    return "纬度待定位";
  }

  const latitude = currentPosition.value.latitude;
  return `${latitude >= 0 ? "北纬" : "南纬"} ${Math.abs(latitude).toFixed(1)}`;
});
const longitudeText = computed(() => {
  if (!currentPosition.value) {
    return "经度待定位";
  }

  const longitude = currentPosition.value.longitude;
  return `${longitude >= 0 ? "东经" : "西经"} ${Math.abs(longitude).toFixed(1)}`;
});
const locationMetaText = computed(() => {
  if (!currentPosition.value) {
    return locationStatus.value;
  }

  return "海域定位已同步";
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

  return distance >= 100 ? `约 ${Math.round(distance)} 公里` : `约 ${distance.toFixed(1)} 公里`;
});
const greetingText = computed(() => {
  const hour = new Date().getHours();
  if (hour < 6) return "夜深了，注意休息";
  if (hour < 11) return "早上好，祝你今天顺利";
  if (hour < 14) return "中午好，记得补充能量";
  if (hour < 19) return "下午好，继续向前航行";
  return "晚上好，愿这段阅读陪伴你";
});
const welcomeMessage = computed(() => {
  const location = visitorLocationText.value === "正在查询访客位置" ? "远方" : visitorLocationText.value;
  return `欢迎来自 ${location} 的小伙伴，${greetingText.value}。你距离站长「${settings.value.owner_location_name}」${distanceText.value}。`;
});

async function loadSettings() {
  try {
    settings.value = await fetchSiteSettings();
  } catch {
    settings.value = fallbackSettings;
  }
}

async function loadVisitorLocation() {
  try {
    visitorLocation.value = await fetchVisitorLocation();
    visitorLocationStatus.value = visitorLocation.value.location_available ? "位置已同步" : "位置暂不可用";
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

function handleScroll() {
  const currentY = window.scrollY;
  const scrollingUp = currentY < lastScrollY;
  navVisible.value = currentY < 24 || scrollingUp;

  if (scrollingUp && currentY >= 24) {
    navRevealing.value = true;
    window.clearTimeout(navRevealTimer);
    navRevealTimer = window.setTimeout(() => {
      navRevealing.value = false;
    }, 1200);
  } else if (!scrollingUp) {
    navRevealing.value = false;
    window.clearTimeout(navRevealTimer);
  }

  lastScrollY = currentY;

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

function observeSections() {
  sectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          visibleSections.value[entry.target.id] = true;
          sectionObserver?.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.16 },
  );

  document.querySelectorAll<HTMLElement>("[data-reveal-section]").forEach((section) => {
    sectionObserver?.observe(section);
  });
}

function startLocationWatch() {
  if (!("geolocation" in navigator)) {
    locationStatus.value = "定位不可用";
    return;
  }

  locationWatchId = navigator.geolocation.watchPosition(
    (position) => {
      currentPosition.value = position.coords;
      locationStatus.value = "海域定位已同步";
    },
    (error) => {
      currentPosition.value = null;
      if (error.code === error.PERMISSION_DENIED) {
        locationStatus.value = "定位未授权";
        return;
      }
      if (error.code === error.TIMEOUT) {
        locationStatus.value = "定位超时";
        return;
      }
      locationStatus.value = "定位失败";
    },
    {
      enableHighAccuracy: true,
      maximumAge: 10000,
      timeout: 15000,
    },
  );
}

onMounted(async () => {
  await loadSettings();
  void loadVisitorLocation();
  startTypingCycle();
  startLocationWatch();
  observeSections();
  window.addEventListener("scroll", handleScroll, { passive: true });
  handleScroll();
});

onBeforeUnmount(() => {
  window.removeEventListener("scroll", handleScroll);
  window.clearInterval(quoteTimer);
  window.clearTimeout(switchTimer);
  window.clearTimeout(navRevealTimer);
  if (scrollFrame !== undefined) {
    window.cancelAnimationFrame(scrollFrame);
  }
  sectionObserver?.disconnect();
  if (locationWatchId !== undefined) {
    navigator.geolocation.clearWatch(locationWatchId);
  }
});
</script>

<template>
  <div v-if="route.path === '/'" class="page-shell">
    <div class="voyage-progress" aria-hidden="true">
      <span :style="{ transform: `scaleY(${scrollProgress})` }"></span>
    </div>
    <header :class="['floating-nav', { hidden: !navVisible, revealing: navRevealing }]">
      <a class="brand" href="#hero">{{ settings.nav_brand }}</a>
      <nav aria-label="主导航">
        <a href="#hero">首页</a>
        <div class="article-nav-menu">
          <button type="button" class="article-nav-trigger">
            文章 <i class="iconfont article-nav-icon" aria-hidden="true">&#xe64e;</i>
          </button>
          <div class="article-nav-panel">
            <a href="/articles?view=archive"><i class="nav-item-mark" aria-hidden="true"></i>归档</a>
            <a href="/articles?view=tags"><i class="nav-item-mark" aria-hidden="true"></i>标签</a>
            <a href="/articles?view=categories"><i class="nav-item-mark" aria-hidden="true"></i>分类</a>
          </div>
        </div>
        <a href="#about">关于自己</a>
        <a href="#timeline">航海日志</a>
      </nav>
    </header>

    <section
      id="hero"
      class="hero"
      :style="{ backgroundImage: `linear-gradient(rgba(7, 18, 29, 0.38), rgba(7, 18, 29, 0.72)), url(${settings.hero_image_url})` }"
    >
      <div class="hero-atmosphere" aria-hidden="true"></div>
      <div class="hero-grain" aria-hidden="true"></div>
      <div class="hero-route" aria-hidden="true">
        <span class="route-point"></span>
      </div>
      <div class="hero-compass" aria-hidden="true"></div>
      <div class="hero-ripple hero-ripple-one" aria-hidden="true"></div>
      <div class="hero-ripple hero-ripple-two" aria-hidden="true"></div>
      <div class="hero-overlay">
        <div class="hero-coordinates" aria-live="polite">
          <span>{{ latitudeText }}</span>
          <span>{{ longitudeText }}</span>
          <span>{{ locationMetaText }}</span>
        </div>
        <div class="hero-copy" :style="{ transform: `translate3d(0, ${heroParallax}px, 0)` }">
          <p class="hero-subtitle">{{ settings.site_subtitle }}</p>
          <div class="quote-box">
            <p class="quote-line">
              {{ typedQuote }}<span class="cursor">|</span>
            </p>
            <p class="quote-author">{{ activeQuote.author }}</p>
          </div>
        </div>
        <a
          class="scroll-indicator"
          href="#articles"
          aria-label="继续往下看"
          title="继续往下看"
        >
          <span class="scroll-arrow" aria-hidden="true"></span>
        </a>
      </div>
    </section>

    <main class="content-shell">
      <section
        id="articles"
        :class="['content-section', 'deck-section', 'reveal-section', { visible: visibleSections.articles }]"
        data-reveal-section
      >
        <div class="section-heading">
          <p class="section-tag">CAPTAIN'S DESK</p>
          <h2>从最近靠岸的文字开始读</h2>
          <p>首页像一张会展开的海图，随着向下浏览，逐步显露下一段航行的入口。</p>
        </div>

        <div class="feature-grid">
          <article
            v-for="(card, index) in featureCards"
            :key="card.title"
            :class="['feature-card', { 'feature-card-accent': index === 0 }]"
          >
            <p class="section-tag">{{ card.tag }}</p>
            <h3>{{ card.title }}</h3>
            <p>{{ card.text }}</p>
            <a class="feature-card-link" href="/articles">打开文章归档 <span aria-hidden="true">↗</span></a>
          </article>
        </div>
      </section>

      <section
        id="about"
        :class="['content-section', 'split-section', 'reveal-section', { visible: visibleSections.about }]"
        data-reveal-section
      >
        <div class="about-copy">
          <p class="section-tag">ONBOARD PROFILE</p>
          <h2>一页可读的航行档案</h2>
          <p>
            不展示冗长履历，而是把正在写什么、当前位置与站点状态压缩成几张可以快速读完的信息舱。
          </p>
        </div>
        <div class="identity-deck">
          <article class="profile-card info-card">
            <div class="profile-card-top">
              <div class="profile-seal">
                <img :src="settings.owner_avatar_url" alt="站长头像" />
              </div>
              <div>
                <p class="panel-kicker">PERSONAL LOG</p>
                <h3>{{ settings.nav_brand }}</h3>
              </div>
            </div>
            <p class="profile-summary">开发、写作、长期主义。把每段正在发生的思考留下航迹。</p>
            <div class="profile-stats">
              <div v-for="stat in voyageStats" :key="stat.label">
                <strong>{{ stat.value }}</strong>
                <span>{{ stat.label }}</span>
                <small>{{ stat.detail }}</small>
              </div>
            </div>
          </article>

          <article class="signal-card info-card">
            <div class="card-title-row">
              <span class="signal-light" aria-hidden="true"></span>
              <p class="panel-kicker">航线信号</p>
              <span class="signal-code">LIVE</span>
            </div>
            <h3>欢迎靠岸</h3>
            <p class="welcome-message">{{ welcomeMessage }}</p>
            <dl class="signal-data">
              <div>
                <dt>城市</dt>
                <dd>{{ visitorLocationText }}</dd>
              </div>
              <div>
                <dt>IP</dt>
                <dd>{{ visitorIpText }}</dd>
              </div>
              <div>
                <dt>距离</dt>
                <dd>{{ distanceText }}</dd>
              </div>
            </dl>
          </article>

          <article class="vessel-card info-card">
            <div>
              <p class="panel-kicker">船况简报</p>
              <h3>站点正在持续记录</h3>
            </div>
            <div class="vessel-statuses">
              <span><i></i> 日志系统在线</span>
              <span><i></i> 首页航线已展开</span>
              <span><i></i> 下次靠岸：下一篇文章</span>
            </div>
          </article>
        </div>
      </section>

      <section
        id="timeline"
        :class="['content-section', 'timeline-section', 'reveal-section', { visible: visibleSections.timeline }]"
        data-reveal-section
      >
        <div class="section-heading section-heading-compact">
          <p class="section-tag">VOYAGE LOG</p>
          <h2>航海日志</h2>
        </div>
        <div class="timeline">
          <div v-for="(item, index) in logItems" :key="item" class="timeline-item">
            <span>{{ String(index + 1).padStart(2, "0") }}</span>
            <p>{{ item }}</p>
          </div>
        </div>
      </section>
    </main>
  </div>
  <router-view v-else />
</template>

<style scoped>
.page-shell {
  color: #fef9ef;
  background: #07131f;
}

.voyage-progress {
  position: fixed;
  top: 30%;
  right: 1.35rem;
  z-index: 22;
  width: 1px;
  height: 7.5rem;
  overflow: hidden;
  background: rgba(255, 249, 239, 0.2);
  transform: rotate(180deg);
}

.voyage-progress span {
  display: block;
  width: 100%;
  height: 100%;
  background: #ffd36f;
  box-shadow: 0 0 0.8rem rgba(255, 211, 111, 0.65);
  transform-origin: bottom;
  transition: transform 0.15s linear;
}

.floating-nav {
  position: fixed;
  inset: 0 0 auto 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.1rem 2.4rem;
  background: transparent;
  isolation: isolate;
  transition:
    transform 0.75s cubic-bezier(0.22, 0.72, 0.25, 1),
    opacity 0.75s ease;
  will-change: transform, opacity;
}

.floating-nav::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    linear-gradient(180deg, rgba(8, 22, 36, 0.72), rgba(8, 22, 36, 0.34)),
    repeating-linear-gradient(168deg, transparent 0 9px, rgba(255, 255, 255, 0.045) 10px 11px, transparent 12px 20px);
  backdrop-filter: blur(12px);
  opacity: 0;
}

.floating-nav > * {
  position: relative;
  z-index: 1;
}

.floating-nav.revealing::before {
  animation: nav-glass-fade 1.2s ease both;
}

.floating-nav.hidden {
  opacity: 0;
  transform: translateY(-110%);
  pointer-events: none;
}

.brand,
nav a,
.article-nav-trigger {
  color: #fff9ef;
  text-decoration: none;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
}

.brand {
  font-weight: 700;
  font-size: 1rem;
  letter-spacing: 0.04em;
}

nav {
  display: flex;
  align-items: center;
  gap: 1.35rem;
  font-size: 0.95rem;
  font-weight: 700;
}

nav > a,
.article-nav-trigger {
  position: relative;
  padding-bottom: 0.45rem;
}

nav > a::before,
.article-nav-trigger::before {
  content: "";
  position: absolute;
  right: 50%;
  bottom: 0;
  left: 50%;
  height: 2px;
  background: #ffd36f;
  box-shadow: 0 0 0.65rem rgba(255, 211, 111, 0.54);
  transition:
    left 0.28s cubic-bezier(0.2, 0.75, 0.28, 1),
    right 0.28s cubic-bezier(0.2, 0.75, 0.28, 1);
}

nav > a:hover::before,
nav > a:focus-visible::before,
.article-nav-menu:hover .article-nav-trigger::before,
.article-nav-menu:focus-within .article-nav-trigger::before {
  right: 0;
  left: 0;
}

nav > a:hover,
nav > a:focus-visible,
.article-nav-menu:hover .article-nav-trigger,
.article-nav-menu:focus-within .article-nav-trigger {
  color: #ffd36f;
}

.article-nav-menu {
  position: relative;
  cursor: pointer;
}

.article-nav-menu::after {
  content: "";
  position: absolute;
  top: 100%;
  right: -0.75rem;
  left: -0.75rem;
  height: 0.45rem;
}

.article-nav-menu * {
  cursor: pointer;
}

.article-nav-trigger {
  display: inline-flex;
  align-items: center;
  border: 0;
  background: transparent;
  font: inherit;
}

.article-nav-icon {
  display: inline-block;
  margin-left: 0.35rem;
  color: currentColor;
  font-size: 0.72rem;
  line-height: 1;
  transition: transform 0.28s cubic-bezier(0.2, 0.75, 0.28, 1);
}

.article-nav-menu:hover .article-nav-icon,
.article-nav-menu:focus-within .article-nav-icon {
  transform: rotate(180deg);
}

.article-nav-panel {
  position: absolute;
  top: calc(100% + 0.45rem);
  left: 50%;
  display: none;
  grid-template-columns: repeat(3, auto);
  gap: 0.2rem;
  min-width: 14.5rem;
  padding: 0.45rem;
  border: 1px solid rgba(255, 249, 239, 0.14);
  border-radius: 8px;
  background:
    linear-gradient(145deg, rgba(65, 146, 158, 0.24), transparent 60%),
    rgba(8, 28, 43, 0.92);
  box-shadow: 0 1rem 2.5rem rgba(0, 0, 0, 0.28);
  backdrop-filter: blur(14px);
  transform: translateX(-50%);
}

.article-nav-menu:hover .article-nav-panel,
.article-nav-menu:focus-within .article-nav-panel {
  display: grid;
  animation: article-menu-reveal 0.22s ease both;
}

.article-nav-panel a {
  display: inline-flex;
  gap: 0.38rem;
  align-items: center;
  justify-content: center;
  min-height: 2.15rem;
  padding: 0.35rem 0.55rem;
  border-radius: 5px;
  color: rgba(255, 249, 239, 0.82);
  font-size: 0.78rem;
  text-shadow: none;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.article-nav-panel a:hover {
  color: #ffd36f;
  background: rgba(255, 211, 111, 0.12);
}

.nav-item-mark {
  width: 0.4rem;
  height: 0.4rem;
  border: 1px solid #ffd36f;
  border-radius: 50%;
  box-shadow: 0 0 0.45rem rgba(255, 211, 111, 0.36);
}

.hero {
  position: relative;
  overflow: hidden;
  min-height: 100vh;
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
}

.hero-atmosphere {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 50% 48%, rgba(255, 211, 111, 0.16), transparent 18rem),
    linear-gradient(116deg, transparent 20%, rgba(255, 211, 111, 0.1) 46%, transparent 66%),
    repeating-linear-gradient(172deg, transparent 0 16px, rgba(255, 255, 255, 0.026) 17px 18px, transparent 19px 34px),
    repeating-linear-gradient(88deg, transparent 0 58px, rgba(255, 255, 255, 0.03) 59px 60px);
  background-size: 100% 100%, 220% 100%, 100% 100%, 100% 100%;
  mix-blend-mode: screen;
  opacity: 0.65;
  animation: sea-glow 16s ease-in-out infinite alternate;
}

.hero-grain {
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0.16;
  background-image: repeating-radial-gradient(circle at 0 0, rgba(255, 255, 255, 0.45) 0 1px, transparent 1px 3px);
  background-size: 5px 5px;
  mix-blend-mode: soft-light;
  animation: grain-shift 0.28s steps(2) infinite;
}

.hero-route {
  position: absolute;
  top: 28%;
  right: 8%;
  width: min(21rem, 32%);
  height: min(15rem, 24%);
  border-top: 1px solid rgba(255, 211, 111, 0.42);
  border-right: 1px dashed rgba(255, 249, 239, 0.3);
  border-radius: 0 100% 0 0;
  transform: rotate(-18deg);
  opacity: 0.72;
  pointer-events: none;
  animation: route-drift 9s ease-in-out infinite;
}

.hero-route::after {
  content: "";
  position: absolute;
  right: -0.25rem;
  bottom: -0.25rem;
  width: 0.5rem;
  height: 0.5rem;
  border: 1px solid #ffd36f;
  border-radius: 50%;
  box-shadow: 0 0 0 0 rgba(255, 211, 111, 0.5);
  animation: route-pulse 2.8s ease-out infinite;
}

.route-point {
  position: absolute;
  top: -0.2rem;
  left: 18%;
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 50%;
  background: #ffd36f;
  box-shadow: 0 0 16px rgba(255, 211, 111, 0.9);
}

.hero-compass {
  position: absolute;
  left: 8%;
  bottom: 14%;
  width: 10rem;
  height: 10rem;
  border: 1px solid rgba(255, 249, 239, 0.16);
  border-radius: 50%;
  opacity: 0.42;
  pointer-events: none;
  animation: compass-turn 28s linear infinite;
}

.hero-compass::before,
.hero-compass::after {
  content: "";
  position: absolute;
  inset: 1.25rem;
  border: 1px dashed rgba(255, 211, 111, 0.24);
  border-radius: 50%;
}

.hero-compass::after {
  inset: 50% auto auto 50%;
  width: 1px;
  height: 4rem;
  border: 0;
  background: linear-gradient(rgba(255, 211, 111, 0.75), transparent);
  transform-origin: top;
  transform: rotate(42deg);
}

.hero-ripple {
  position: absolute;
  right: 13%;
  bottom: 13%;
  width: 5rem;
  height: 1.15rem;
  border: 1px solid rgba(255, 249, 239, 0.2);
  border-radius: 50%;
  opacity: 0;
  pointer-events: none;
}

.hero-ripple-one {
  animation: wake-ripple 5.4s ease-out 1.2s infinite;
}

.hero-ripple-two {
  animation: wake-ripple 5.4s ease-out 3.9s infinite;
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

.hero-coordinates {
  position: absolute;
  top: 7rem;
  left: 50%;
  display: flex;
  gap: 1rem;
  color: rgba(255, 249, 239, 0.62);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  transform: translateX(-50%);
}

.hero-coordinates span {
  padding-inline: 0.6rem;
  border-inline: 1px solid rgba(255, 211, 111, 0.28);
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
  animation: arrow-bounce 2.8s ease-in-out 1.4s infinite;
}

.content-shell {
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 12% 10%, rgba(255, 211, 111, 0.12), transparent 18rem),
    radial-gradient(circle at 88% 32%, rgba(71, 150, 157, 0.2), transparent 22rem),
    linear-gradient(180deg, #07131f, #0a1c2e 44%, #10283b 100%);
}

.content-shell::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(rgba(255, 255, 255, 0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.025) 1px, transparent 1px);
  background-size: 4rem 4rem;
  mask-image: linear-gradient(180deg, transparent, #000 10rem, #000 80%, transparent);
}

.content-section {
  position: relative;
  max-width: 1180px;
  margin: 0 auto;
  padding: 5.8rem 1.5rem;
}

.reveal-section {
  opacity: 0;
  transform: translateY(2.5rem);
  transition:
    opacity 0.8s ease,
    transform 0.8s cubic-bezier(0.2, 0.76, 0.26, 1);
}

.reveal-section.visible {
  opacity: 1;
  transform: translateY(0);
}

.deck-section {
  display: grid;
  gap: 2rem;
}

.section-heading {
  max-width: 42rem;
}

.section-heading h2,
.split-section h2,
.timeline-section h2 {
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

.section-heading-compact {
  margin-bottom: 1.8rem;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.25rem;
}

.feature-card,
.glass-panel,
.timeline-item {
  border: 1px solid rgba(255, 255, 255, 0.12);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.035)),
    rgba(7, 19, 31, 0.4);
  backdrop-filter: blur(14px);
  border-radius: 18px;
  box-shadow: 0 1.2rem 3.5rem rgba(0, 0, 0, 0.22);
}

.feature-card {
  position: relative;
  min-height: 16rem;
  padding: 2rem;
  overflow: hidden;
  transition:
    transform 0.5s cubic-bezier(0.2, 0.76, 0.26, 1),
    border-color 0.35s ease,
    background-color 0.35s ease;
}

.feature-card:nth-child(2) {
  transition-delay: 0.08s;
}

.feature-card:nth-child(3) {
  transition-delay: 0.16s;
}

.feature-card::after {
  content: "";
  position: absolute;
  right: -2.4rem;
  bottom: -2.4rem;
  width: 8rem;
  height: 8rem;
  border: 1px solid rgba(255, 211, 111, 0.14);
  border-radius: 50%;
}

.feature-card:hover {
  transform: translateY(-0.55rem) rotate(0.3deg);
  border-color: rgba(255, 211, 111, 0.42);
}

.feature-card-accent {
  background:
    linear-gradient(145deg, rgba(198, 82, 49, 0.36), rgba(255, 211, 111, 0.08)),
    rgba(7, 19, 31, 0.46);
}

.section-tag {
  margin: 0 0 0.75rem;
  color: #ffd36f;
  letter-spacing: 0.18em;
  font-size: 0.78rem;
}

.feature-card h3 {
  margin: 0 0 1rem;
  font-family: var(--display-font);
  font-size: 2rem;
  line-height: 1.18;
}

.feature-card p,
.about-copy p,
.timeline-item p,
.glass-panel p,
.keyword-cloud span {
  color: rgba(255, 249, 239, 0.82);
  line-height: 1.8;
}

.feature-card-link {
  position: absolute;
  right: 2rem;
  bottom: 1.7rem;
  color: #ffd36f;
  font-size: 0.78rem;
  text-decoration: none;
}

.feature-card-link span {
  display: inline-block;
  margin-left: 0.35rem;
  transition: transform 0.25s ease;
}

.feature-card-link:hover span {
  transform: translate(0.2rem, -0.2rem);
}

.split-section {
  display: grid;
  grid-template-columns: minmax(220px, 0.7fr) minmax(0, 1.3fr);
  gap: 2rem;
  align-items: center;
}

.about-copy {
  padding-block: 1.2rem;
}

.panel-kicker {
  margin: 0 0 1rem;
  color: #ffd36f;
  font-size: 0.72rem;
  letter-spacing: 0.15em;
}

.identity-deck {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.info-card {
  position: relative;
  min-height: 15.75rem;
  overflow: hidden;
  border: 1px solid rgba(255, 249, 239, 0.14);
  border-radius: 12px;
  box-shadow: 0 1.3rem 3.5rem rgba(0, 0, 0, 0.2);
  transition:
    transform 0.5s cubic-bezier(0.2, 0.76, 0.26, 1),
    border-color 0.4s ease,
    box-shadow 0.4s ease;
}

.info-card:hover {
  transform: translateY(-0.45rem);
  border-color: rgba(255, 211, 111, 0.45);
  box-shadow: 0 1.8rem 4rem rgba(0, 0, 0, 0.3);
}

.profile-card {
  padding: 1.5rem;
  background:
    linear-gradient(135deg, rgba(198, 82, 49, 0.45), transparent 62%),
    linear-gradient(180deg, rgba(255, 211, 111, 0.13), rgba(7, 19, 31, 0.72));
}

.profile-card::after {
  content: "N";
  position: absolute;
  top: -1.3rem;
  right: 0.55rem;
  color: rgba(255, 249, 239, 0.1);
  font-family: var(--display-font);
  font-size: 12rem;
  line-height: 1;
}

.profile-card-top,
.card-title-row,
.profile-stats,
.signal-data,
.vessel-statuses {
  position: relative;
  z-index: 1;
}

.profile-card-top {
  display: flex;
  gap: 0.9rem;
  align-items: center;
}

.profile-card-top h3,
.signal-card h3,
.vessel-card h3 {
  margin: 0;
  font-family: var(--display-font);
  font-size: 1.28rem;
  line-height: 1.25;
}

.profile-seal {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 3.25rem;
  aspect-ratio: 1;
  overflow: hidden;
  border: 1px solid rgba(255, 211, 111, 0.8);
  border-radius: 50%;
  background: rgba(7, 19, 31, 0.45);
  box-shadow: inset 0 0 0 0.32rem rgba(255, 211, 111, 0.08);
}

.profile-seal img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 22%;
}

.profile-summary,
.signal-card > p {
  position: relative;
  z-index: 1;
  margin: 1.3rem 0;
  color: rgba(255, 249, 239, 0.78);
  font-size: 0.9rem;
  line-height: 1.75;
}

.profile-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 249, 239, 0.16);
}

.profile-stats div {
  display: grid;
  gap: 0.12rem;
}

.profile-stats strong {
  color: #fff9ef;
  font-family: var(--display-font);
  font-size: 1.4rem;
}

.profile-stats span {
  color: #ffd36f;
  font-size: 0.7rem;
}

.profile-stats small {
  color: rgba(255, 249, 239, 0.48);
  font-size: 0.63rem;
}

.signal-card {
  min-height: 18rem;
  padding: 1.5rem;
  background:
    linear-gradient(150deg, rgba(65, 146, 158, 0.34), transparent 58%),
    rgba(8, 28, 43, 0.86);
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: 0.55rem;
}

.card-title-row .panel-kicker {
  margin: 0;
}

.signal-light,
.vessel-statuses i {
  display: inline-block;
  width: 0.45rem;
  aspect-ratio: 1;
  border-radius: 50%;
  background: #ffd36f;
  box-shadow: 0 0 0 0.35rem rgba(255, 211, 111, 0.13);
  animation: signal-pulse 2.7s ease-in-out infinite;
}

.signal-code {
  margin-left: auto;
  color: rgba(255, 249, 239, 0.55);
  font-family: var(--display-font);
  font-size: 0.65rem;
  letter-spacing: 0.14em;
}

.signal-card h3 {
  margin-top: 1.25rem;
}

.signal-data {
  display: grid;
  gap: 0.65rem;
  margin: 0;
}

.signal-data div {
  display: grid;
  grid-template-columns: 3.2rem 1fr;
  gap: 0.6rem;
  padding-top: 0.65rem;
  border-top: 1px solid rgba(255, 249, 239, 0.12);
}

.signal-data dt,
.signal-data dd {
  margin: 0;
  font-size: 0.72rem;
}

.signal-data dt {
  color: rgba(255, 249, 239, 0.48);
}

.signal-data dd {
  color: rgba(255, 249, 239, 0.86);
}

.vessel-card {
  display: flex;
  grid-column: 1 / -1;
  justify-content: space-between;
  gap: 2rem;
  min-height: 7.8rem;
  padding: 1.35rem 1.5rem;
  background:
    repeating-linear-gradient(90deg, transparent 0 1.7rem, rgba(255, 249, 239, 0.035) 1.7rem 1.76rem),
    rgba(14, 39, 55, 0.76);
}

.vessel-statuses {
  display: grid;
  align-content: center;
  gap: 0.45rem;
}

.vessel-statuses span {
  display: flex;
  gap: 0.55rem;
  align-items: center;
  color: rgba(255, 249, 239, 0.75);
  font-size: 0.78rem;
}

.vessel-statuses i {
  width: 0.32rem;
  box-shadow: 0 0 0 0.24rem rgba(255, 211, 111, 0.1);
}

.timeline {
  display: grid;
  gap: 1rem;
}

.timeline-item {
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: 1rem;
  align-items: center;
  padding: 1.45rem 1.6rem;
  transition:
    transform 0.4s ease,
    border-color 0.4s ease;
}

.timeline-item:hover {
  transform: translateX(0.45rem);
  border-color: rgba(255, 211, 111, 0.36);
}

.timeline-item span {
  display: inline-grid;
  place-items: center;
  width: 3rem;
  height: 3rem;
  border-radius: 999px;
  background: rgba(255, 211, 111, 0.18);
  color: #ffd36f;
  font-weight: 700;
  animation: marker-glow 3.8s ease-in-out infinite;
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

@keyframes sea-glow {
  from {
    background-position: 0 0, 0% 0%, 0 0, 0 0;
  }
  to {
    background-position: 0 0, 100% 0%, 0 14px, 16px 0;
  }
}

@keyframes grain-shift {
  0% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(2%, -1%, 0);
  }
  100% {
    transform: translate3d(-1%, 2%, 0);
  }
}

@keyframes compass-turn {
  to {
    transform: rotate(360deg);
  }
}

@keyframes route-drift {
  0%,
  100% {
    transform: rotate(-18deg) translate3d(0, 0, 0);
  }
  50% {
    transform: rotate(-15deg) translate3d(-0.7rem, 0.45rem, 0);
  }
}

@keyframes route-pulse {
  70% {
    box-shadow: 0 0 0 0.65rem rgba(255, 211, 111, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(255, 211, 111, 0);
  }
}

@keyframes arrow-bounce {
  0%,
  100% {
    transform: translateY(-0.35rem) rotate(45deg);
  }
  50% {
    transform: translateY(0.35rem) rotate(45deg);
  }
}

@keyframes marker-glow {
  0%,
  100% {
    box-shadow: 0 0 0 rgba(255, 211, 111, 0);
  }
  50% {
    box-shadow: 0 0 1.2rem rgba(255, 211, 111, 0.18);
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

@keyframes wake-ripple {
  0% {
    opacity: 0;
    transform: scale(0.6);
  }
  16% {
    opacity: 0.48;
  }
  100% {
    opacity: 0;
    transform: scale(4.5);
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

@keyframes nav-glass-fade {
  0% {
    opacity: 0;
  }

  18% {
    opacity: 1;
  }

  100% {
    opacity: 0;
  }
}

@keyframes article-menu-reveal {
  from {
    opacity: 0;
    transform: translate(-50%, -0.4rem);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

@media (max-width: 900px) {
  .floating-nav {
    flex-direction: column;
    gap: 0.9rem;
    padding-inline: 1rem;
  }

  nav {
    flex-wrap: wrap;
    justify-content: center;
  }

  .article-nav-panel {
    top: calc(100% + 0.45rem);
  }

  .feature-grid,
  .split-section {
    grid-template-columns: 1fr;
  }

  .identity-deck {
    max-width: 44rem;
  }

  .hero-coordinates,
  .hero-compass {
    display: none;
  }

  .hero-subtitle {
    font-size: 1.1rem;
  }

  .quote-line {
    font-size: 1.25rem;
  }

  .section-heading h2,
  .split-section h2,
  .timeline-section h2 {
    font-size: 2rem;
  }

  .hero-route {
    top: 24%;
    right: -8%;
    width: 15rem;
    height: 10rem;
    opacity: 0.45;
  }

  .voyage-progress {
    right: 0.7rem;
    height: 4.5rem;
  }

  .hero-ripple {
    right: 4%;
    bottom: 16%;
  }
}

@media (max-width: 560px) {
  .identity-deck {
    grid-template-columns: 1fr;
  }

  .vessel-card {
    grid-column: auto;
    flex-direction: column;
    gap: 1rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .floating-nav::before,
  .hero-atmosphere,
  .hero-grain,
  .hero-route,
  .hero-route::after,
  .hero-compass,
  .hero-ripple,
  .hero-copy > *,
  .scroll-arrow,
  .timeline-item span {
    animation: none;
  }

  .article-nav-panel {
    animation: none;
  }

  .hero-copy > * {
    opacity: 1;
  }

  .feature-card {
    transition: none;
  }

  .reveal-section {
    opacity: 1;
    transform: none;
    transition: none;
  }

  .timeline-item {
    transition: none;
  }

  .scroll-indicator {
    transition: none;
  }
}
</style>
