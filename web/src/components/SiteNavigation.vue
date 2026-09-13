<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { fetchSiteSettings } from "../api/site-settings";
import { fetchGallery } from "../api/gallery";
import OceanIcon from "./OceanIcon.vue";
import SiteSearchDialog from "./SiteSearchDialog.vue";

const props = defineProps<{ brand?: string }>();

const route = useRoute();
const loadedBrand = ref("个人空间");
const navVisible = ref(true);
const navRevealing = ref(false);
const searchOpen = ref(false);
const mobileMenuOpen = ref(false);
const openMenu = ref<"reading" | "voyage" | null>(null);
const suppressedMenu = ref<"reading" | "voyage" | null>(null);
const galleryEntryVisible = ref(true);
const dashboardEntryVisible = ref(false);
const articleNavigationResetKey = "articles-navigation-reset";
let lastScrollY = 0;
let revealTimer: number | undefined;
let articleNavigationResetFrame: number | undefined;
let loadingBrand = false;

const brand = computed(() => props.brand ?? loadedBrand.value);
const readingActive = computed(() => /^\/(articles|series|notes)(\/|$)/.test(route.path));
const voyageActive = computed(() => route.path === "/dashboard" || route.path.startsWith("/gallery"));
const usesLightSurface = computed(() => route.path === "/about" || route.path === "/privacy" || route.path === "/guestbook" || /^\/articles\/[^/]+/.test(route.path));
const usesSystemSurface = computed(() => route.path === "/icons");

async function loadBrand() {
  if (loadingBrand) return;
  loadingBrand = true;
  try {
    const settings = await fetchSiteSettings();
    loadedBrand.value = settings.nav_brand;
    dashboardEntryVisible.value = settings.dashboard_show_entry;
  } catch (error) {
    console.error("导航站点设置加载失败", error);
  } finally {
    loadingBrand = false;
  }
}

async function loadGalleryVisibility() {
  try {
    galleryEntryVisible.value = (await fetchGallery()).settings.show_entry;
  } catch {
    galleryEntryVisible.value = true;
  }
}

function handleScroll() {
  const currentY = window.scrollY;
  const scrollingUp = currentY < lastScrollY;
  navVisible.value = currentY < 24 || scrollingUp;

  if (scrollingUp && currentY >= 24) {
    navRevealing.value = true;
    window.clearTimeout(revealTimer);
    revealTimer = window.setTimeout(() => {
      navRevealing.value = false;
    }, 1200);
  } else if (!scrollingUp) {
    navRevealing.value = false;
    window.clearTimeout(revealTimer);
  }

  lastScrollY = currentY;
}

function handleShortcut(event: KeyboardEvent) {
  if (event.key === "Escape") {
    searchOpen.value = false;
    mobileMenuOpen.value = false;
    openMenu.value = null;
    return;
  }
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    searchOpen.value = true;
    mobileMenuOpen.value = false;
    openMenu.value = null;
  }
}

function toggleMenu(menu: "reading" | "voyage") {
  suppressedMenu.value = null;
  openMenu.value = openMenu.value === menu ? null : menu;
}

function handleMenuSelection(menu: "reading" | "voyage", event: MouseEvent) {
  openMenu.value = null;
  suppressedMenu.value = menu;
  if (event.currentTarget instanceof HTMLElement) {
    event.currentTarget.blur();
  }
}

function releaseSuppressedMenu(menu: "reading" | "voyage") {
  if (suppressedMenu.value === menu) {
    suppressedMenu.value = null;
  }
}

function closeMenus() {
  mobileMenuOpen.value = false;
  openMenu.value = null;
}

function handleDocumentClick() {
  openMenu.value = null;
}

function handleArticlesNavigation(event: MouseEvent) {
  if (
    event.button !== 0 ||
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey
  ) {
    return;
  }

  if (route.path === "/articles") {
    sessionStorage.removeItem(articleNavigationResetKey);
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
    return;
  }

  sessionStorage.setItem(articleNavigationResetKey, "1");
  if (articleNavigationResetFrame !== undefined) {
    window.cancelAnimationFrame(articleNavigationResetFrame);
  }
  articleNavigationResetFrame = window.requestAnimationFrame(() => {
    articleNavigationResetFrame = window.requestAnimationFrame(() => {
      articleNavigationResetFrame = undefined;
      if (window.location.pathname !== "/articles") return;
      sessionStorage.removeItem(articleNavigationResetKey);
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
    });
  });
}

