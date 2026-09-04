<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { onBeforeRouteLeave, useRoute } from "vue-router";

import { ApiError } from "../api/http";
import { fetchSeriesDetail, type SeriesDetail } from "../api/content";
import OceanAtmosphere from "../components/OceanAtmosphere.vue";
import OceanIcon from "../components/OceanIcon.vue";
import { readArticleReturnContext, saveArticleReturnContext } from "../composables/useArticleReturnContext";
import { useSeo } from "../composables/useSeo";
import { useViewportReveal } from "../composables/useViewportReveal";

const route = useRoute();
const series = ref<SeriesDetail | null>(null);
const loading = ref(true);
const notFound = ref(false);
const errorText = ref("");
const pageRoot = ref<HTMLElement | null>(null);
const { applySeo } = useSeo();
const { observe } = useViewportReveal();
const progressText = computed(() => `${series.value?.articles.length ?? 0} 个航线节点`);

function formatDate(value: string | null) {
  return new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "short", day: "numeric" }).format(
    new Date(value ?? Date.now()),
  );
}

function rememberSeriesArticleEntry(articleSlug: string) {
  saveArticleReturnContext({
    source: "series",
    path: route.fullPath,
    scrollY: window.scrollY,
    articleSlug,
  });
}

async function restoreSeriesReturnPosition() {
  const returnContext = readArticleReturnContext();
  if (returnContext?.source !== "series" || returnContext.path !== route.fullPath) return;

  await nextTick();
  window.requestAnimationFrame(() => {
    window.scrollTo({ top: returnContext.scrollY, left: 0, behavior: "auto" });
  });
}

async function loadSeries() {
  loading.value = true;
  notFound.value = false;
  errorText.value = "";
  try {
    series.value = await fetchSeriesDetail(String(route.params.slug));
    applySeo({
      title: series.value.title,
      description: series.value.description || `专题《${series.value.title}》的完整文章航线。`,
      canonicalPath: `/series/${series.value.slug}`,
      image: series.value.cover_image_url,
      jsonLd: {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        name: series.value.title,
        description: series.value.description,
      },
    });
  } catch (error) {
    series.value = null;
    notFound.value = error instanceof ApiError && error.status === 404;
    errorText.value = notFound.value ? "这条专题航线不存在。" : "专题航线暂时无法读取。";
  } finally {
    loading.value = false;
    void observe(pageRoot.value);
    void restoreSeriesReturnPosition();
  }
}

watch(() => route.params.slug, loadSeries, { immediate: true });

onBeforeRouteLeave((to) => {
  if (!to.path.startsWith("/articles/") || typeof to.params.slug !== "string") return;
  rememberSeriesArticleEntry(to.params.slug);
});
</script>

<template>
  <main ref="pageRoot" class="content-hub series-detail-hub">
    <OceanAtmosphere variant="series" />
    <template v-if="series">
      <header
        class="series-detail-hero"
        :style="series.cover_image_url ? { '--series-cover': `url(${series.cover_image_url})` } : undefined"
      >
        <RouterLink to="/series"><OceanIcon name="previous" :size="18" />返回专题</RouterLink>
        <p>SERIES / {{ series.slug }}</p>
        <h1>{{ series.title }}</h1>
        <span>{{ series.description || "沿着顺序阅读这组文章。" }}</span>
        <strong>{{ progressText }}</strong>
      </header>
      <section class="series-route" aria-label="专题文章">
        <RouterLink
          v-for="(article, index) in series.articles"
          :key="article.id"
          class="series-route-stop reveal-item"
          data-reveal
          :to="`/articles/${article.slug}`"
          @click="rememberSeriesArticleEntry(article.slug)"
        >
          <span class="route-node">{{ String(index + 1).padStart(2, "0") }}</span>
          <div>
            <p>{{ formatDate(article.published_at ?? article.created_at) }} · {{ article.category }}</p>
            <h2>{{ article.title }}</h2>
            <span>{{ article.summary || "打开文章查看完整记录。" }}</span>
          </div>
          <OceanIcon name="next" :size="20" />
        </RouterLink>
        <div v-if="!series.articles.length" class="content-state">这条航线还没有文章。</div>
      </section>
    </template>
    <section v-else-if="loading" class="content-state">正在读取专题航线…</section>
    <section v-else class="content-state error">
      <OceanIcon name="warning" :size="28" />
      <p>{{ errorText }}</p>
      <RouterLink :to="notFound ? '/series' : route.fullPath">{{ notFound ? "返回专题列表" : "重新读取" }}</RouterLink>
    </section>
  </main>
</template>
