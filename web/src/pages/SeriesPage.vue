<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { fetchSeries, type Series } from "../api/content";
import OceanAtmosphere from "../components/OceanAtmosphere.vue";
import { useSeo } from "../composables/useSeo";
import { useViewportReveal } from "../composables/useViewportReveal";

const items = ref<Series[]>([]);
const displayItems = computed(() =>
  [...items.value].sort((a, b) => a.sort_order - b.sort_order || a.id - b.id),
);
const loading = ref(true);
const errorText = ref("");
const pageRoot = ref<HTMLElement | null>(null);
const { applySeo } = useSeo();
const { observe } = useViewportReveal();

onMounted(async () => {
  applySeo({
    title: "专题航线",
    description: "按专题顺序阅读完整的文章航线。",
    canonicalPath: "/series",
  });
  try {
    items.value = (await fetchSeries()).items;
  } catch {
    errorText.value = "专题航线暂时无法读取，请稍后重试。";
  } finally {
    loading.value = false;
    void observe(pageRoot.value);
  }
});
</script>

<template>
  <main ref="pageRoot" class="content-hub series-hub">
    <OceanAtmosphere variant="series" />
    <header class="content-hub-hero hub-masthead">
      <div class="hub-hero-copy">
        <RouterLink class="hub-back" to="/">← 返回首页</RouterLink>
        <h1>专题航线</h1>
        <p>把分散的文章连成可连续阅读的航段。</p>
        <div class="hub-hero-meta"><span>CURATED ROUTES</span><strong>{{ items.length }} 条航线</strong></div>
      </div>
      <div class="hub-hero-aside">
        <p>按主题收束文章，让一次阅读有起点，也有下一站。</p>
        <div class="hub-instrument" aria-hidden="true">
          <span class="hub-instrument-label">ROUTE INDEX</span>
          <div class="hub-sweep"><i></i><i></i><i></i><i></i><i></i></div>
          <span class="hub-instrument-note">FOLLOW THE CURRENT</span>
        </div>
      </div>
    </header>

    <div class="hub-section-lead"><span>已标记航段</span><span>按阅读顺序排列</span></div>
    <section v-if="items.length" class="series-grid" aria-label="专题列表">
      <RouterLink
        v-for="(series, index) in displayItems"
        :key="series.id"
        class="series-card reveal-item"
        data-reveal
        :to="`/series/${series.slug}`"
        :style="series.cover_image_url ? { '--series-cover': `url(${series.cover_image_url})` } : undefined"
      >
        <div class="series-card-cover" aria-hidden="true"></div>
        <div class="series-index"><span>{{ String(index + 1).padStart(2, "0") }}</span><i></i></div>
        <div>
          <p>{{ series.article_count }} 篇文章</p>
          <h2>{{ series.title }}</h2>
          <span>{{ series.description || "这条航线正在等待补充说明。" }}</span>
        </div>
        <b aria-hidden="true">进入航线 →</b>
      </RouterLink>
    </section>
    <section v-else-if="loading" class="content-state" aria-live="polite">正在校准专题航线…</section>
    <section v-else-if="errorText" class="content-state error" role="alert">{{ errorText }}</section>
    <section v-else class="content-state">专题正在整理中，稍后回来看看。</section>
  </main>
</template>
