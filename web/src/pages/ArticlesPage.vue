<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { fetchArticles, type Article } from "../api/articles";

const route = useRoute();
const articles = ref<Article[]>([]);
const loading = ref(true);
const errorText = ref("");
const activeCategory = ref("");
const activeTag = ref("");

const categories = computed(() => [...new Set(articles.value.map((article) => article.category))]);
const tags = computed(() => [...new Set(articles.value.flatMap((article) => article.tags))].slice(0, 12));
const archiveMode = computed(() => !route.query.view || route.query.view === "archive");
function archiveDate(article: Article) {
  return article.published_at ?? article.created_at;
}
const visibleArticles = computed(() => {
  const filtered = articles.value.filter(
    (article) => (!activeCategory.value || article.category === activeCategory.value) && (!activeTag.value || article.tags.includes(activeTag.value)),
  );
  if (!archiveMode.value) return filtered;
  return [...filtered].sort((left, right) => {
    const publishedAtOrder = Date.parse(archiveDate(right)) - Date.parse(archiveDate(left));
    return publishedAtOrder || right.id - left.id;
  });
});
const pageTitle = computed(() => {
  if (route.query.view === "tags") return "标签航线";
  if (route.query.view === "categories") return "分类航线";
  return "文章归档";
});

function formatDate(value: string | null) {
  if (!value) return "时间待定";
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium" }).format(new Date(value));
}

async function loadArticles() {
  loading.value = true;
  try {
    const result = await fetchArticles({ page: 1, page_size: 50 });
    articles.value = result.items;
  } catch {
    errorText.value = "文章航线暂时无法读取，请稍后再试。";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadArticles();
});
</script>

<template>
  <div class="article-page">
    <header class="article-page-header">
      <a class="article-back-link" href="/">← 返回首页</a>
      <p class="article-kicker">LOGBOOK / {{ String(route.query.view ?? "ARCHIVE").toUpperCase() }}</p>
      <h1>{{ pageTitle }}</h1>
      <p>每一篇文章都是一次靠岸。归档沿文章发表时间展开成一条航线，也可以从标签和分类切入。</p>
    </header>

    <main class="article-page-body">
      <aside class="article-filter-rail">
        <p class="article-filter-title">航线索引</p>
        <button :class="{ active: !activeCategory && !activeTag }" @click="activeCategory = ''; activeTag = ''">全部记录</button>
        <p class="article-filter-label">分类</p>
        <button v-for="category in categories" :key="category" :class="{ active: activeCategory === category }" @click="activeCategory = category; activeTag = ''">{{ category }}</button>
        <p class="article-filter-label">标签</p>
        <button v-for="tag in tags" :key="tag" :class="{ active: activeTag === tag }" @click="activeTag = tag; activeCategory = ''"># {{ tag }}</button>
      </aside>

      <section :class="['article-results', { 'archive-mode': archiveMode }]" aria-live="polite">
        <div v-if="loading" class="article-empty-state">正在展开海图……</div>
        <div v-else-if="errorText" class="article-empty-state">{{ errorText }}</div>
        <div v-else-if="!articles.length" class="article-empty-state">还没有文章，下一次靠岸会从这里开始。</div>
        <div v-else-if="!visibleArticles.length" class="article-empty-state">这条航线上还没有匹配的记录。</div>
        <div v-else class="article-list">
          <article
            v-for="article in visibleArticles"
            :key="article.id"
            class="article-result-card"
          >
            <div class="article-result-marker">
              <span>{{ archiveMode ? formatDate(archiveDate(article)) : String(article.id).padStart(2, "0") }}</span>
            </div>
            <div class="article-result-content">
              <div class="article-result-meta"><span>{{ formatDate(archiveDate(article)) }}</span><span>{{ article.category }}</span></div>
              <h2><a :href="`/articles/${article.slug}`">{{ article.title }}</a></h2>
              <p>{{ article.summary || "这段航行还没有摘要，打开文章查看完整记录。" }}</p>
              <div class="article-result-footer">
                <span>{{ article.views }} 次阅读 · {{ article.likes }} 个喜欢</span>
                <span class="article-tags"><b v-for="tag in article.tags" :key="tag">#{{ tag }}</b></span>
              </div>
            </div>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.article-page {
  min-height: 100vh;
  color: #fef9ef;
  background:
    linear-gradient(125deg, rgba(7, 19, 31, 0.97), rgba(13, 47, 62, 0.95)),
    #07131f;
}

