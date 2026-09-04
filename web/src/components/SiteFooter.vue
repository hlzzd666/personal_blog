<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { fetchSiteSettings } from "../api/site-settings";
import OceanIcon from "./OceanIcon.vue";

const route = useRoute();
const currentYear = new Date().getFullYear();
const light = computed(() => route.path === "/about" || route.path === "/privacy");
const systemSurface = computed(() => route.path === "/icons");
const icpFilingUrl = "https://beian.miit.gov.cn/";
const policeFilingUrl = "https://www.beian.gov.cn/portal/index";
const icpFilingNumber = ref("");
const policeFilingNumber = ref("");

onMounted(async () => {
  try {
    const settings = await fetchSiteSettings();
    icpFilingNumber.value = settings.icp_filing_number?.trim() ?? "";
    policeFilingNumber.value = settings.police_filing_number?.trim() ?? "";
  } catch {
    // 备案信息为可选内容，读取失败时保持页脚原样。
  }
});
</script>

<template>
  <footer :class="['site-footer', { light, 'system-surface': systemSurface }]">
    <div>
      <strong>个人航海日志</strong>
      <span>© {{ currentYear }} 内容与代码持续更新</span>
    </div>
    <nav aria-label="页脚导航">
      <div v-if="icpFilingNumber || policeFilingNumber" class="filing-links" aria-label="备案信息">
        <a v-if="icpFilingNumber" :href="icpFilingUrl" target="_blank" rel="noreferrer noopener">
          {{ icpFilingNumber }}
        </a>
        <a v-if="policeFilingNumber" :href="policeFilingUrl" target="_blank" rel="noreferrer noopener">
          {{ policeFilingNumber }}
        </a>
      </div>
      <RouterLink to="/series">专题</RouterLink>
      <RouterLink to="/notes">动态</RouterLink>
      <RouterLink class="icon-atlas-link" to="/icons"><OceanIcon name="toc" :size="20" />图标航海图</RouterLink>
      <RouterLink to="/privacy">隐私说明</RouterLink>
      <a class="footer-external-link" href="/api/feed.xml" target="_blank" rel="alternate"><OceanIcon name="external" :size="16" />RSS</a>
    </nav>
  </footer>
</template>

<style scoped>
.site-footer { position: relative; z-index: 2; display: flex; justify-content: space-between; gap: 2rem; align-items: center; min-height: 8.5rem; padding: 2.4rem clamp(1rem, 5vw, 4rem); border-top: 1px solid rgba(244, 240, 223, 0.2); color: rgba(244, 240, 223, 0.84); background: #051923; font-family: "Noto Sans SC", sans-serif; }
.site-footer > div { display: grid; gap: 0.35rem; }
.filing-links { display: flex; flex-wrap: wrap; gap: 0.45rem 0.8rem; }
.filing-links a { font-size: 0.68rem; }
.site-footer strong { color: #f4f0df; font-family: var(--display-font); }
.site-footer span { color: rgba(244, 240, 223, 0.78); font-size: 0.76rem; }
.site-footer nav { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 0.7rem 1rem; }
.site-footer a { color: inherit; font-size: 0.78rem; text-decoration: none; transition: color 180ms ease; }
.icon-atlas-link { display: inline-flex; gap: 0.3rem; align-items: center; }
.footer-external-link { display: inline-flex; gap: 0.25rem; align-items: center; }
.site-footer a:hover, .site-footer a:focus-visible { color: #f4ca58; }
.site-footer.light { border-color: rgba(16, 42, 54, 0.16); color: rgba(23, 53, 65, 0.82); background: #edf2f5; }
.site-footer.light strong { color: #173541; }
.site-footer.light a:hover, .site-footer.light a:focus-visible { color: #c64f3a; }
@media (prefers-color-scheme: light) { .site-footer.system-surface { border-color: rgba(16, 42, 54, 0.1); color: rgba(23, 53, 65, 0.66); background: #dce8e9; } .site-footer.system-surface strong { color: #173541; } .site-footer.system-surface a:hover, .site-footer.system-surface a:focus-visible { color: #c64f3a; } }
@media (max-width: 680px) { .site-footer { align-items: flex-start; flex-direction: column; gap: 1.25rem; } .site-footer nav { justify-content: flex-start; } }
@media (prefers-reduced-motion: reduce) { .site-footer a { transition: none; } }
</style>