onMounted(() => {
  void loadBrand();
  void loadGalleryVisibility();
  window.addEventListener("scroll", handleScroll, { passive: true });
  window.addEventListener("keydown", handleShortcut);
  document.addEventListener("click", handleDocumentClick);
  handleScroll();
});

watch(
  () => route.path,
  () => {
    navVisible.value = true;
    navRevealing.value = false;
    searchOpen.value = false;
    mobileMenuOpen.value = false;
    openMenu.value = null;
    suppressedMenu.value = null;
    lastScrollY = window.scrollY;
    void loadBrand();
    void loadGalleryVisibility();
  },
);

onBeforeUnmount(() => {
  window.removeEventListener("scroll", handleScroll);
  window.removeEventListener("keydown", handleShortcut);
  document.removeEventListener("click", handleDocumentClick);
  window.clearTimeout(revealTimer);
  if (articleNavigationResetFrame !== undefined) {
    window.cancelAnimationFrame(articleNavigationResetFrame);
  }
});
</script>

<template>
  <header
    :class="[
      'floating-nav',
      { hidden: !navVisible, revealing: navRevealing, 'light-surface': usesLightSurface, 'system-surface': usesSystemSurface, 'menu-open': mobileMenuOpen },
    ]"
  >
    <RouterLink class="brand" :to="{ path: '/', hash: '#hero' }" @click="closeMenus">{{ brand }}</RouterLink>
    <nav class="main-nav" aria-label="主导航" @click.stop>
      <RouterLink class="nav-primary-link" :to="{ path: '/', hash: '#hero' }" @click="closeMenus"><OceanIcon name="home" :size="18" />首页</RouterLink>
      <div class="nav-menu-group" :class="{ open: openMenu === 'reading', active: readingActive, suppressed: suppressedMenu === 'reading' }" @pointerleave="releaseSuppressedMenu('reading')">
        <button class="nav-group-trigger" type="button" :aria-expanded="openMenu === 'reading'" aria-haspopup="true" @click="toggleMenu('reading')">
          <OceanIcon name="archive" :size="18" />阅读<span class="iconfont nav-group-icon" aria-hidden="true">&#xe64e;</span>
        </button>
        <div class="nav-dropdown" role="menu" aria-label="阅读">
          <RouterLink :to="{ path: '/articles', query: { view: 'archive' } }" role="menuitem" @click="handleArticlesNavigation($event); handleMenuSelection('reading', $event)"><OceanIcon name="articles" :size="18" /><span><b>文章</b><small>按时间回看全部记录</small></span></RouterLink>
          <RouterLink to="/series" role="menuitem" @click="handleMenuSelection('reading', $event)"><OceanIcon name="series" :size="18" /><span><b>专题</b><small>沿航线连续阅读</small></span></RouterLink>
          <RouterLink to="/notes" role="menuitem" @click="handleMenuSelection('reading', $event)"><OceanIcon name="notes" :size="18" /><span><b>动态</b><small>接收最近的简短信号</small></span></RouterLink>
        </div>
      </div>
      <div class="nav-menu-group" :class="{ open: openMenu === 'voyage', active: voyageActive, suppressed: suppressedMenu === 'voyage' }" @pointerleave="releaseSuppressedMenu('voyage')">
        <button class="nav-group-trigger" type="button" :aria-expanded="openMenu === 'voyage'" aria-haspopup="true" @click="toggleMenu('voyage')">
          <OceanIcon name="favorite" :size="18" />航海<span class="iconfont nav-group-icon" aria-hidden="true">&#xe64e;</span>
        </button>
        <div class="nav-dropdown" role="menu" aria-label="航海">
          <RouterLink v-if="dashboardEntryVisible" to="/dashboard" role="menuitem" @click="handleMenuSelection('voyage', $event)"><OceanIcon name="views" :size="18" /><span><b>文章大屏</b><small>查看全站航行数据</small></span></RouterLink>
          <RouterLink v-if="galleryEntryVisible" to="/gallery" role="menuitem" @click="handleMenuSelection('voyage', $event)"><OceanIcon name="gallery" :size="18" /><span><b>3D 展厅</b><small>漫游人物档案</small></span></RouterLink>
          <span v-if="!dashboardEntryVisible && !galleryEntryVisible" class="nav-dropdown-empty">暂无开放航线</span>
        </div>
      </div>
      <RouterLink class="nav-primary-link" to="/about" @click="closeMenus"><OceanIcon name="about" :size="18" />关于我</RouterLink>
    </nav>
    <div class="nav-actions" @click.stop>
      <button
        class="nav-search-button"
        type="button"
        aria-haspopup="dialog"
        aria-label="打开搜索"
        @click="searchOpen = true; closeMenus()"
      >
        <OceanIcon name="search" :size="20" />
        搜索
      </button>
      <RouterLink class="nav-cta" to="/guestbook" @click="closeMenus"><OceanIcon name="comment" :size="18" />留言</RouterLink>
    </div>
    <button class="mobile-menu-toggle" type="button" :aria-expanded="mobileMenuOpen" aria-controls="mobile-navigation" :aria-label="mobileMenuOpen ? '关闭导航菜单' : '打开导航菜单'" @click="mobileMenuOpen = !mobileMenuOpen; openMenu = null">
      <span aria-hidden="true"></span><span aria-hidden="true"></span>
    </button>
    <div v-if="mobileMenuOpen" id="mobile-navigation" class="mobile-nav-panel" @click.stop>
      <RouterLink class="mobile-nav-home" :to="{ path: '/', hash: '#hero' }" @click="closeMenus"><OceanIcon name="home" :size="18" />首页</RouterLink>
      <div class="mobile-nav-group"><p><OceanIcon name="archive" :size="15" />阅读</p><RouterLink to="/articles" @click="closeMenus"><OceanIcon name="articles" :size="17" />文章</RouterLink><RouterLink to="/series" @click="closeMenus"><OceanIcon name="series" :size="17" />专题</RouterLink><RouterLink to="/notes" @click="closeMenus"><OceanIcon name="notes" :size="17" />动态</RouterLink></div>
      <div class="mobile-nav-group"><p><OceanIcon name="favorite" :size="15" />航海</p><RouterLink v-if="dashboardEntryVisible" to="/dashboard" @click="closeMenus"><OceanIcon name="views" :size="17" />文章大屏</RouterLink><RouterLink v-if="galleryEntryVisible" to="/gallery" @click="closeMenus"><OceanIcon name="gallery" :size="17" />3D 展厅</RouterLink><span v-if="!dashboardEntryVisible && !galleryEntryVisible" class="nav-dropdown-empty">暂无开放航线</span></div>
      <RouterLink to="/about" @click="closeMenus"><OceanIcon name="about" :size="18" />关于我</RouterLink>
      <RouterLink class="mobile-nav-cta" to="/guestbook" @click="closeMenus"><OceanIcon name="comment" :size="18" />留言板</RouterLink>
      <button class="mobile-nav-search" type="button" @click="searchOpen = true; closeMenus()"><OceanIcon name="search" :size="18" />搜索</button>
    </div>
  </header>
  <SiteSearchDialog :open="searchOpen" @close="searchOpen = false" />