.article-page-header,
.article-page-body {
  width: min(1120px, calc(100% - 3rem));
  margin: 0 auto;
}

.article-page-header {
  padding: 5rem 0 4rem;
  border-bottom: 1px solid rgba(255, 249, 239, 0.16);
}

.article-back-link {
  color: #ffd36f;
  text-decoration: none;
}

.article-kicker,
.article-filter-title,
.article-filter-label {
  color: #ffd36f;
  font-size: 0.74rem;
  letter-spacing: 0.14em;
}

.article-kicker {
  margin: 4rem 0 1rem;
}

.article-page-header h1 {
  max-width: 46rem;
  margin: 0;
  font-size: clamp(2.7rem, 7vw, 5.8rem);
  line-height: 1.05;
}

.article-page-header > p:last-child {
  max-width: 34rem;
  margin: 1.4rem 0 0;
  color: rgba(255, 249, 239, 0.7);
  line-height: 1.8;
}

.article-page-body {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr);
  gap: 4rem;
  padding: 3rem 0 6rem;
}

.article-filter-rail {
  align-self: start;
  position: sticky;
  top: 2rem;
}

.article-filter-title {
  margin: 0 0 1.4rem;
}

.article-filter-label {
  margin: 2rem 0 0.6rem;
  color: rgba(255, 249, 239, 0.42);
  letter-spacing: 0.08em;
}

.article-filter-rail button {
  display: block;
  width: 100%;
  padding: 0.45rem 0;
  border: 0;
  background: none;
  color: rgba(255, 249, 239, 0.66);
  text-align: left;
  cursor: pointer;
}

.article-filter-rail button:hover,
.article-filter-rail button.active {
  color: #ffd36f;
}

.article-list {
  display: grid;
  gap: 1rem;
}

.archive-mode .article-list {
  position: relative;
  gap: 0;
  padding-left: 1.2rem;
}

.archive-mode .article-list::before {
  content: "";
  position: absolute;
  top: 1rem;
  bottom: 1rem;
  left: 0.18rem;
  width: 1px;
  background: linear-gradient(#ffd36f, rgba(255, 249, 239, 0.12));
}

.article-result-card {
  position: relative;
  display: grid;
  grid-template-columns: 5.6rem 1fr;
  gap: 1.2rem;
  padding: 1.5rem 0;
  border-bottom: 1px solid rgba(255, 249, 239, 0.14);
}

.archive-mode .article-result-card::before {
  content: "";
  position: absolute;
  top: 2rem;
  left: -1.27rem;
  width: 0.48rem;
  height: 0.48rem;
  border: 2px solid #ffd36f;
  border-radius: 50%;
  background: #102f3e;
  box-shadow: 0 0 0 0.3rem rgba(255, 211, 111, 0.08);
}

.article-result-marker {
  color: rgba(255, 211, 111, 0.72);
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.68rem;
  line-height: 1.35;
}

.article-result-meta,
.article-result-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  color: rgba(255, 249, 239, 0.5);
  font-size: 0.76rem;
}

.article-result-content h2 {
  margin: 0.55rem 0 0.6rem;
  font-size: clamp(1.4rem, 3vw, 2.1rem);
  line-height: 1.25;
}

.article-result-content h2 a {
  color: #fff9ef;
  text-decoration: none;
}

.article-result-content h2 a:hover {
  color: #ffd36f;
}

.article-result-content > p {
  margin: 0;
  color: rgba(255, 249, 239, 0.7);
  line-height: 1.75;
}

.article-result-footer {
  justify-content: space-between;
  margin-top: 1.1rem;
}

.article-tags {
  display: flex;
  gap: 0.55rem;
  color: #8fd5d0;
}

.article-empty-state {
  padding: 5rem 0;
  color: rgba(255, 249, 239, 0.58);
}

@media (max-width: 720px) {
  .article-page-header,
  .article-page-body {
    width: min(100% - 2rem, 40rem);
  }

  .article-page-header {
    padding-top: 3rem;
  }

  .article-kicker {
    margin-top: 3rem;
  }

  .article-page-body {
    grid-template-columns: 1fr;
    gap: 1.5rem;
    padding-top: 2rem;
  }

  .article-filter-rail {
    position: static;
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem 1rem;
  }

  .article-filter-title,
  .article-filter-label {
    width: 100%;
    margin: 0.4rem 0;
  }

  .article-filter-rail button {
    width: auto;
  }
}
</style>
