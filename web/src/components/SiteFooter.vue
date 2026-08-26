<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const currentYear = new Date().getFullYear();
const light = computed(() => route.path === "/about" || route.path === "/privacy");
</script>

<template>
  <footer :class="['site-footer', { light }]">
    <div>
      <strong>个人航海日志</strong>
      <span>© {{ currentYear }} 内容与代码持续更新</span>
    </div>
    <nav aria-label="页脚导航">
      <RouterLink to="/series">专题</RouterLink>
      <RouterLink to="/notes">动态</RouterLink>
      <RouterLink to="/privacy">隐私说明</RouterLink>
      <a href="/api/feed.xml" target="_blank" rel="alternate">RSS</a>
    </nav>
  </footer>
</template>

<style scoped>
.site-footer { display: flex; justify-content: space-between; gap: 1.5rem; align-items: center; padding: 2rem clamp(1rem, 5vw, 4rem); border-top: 1px solid rgba(244, 240, 223, 0.12); color: rgba(244, 240, 223, 0.7); background: #051923; font-family: "Noto Sans SC", sans-serif; }
.site-footer div { display: grid; gap: 0.25rem; }
.site-footer strong { color: #f4f0df; font-family: var(--display-font); }
.site-footer span { font-size: 0.72rem; }
.site-footer nav { display: flex; flex-wrap: wrap; gap: 1rem; }
.site-footer a { color: inherit; font-size: 0.78rem; text-decoration: none; transition: color 180ms ease; }
.site-footer a:hover, .site-footer a:focus-visible { color: #f4ca58; }
.site-footer.light { border-color: rgba(16, 42, 54, 0.1); color: rgba(23, 53, 65, 0.66); background: #edf2f5; }
.site-footer.light strong { color: #173541; }
.site-footer.light a:hover, .site-footer.light a:focus-visible { color: #c64f3a; }
@media (max-width: 680px) { .site-footer { align-items: flex-start; flex-direction: column; } }
@media (prefers-reduced-motion: reduce) { .site-footer a { transition: none; } }
</style>
