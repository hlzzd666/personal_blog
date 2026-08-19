<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { fetchSiteSettings, type SiteSettings } from "./api/site-settings";

const fallbackSettings: SiteSettings = {
  site_subtitle: "自由、梦想、伙伴，这里记录我向前航行的每一步。",
  hero_image_url: "https://images.hdqwalls.com/download/one-piece-anime-artwork-i6-2560x1440.jpg",
  nav_brand: "某某某的个人空间",
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

const settings = ref<SiteSettings>(fallbackSettings);
const navVisible = ref(true);
const navRevealing = ref(false);
const activeQuoteIndex = ref(0);
const typedCharacters = ref(0);

let quoteTimer: number | undefined;
let switchTimer: number | undefined;
let navRevealTimer: number | undefined;
let lastScrollY = 0;

const activeQuote = computed(() => settings.value.quotes[activeQuoteIndex.value] ?? fallbackSettings.quotes[0]);
const typedQuote = computed(() => activeQuote.value.text.slice(0, typedCharacters.value));

async function loadSettings() {
  try {
    settings.value = await fetchSiteSettings();
  } catch {
    settings.value = fallbackSettings;
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
}

onMounted(async () => {
  await loadSettings();
  startTypingCycle();
  window.addEventListener("scroll", handleScroll, { passive: true });
});

onBeforeUnmount(() => {
  window.removeEventListener("scroll", handleScroll);
  window.clearInterval(quoteTimer);
  window.clearTimeout(switchTimer);
  window.clearTimeout(navRevealTimer);
});
</script>

<template>
  <div class="page-shell">
    <header :class="['floating-nav', { hidden: !navVisible, revealing: navRevealing }]">
      <a class="brand" href="#hero">{{ settings.nav_brand }}</a>
      <nav aria-label="主导航">
        <a href="#hero">首页</a>
        <a href="#articles">文章</a>
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
      <div class="hero-route" aria-hidden="true">
        <span class="route-point"></span>
      </div>
      <div class="hero-overlay">
        <div class="hero-copy">
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
      <section id="articles" class="content-section feature-grid">
        <article class="feature-card feature-card-accent">
          <p class="section-tag">LATEST ARC</p>
          <h2>最新文章</h2>
          <p>这里后面接文章列表、分类与推荐位，现在先保留成首页的主内容入口。</p>
        </article>
        <article class="feature-card">
          <p class="section-tag">CREW NOTE</p>
          <h2>精选专题</h2>
          <p>适合放技术专栏、生活记录或长期系列，让首页有明确的内容分发方向。</p>
        </article>
        <article class="feature-card">
          <p class="section-tag">TREASURE MAP</p>
          <h2>站内导航</h2>
          <p>后面可以放标签、归档、热门文章和搜索入口，作为向下浏览后的信息中枢。</p>
        </article>
      </section>

      <section id="about" class="content-section split-section">
        <div>
          <p class="section-tag">ABOUT CAPTAIN</p>
          <h2>关于自己</h2>
          <p>
            这一块用来放你的简介、身份标签和长期在写的主题。首页会先给一个轻量版本，再引导访客进入完整的关于页。
          </p>
        </div>
        <div class="glass-panel">
          <p>建议放 3 个关键词：</p>
          <ul>
            <li>开发者</li>
            <li>写作者</li>
            <li>长期主义者</li>
          </ul>
        </div>
      </section>

      <section id="timeline" class="content-section timeline-section">
        <p class="section-tag">VOYAGE LOG</p>
        <h2>航海日志</h2>
        <div class="timeline">
          <div class="timeline-item">
            <span>01</span>
            <p>建站起航，确定首页视觉与博客主题。</p>
          </div>
          <div class="timeline-item">
            <span>02</span>
            <p>文章模块接入后，这里可以展示新的里程碑和阶段进展。</p>
          </div>
          <div class="timeline-item">
            <span>03</span>
            <p>后续可扩展为真实的成长、项目、学习时间线。</p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.page-shell {
  color: #fef9ef;
}

.floating-nav {
  position: fixed;
  inset: 0 0 auto 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
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
nav a {
  color: #fff9ef;
  text-decoration: none;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
}

.brand {
  font-weight: 700;
  font-size: 1.15rem;
}

nav {
  display: flex;
  gap: 1.2rem;
  font-size: 0.98rem;
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
    linear-gradient(116deg, transparent 20%, rgba(255, 211, 111, 0.09) 46%, transparent 66%),
    repeating-linear-gradient(172deg, transparent 0 16px, rgba(255, 255, 255, 0.025) 17px 18px, transparent 19px 34px);
  background-size: 220% 100%, 100% 100%;
  mix-blend-mode: screen;
  opacity: 0.65;
  animation: sea-glow 16s ease-in-out infinite alternate;
}

.hero-route {
  position: absolute;
  top: 29%;
  right: 8%;
  width: min(24vw, 20rem);
  height: min(18vw, 14rem);
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
  font-size: clamp(1.1rem, 2.2vw, 1.5rem);
  line-height: 1.8;
  color: rgba(255, 248, 233, 0.9);
}

.quote-box {
  margin-top: 0.2rem;
  min-height: 5.2rem;
}

.quote-line {
  margin: 0;
  font-size: clamp(1.15rem, 2.4vw, 1.8rem);
  font-weight: 600;
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
  background:
    radial-gradient(circle at top right, rgba(255, 213, 111, 0.18), transparent 18rem),
    linear-gradient(180deg, #08111d, #0d1e31 35%, #10283b 100%);
}

.content-section {
  max-width: 1180px;
  margin: 0 auto;
  padding: 5rem 1.5rem;
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
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(14px);
  border-radius: 28px;
}

.feature-card {
  padding: 2rem;
  transition:
    transform 0.35s ease,
    border-color 0.35s ease,
    background-color 0.35s ease;
}

.feature-card:hover {
  transform: translateY(-0.45rem);
  border-color: rgba(255, 211, 111, 0.42);
}

.feature-card-accent {
  background: linear-gradient(160deg, rgba(204, 87, 55, 0.32), rgba(255, 255, 255, 0.06));
}

.section-tag {
  margin: 0 0 0.75rem;
  color: #ffd36f;
  letter-spacing: 0.22em;
  font-size: 0.78rem;
}

.feature-card h2,
.split-section h2,
.timeline-section h2 {
  margin: 0 0 1rem;
  font-family: var(--display-font);
  font-size: clamp(2rem, 4vw, 3.3rem);
}

.feature-card p,
.split-section p,
.timeline-item p,
.glass-panel p,
.glass-panel li {
  color: rgba(255, 249, 239, 0.82);
  line-height: 1.8;
}

.split-section {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.85fr);
  gap: 1.5rem;
  align-items: start;
}

.glass-panel {
  padding: 2rem;
}

.glass-panel ul {
  margin: 1rem 0 0;
  padding-left: 1.2rem;
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
  padding: 1.4rem 1.5rem;
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
    background-position: 0% 0%, 0 0;
  }
  to {
    background-position: 100% 0%, 0 14px;
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

  .feature-grid,
  .split-section {
    grid-template-columns: 1fr;
  }

  .hero-route {
    top: 24%;
    right: -8%;
    width: 15rem;
    height: 10rem;
    opacity: 0.45;
  }
}

@media (prefers-reduced-motion: reduce) {
  .floating-nav::before,
  .hero-atmosphere,
  .hero-route,
  .hero-route::after,
  .hero-copy > *,
  .scroll-arrow,
  .timeline-item span {
    animation: none;
  }

  .hero-copy > * {
    opacity: 1;
  }

  .feature-card {
    transition: none;
  }

  .scroll-indicator {
    transition: none;
  }
}
</style>