</template>

<style scoped>
.floating-nav {
  position: fixed;
  inset: 0 0 auto;
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
}
.floating-nav::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: linear-gradient(180deg, rgba(8, 22, 36, 0.72), rgba(8, 22, 36, 0.34));
  backdrop-filter: blur(12px);
  opacity: 0;
}
.floating-nav > * {
  position: relative;
  z-index: 1;
}
.floating-nav.light-surface,
.floating-nav.system-surface {
  background: transparent;
  border-bottom: 1px solid transparent;
  backdrop-filter: none;
}
.floating-nav.light-surface::before,
.floating-nav.system-surface::before {
  display: block;
  border-bottom: 1px solid rgba(24, 49, 56, 0.07);
  background: rgba(255, 250, 242, 0.88);
  backdrop-filter: blur(15px) saturate(1.08);
}
.floating-nav.light-surface .brand,
.floating-nav.light-surface .nav-primary-link,
.floating-nav.light-surface .nav-group-trigger,
.floating-nav.light-surface .nav-search-button,
.floating-nav.system-surface .brand,
.floating-nav.system-surface .nav-primary-link,
.floating-nav.system-surface .nav-group-trigger,
.floating-nav.system-surface .nav-search-button {
  color: #183138;
  text-shadow: none;
}
.floating-nav.light-surface nav > a::before,
.floating-nav.light-surface .nav-search-button::before,
.floating-nav.system-surface nav > a::before,
.floating-nav.system-surface .nav-search-button::before {
  background: #276f6d;
  box-shadow: none;
}
.floating-nav.light-surface .nav-primary-link:hover,
.floating-nav.light-surface .nav-primary-link:focus-visible,
.floating-nav.light-surface .nav-group-trigger:hover,
.floating-nav.light-surface .nav-group-trigger:focus-visible,
.floating-nav.light-surface .nav-menu-group.active .nav-group-trigger,
.floating-nav.light-surface .nav-menu-group.open .nav-group-trigger,
.floating-nav.light-surface .nav-search-button:hover,
.floating-nav.light-surface .nav-search-button:focus-visible,
.floating-nav.light-surface .nav-primary-link.router-link-active {
  color: #276f6d;
}
.floating-nav.system-surface .nav-primary-link:hover,
.floating-nav.system-surface .nav-primary-link:focus-visible,
.floating-nav.system-surface .nav-group-trigger:hover,
.floating-nav.system-surface .nav-group-trigger:focus-visible,
.floating-nav.system-surface .nav-menu-group.active .nav-group-trigger,
.floating-nav.system-surface .nav-menu-group.open .nav-group-trigger,
.floating-nav.system-surface .nav-search-button:hover,
.floating-nav.system-surface .nav-search-button:focus-visible,
.floating-nav.system-surface .nav-primary-link.router-link-active {
  color: #276f6d;
}
.floating-nav.revealing::before {
  animation: nav-glass-fade 1.2s ease both;
}
.floating-nav.light-surface.revealing::before {
  animation: nav-light-fade 1.2s ease both;
}
.floating-nav.hidden {
  opacity: 0;
  transform: translateY(-110%);
  pointer-events: none;
}
.brand,
nav a,
.nav-search-button {
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
.nav-search-button {
  position: relative;
  display: inline-flex;
  gap: 0.32rem;
  align-items: center;
  padding-bottom: 0.45rem;
}
nav > a::before,
.nav-search-button::before {
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
.nav-search-button:hover::before,
.nav-search-button:focus-visible::before {
  right: 0;
  left: 0;
}
nav > a:hover,
nav > a:focus-visible,
.nav-search-button:hover,
.nav-search-button:focus-visible {
  color: #ffd36f;
}
.nav-search-button {
  padding-right: 0;
  padding-left: 0;
  border: 0;
  background: transparent;
  font: inherit;
  cursor: pointer;
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
@keyframes nav-light-fade {
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
    gap: 0.55rem;
    padding: 0.78rem 1rem 0.7rem;
  }
  nav {
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.65rem 1rem;
    font-size: 0.9rem;
  }
}
@media (prefers-color-scheme: dark) {
  .floating-nav.system-surface::before {
    border-color: rgba(246, 235, 212, 0.08);
    background: rgba(7, 28, 41, 0.9);
  }
  .floating-nav.system-surface .brand,
  .floating-nav.system-surface .nav-primary-link,
  .floating-nav.system-surface .nav-group-trigger,
  .floating-nav.system-surface .nav-cta,
  .floating-nav.system-surface .nav-search-button {
    color: #f6ebd4;
  }
  .floating-nav.system-surface nav > a::before,
  .floating-nav.system-surface .nav-search-button::before {
    background: #f0c162;
  }
  .floating-nav.system-surface .nav-primary-link:hover,
  .floating-nav.system-surface .nav-primary-link:focus-visible,
  .floating-nav.system-surface .nav-group-trigger:hover,
  .floating-nav.system-surface .nav-group-trigger:focus-visible,
  .floating-nav.system-surface .nav-menu-group.active .nav-group-trigger,
  .floating-nav.system-surface .nav-menu-group.open .nav-group-trigger,
  .floating-nav.system-surface .nav-cta:hover,
  .floating-nav.system-surface .nav-cta:focus-visible,
  .floating-nav.system-surface .nav-search-button:hover,
  .floating-nav.system-surface .nav-search-button:focus-visible,
  .floating-nav.system-surface .nav-primary-link.router-link-active {
    color: #f0c162;
  }
}
@media (prefers-reduced-motion: reduce) {
  .floating-nav {
    transition: none;
  }
  .floating-nav::before {
    animation: none;
  }
}
</style>

<style scoped>
/* 新版导航：桌面分组、移动抽屉和单一留言 CTA。 */
.floating-nav { --nav-accent: #ffd36f; gap: 1.35rem; padding: 1.1rem 2.4rem; transition: transform .75s cubic-bezier(.22,.72,.25,1), opacity .75s ease; }
.floating-nav::before { z-index: 0; opacity: 0; }
.floating-nav.light-surface, .floating-nav.system-surface { --nav-accent: #276f6d; }
.floating-nav.light-surface::before, .floating-nav.system-surface::before { opacity: 0; }
.brand { flex: 0 0 auto; font-size: 1rem; font-weight: 700; }
.floating-nav.light-surface .nav-cta, .floating-nav.system-surface .nav-cta { color: #183138; text-shadow: none; }
.floating-nav.light-surface .nav-cta:hover, .floating-nav.light-surface .nav-cta:focus-visible, .floating-nav.system-surface .nav-cta:hover, .floating-nav.system-surface .nav-cta:focus-visible { color: #276f6d; }
.main-nav { display: flex; align-items: center; gap: 1.35rem; margin-left: auto; font-size: .95rem; font-weight: 700; }
.nav-primary-link, .nav-group-trigger, .nav-search-button { position: relative; display: inline-flex; gap: .32rem; align-items: center; min-height: auto; padding: 0 0 .45rem; border: 0; color: #fff9ef; background: transparent; font: inherit; text-decoration: none; text-shadow: 0 2px 12px rgba(0,0,0,.25); cursor: pointer; }
.main-nav > a::before, .nav-search-button::before { content: none; }
.nav-primary-link::after, .nav-group-trigger::after, .nav-search-button::after, .nav-cta::after { position: absolute; right: 50%; bottom: 0; left: 50%; height: 2px; content: ""; background: var(--nav-accent); box-shadow: 0 0 .65rem color-mix(in srgb, var(--nav-accent) 50%, transparent); transition: left .28s cubic-bezier(.2,.75,.28,1), right .28s cubic-bezier(.2,.75,.28,1); }
.nav-primary-link:hover::after, .nav-primary-link:focus-visible::after, .nav-primary-link.router-link-active::after, .nav-menu-group.active .nav-group-trigger::after, .nav-menu-group.open .nav-group-trigger::after, .nav-search-button:hover::after, .nav-search-button:focus-visible::after, .nav-cta:hover::after, .nav-cta:focus-visible::after, .nav-cta.router-link-active::after { right: 0; left: 0; }
.nav-primary-link:hover, .nav-primary-link:focus-visible, .nav-primary-link.router-link-active, .nav-group-trigger:hover, .nav-group-trigger:focus-visible, .nav-menu-group.active .nav-group-trigger, .nav-menu-group.open .nav-group-trigger, .nav-search-button:hover, .nav-search-button:focus-visible, .nav-cta:hover, .nav-cta:focus-visible, .nav-cta.router-link-active { color: var(--nav-accent); }
.nav-group-icon { display: inline-flex; margin-left: .04rem; font-size: .9rem; line-height: 1; transform: rotate(0deg); transition: transform .24s cubic-bezier(.2,.75,.28,1); }
.nav-menu-group:hover .nav-group-icon, .nav-menu-group:focus-within .nav-group-icon, .nav-menu-group.open .nav-group-icon { transform: rotate(180deg); }
.nav-menu-group { position: relative; }
.nav-menu-group::after { position: absolute; top: 100%; right: -1rem; left: -1rem; height: .55rem; content: ""; }
.nav-dropdown { position: absolute; top: calc(100% + .48rem); left: 50%; display: grid; gap: .2rem; width: 14.5rem; padding: .55rem; border: 1px solid rgba(216,169,78,.28); border-radius: 11px; background: rgba(8,31,41,.96); box-shadow: 0 1.4rem 2.8rem rgba(4,20,29,.22); opacity: 0; pointer-events: none; transform: translate(-50%,-.35rem); transition: opacity .18s ease, transform .18s ease; }
.nav-menu-group.open .nav-dropdown, .nav-menu-group:focus-within .nav-dropdown, .nav-menu-group:hover .nav-dropdown { opacity: 1; pointer-events: auto; transform: translate(-50%,0); }
.nav-menu-group.suppressed .nav-dropdown { opacity: 0; pointer-events: none; transform: translate(-50%,-.35rem); }
.nav-menu-group.suppressed .nav-group-icon { transform: rotate(0deg); }
.nav-dropdown a { display: grid; grid-template-columns: 1.35rem minmax(0,1fr); gap: .55rem; align-items: start; padding: .7rem .65rem; border-radius: 7px; color: #f7eedc; text-decoration: none; text-shadow: none; transition: color .16s ease, background-color .16s ease; }
.nav-dropdown a:hover, .nav-dropdown a:focus-visible { color: #ffd36f; background: rgba(255,211,111,.09); }
.nav-dropdown a > span { display: grid; gap: .2rem; }
.nav-dropdown b { font-size: .82rem; }
.nav-dropdown small { color: rgba(247,238,220,.58); font-size: .68rem; font-weight: 500; line-height: 1.4; }
.nav-dropdown-empty { padding: .8rem .65rem; color: rgba(247,238,220,.6); font-size: .74rem; }
.nav-actions { display: flex; gap: 1.35rem; align-items: center; flex: 0 0 auto; font-size: .95rem; font-weight: 700; line-height: 1.5; }
.nav-search-button { gap: .32rem; padding-inline: 0; }
.nav-cta { position: relative; display: inline-flex; gap: .32rem; align-items: center; min-height: auto; padding: 0 0 .45rem; border: 0; border-radius: 0; color: #fff8e9; background: transparent; font: inherit; text-decoration: none; text-shadow: 0 2px 12px rgba(0,0,0,.25); transition: color .18s ease; }
.nav-cta:hover, .nav-cta:focus-visible { background: transparent; }
.mobile-menu-toggle, .mobile-nav-panel { display: none; }
@media (max-width: 900px) {
  .floating-nav { flex-wrap: wrap; gap: .7rem 1rem; padding: .78rem 1rem .7rem; }
  .brand { margin-right: auto; }
  .main-nav, .nav-actions { display: none; }
  .mobile-menu-toggle { position: relative; display: block; width: 2.7rem; height: 2.7rem; border: 1px solid rgba(255,249,239,.34); border-radius: 8px; color: #fff9ef; background: rgba(8,22,36,.24); cursor: pointer; }
  .mobile-menu-toggle span { position: absolute; top: 50%; left: 50%; display: block; width: 1.15rem; height: 2px; margin-top: -1px; margin-left: -.575rem; background: currentColor; transform-origin: center; transition: transform .18s ease; }
  .mobile-menu-toggle span:first-child { transform: translateY(-.18rem); }
  .mobile-menu-toggle span:last-child { transform: translateY(.18rem); }
  .floating-nav.menu-open .mobile-menu-toggle span:first-child { transform: rotate(45deg); }
  .floating-nav.menu-open .mobile-menu-toggle span:last-child { transform: rotate(-45deg); }
  .floating-nav.light-surface .mobile-menu-toggle, .floating-nav.system-surface .mobile-menu-toggle { border-color: rgba(24,49,56,.22); color: #183138; background: rgba(255,250,242,.55); }
  .mobile-nav-panel { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 1.15rem .8rem; width: 100%; padding: 1rem; border: 1px solid rgba(255,249,239,.2); border-radius: 10px; background: rgba(8,31,41,.96); box-shadow: 0 1.2rem 2.4rem rgba(4,20,29,.28); backdrop-filter: blur(14px) saturate(1.08); }
  .mobile-nav-panel a, .mobile-nav-search { display: inline-flex; gap: .4rem; align-items: center; min-height: 2.6rem; padding: .5rem .65rem; border: 0; border-radius: 7px; color: #fff9ef; background: rgba(255,249,239,.05); font: inherit; font-size: .86rem; font-weight: 700; text-decoration: none; text-shadow: 0 2px 12px rgba(0,0,0,.25); }
  .mobile-nav-panel a:hover, .mobile-nav-panel a:focus-visible, .mobile-nav-search:hover, .mobile-nav-search:focus-visible { color: #ffd36f; background: rgba(255,211,111,.1); }
  .mobile-nav-home, .mobile-nav-cta { grid-column: 1 / -1; }
  .mobile-nav-group { display: grid; gap: .25rem; align-content: start; }
  .mobile-nav-group p { display: inline-flex; gap: .32rem; align-items: center; margin: 0 0 .25rem; color: #ffd36f; font: 700 .66rem "IBM Plex Mono", monospace; letter-spacing: .08em; }
  .mobile-nav-group a { background: transparent; }
  .mobile-nav-cta { color: #132f39 !important; background: #f0c162 !important; text-shadow: none !important; }
  .mobile-nav-search { justify-content: center; color: #ffd36f; background: transparent; }
  .floating-nav.light-surface .mobile-nav-panel, .floating-nav.system-surface .mobile-nav-panel { border-color: rgba(24,49,56,.14); background: rgba(255,250,242,.98); box-shadow: 0 1.2rem 2.4rem rgba(24,49,56,.14); }
  .floating-nav.light-surface .mobile-nav-panel a, .floating-nav.light-surface .mobile-nav-search, .floating-nav.system-surface .mobile-nav-panel a, .floating-nav.system-surface .mobile-nav-search { color: #183138; text-shadow: none; background: rgba(39,111,109,.06); }
  .floating-nav.light-surface .mobile-nav-group p, .floating-nav.system-surface .mobile-nav-group p { color: #276f6d; }
  .floating-nav.light-surface .mobile-nav-panel a:hover, .floating-nav.light-surface .mobile-nav-panel a:focus-visible, .floating-nav.light-surface .mobile-nav-search:hover, .floating-nav.light-surface .mobile-nav-search:focus-visible, .floating-nav.system-surface .mobile-nav-panel a:hover, .floating-nav.system-surface .mobile-nav-panel a:focus-visible, .floating-nav.system-surface .mobile-nav-search:hover, .floating-nav.system-surface .mobile-nav-search:focus-visible { color: #276f6d; background: rgba(39,111,109,.12); }
}
@media (prefers-color-scheme: dark) {
  .floating-nav.system-surface { --nav-accent: #f0c162; }
  .floating-nav.system-surface .nav-cta { color: #f6ebd4; text-shadow: 0 2px 12px rgba(0,0,0,.25); }
  .floating-nav.system-surface .nav-cta:hover, .floating-nav.system-surface .nav-cta:focus-visible { color: #f0c162; }
  .floating-nav.system-surface .mobile-nav-panel a, .floating-nav.system-surface .mobile-nav-search { color: #f6ebd4; text-shadow: 0 2px 12px rgba(0,0,0,.25); background: rgba(255,249,239,.05); }
  .floating-nav.system-surface .mobile-nav-panel { border-color: rgba(246,235,212,.12); background: rgba(7,28,41,.98); box-shadow: 0 1.2rem 2.4rem rgba(0,0,0,.32); }
  .floating-nav.system-surface .mobile-nav-group p { color: #f0c162; }
  .floating-nav.system-surface .mobile-nav-panel a:hover, .floating-nav.system-surface .mobile-nav-panel a:focus-visible, .floating-nav.system-surface .mobile-nav-search:hover, .floating-nav.system-surface .mobile-nav-search:focus-visible { color: #f0c162; background: rgba(255,211,111,.1); }
}
@media (prefers-reduced-motion: reduce) { .floating-nav, .floating-nav::before, .nav-primary-link::after, .nav-group-trigger::after, .nav-search-button::after, .nav-cta::after, .nav-group-icon, .nav-dropdown, .nav-cta, .mobile-menu-toggle span { transition: none; } }
</style>
