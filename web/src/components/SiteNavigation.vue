<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { fetchSiteSettings } from "../api/site-settings";
import SiteSearchDialog from "./SiteSearchDialog.vue";

const props = defineProps<{ brand?: string }>();

const route = useRoute();
const loadedBrand = ref("个人空间");
const navVisible = ref(true);
const navRevealing = ref(false);
const searchOpen = ref(false);
let lastScrollY = 0;
let revealTimer: number | undefined;
let loadingBrand = false;

const brand = computed(() => props.brand ?? loadedBrand.value);
const usesLightSurface = computed(() => route.path === "/about");

async function loadBrand() {
  if (props.brand || loadingBrand) return;
  loadingBrand = true;
  try {
    loadedBrand.value = (await fetchSiteSettings()).nav_brand;
  } finally {
    loadingBrand = false;
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
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    searchOpen.value = true;
  }
}

onMounted(() => {
  void loadBrand();
  window.addEventListener("scroll", handleScroll, { passive: true });
  window.addEventListener("keydown", handleShortcut);
  handleScroll();
});

watch(
  () => route.path,
  () => {
    navVisible.value = true;
    navRevealing.value = false;
    searchOpen.value = false;
    lastScrollY = window.scrollY;
    void loadBrand();
  },
);

onBeforeUnmount(() => {
  window.removeEventListener("scroll", handleScroll);
  window.removeEventListener("keydown", handleShortcut);
  window.clearTimeout(revealTimer);
});
</script>

<template>
  <header
    :class="[
      'floating-nav',
      { hidden: !navVisible, revealing: navRevealing, 'light-surface': usesLightSurface },
    ]"
  >
    <RouterLink class="brand" :to="{ path: '/', hash: '#hero' }">{{ brand }}</RouterLink>
    <nav aria-label="主导航">
      <button
        class="nav-search-button"
        type="button"
        aria-haspopup="dialog"
        @click="searchOpen = true"
      >
        搜索
      </button>
      <RouterLink :to="{ path: '/', hash: '#hero' }">首页</RouterLink>
      <RouterLink :to="{ path: '/articles', query: { view: 'archive' } }">文章</RouterLink>
      <RouterLink to="/about">关于我</RouterLink>
      <RouterLink :to="{ path: '/', hash: '#timeline' }">航海日志</RouterLink>
    </nav>
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
.floating-nav.light-surface {
  border-bottom: 1px solid rgba(16, 42, 54, 0.1);
  background: rgba(237, 242, 245, 0.86);
  box-shadow: 0 5px 22px rgba(16, 42, 54, 0.055);
  backdrop-filter: blur(15px) saturate(1.2);
}
.floating-nav.light-surface::before {
  display: none;
}
.floating-nav.light-surface .brand,
.floating-nav.light-surface nav a,
.floating-nav.light-surface .nav-search-button {
  color: #173541;
  text-shadow: none;
}
.floating-nav.light-surface nav > a::before,
.floating-nav.light-surface .nav-search-button::before {
  background: #e7674c;
  box-shadow: 0 0 0.55rem rgba(231, 103, 76, 0.28);
}
.floating-nav.light-surface nav > a:hover,
.floating-nav.light-surface nav > a:focus-visible,
.floating-nav.light-surface .nav-search-button:hover,
.floating-nav.light-surface .nav-search-button:focus-visible,
.floating-nav.light-surface nav > a.router-link-active {
  color: #c64f3a;
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
}
@media (prefers-reduced-motion: reduce) {
  .floating-nav::before {
    animation: none;
  }
}
</style>
