<script setup lang="ts">
import DOMPurify from "dompurify";
import { marked } from "marked";
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { fetchArticle, likeArticle, type Article } from "../api/articles";

const route = useRoute();
const article = ref<Article | null>(null);
const loading = ref(true);
const errorText = ref("");
const liking = ref(false);

const renderedContent = computed(() => {
  if (!article.value) return "";
  return DOMPurify.sanitize(marked.parse(article.value.content_markdown) as string);
});

function formatDate(value: string | null) {
  if (!value) return "时间待定";
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "long", timeStyle: "short" }).format(new Date(value));
}

async function loadArticle() {
  loading.value = true;
  try {
    article.value = await fetchArticle(String(route.params.slug));
  } catch {
    errorText.value = "这段航行记录不存在，或已经离开当前航线。";
  } finally {
    loading.value = false;
  }
}

async function handleLike() {
  if (!article.value || liking.value) return;
  liking.value = true;
  try {
    const result = await likeArticle(article.value.slug);
    article.value.likes = result.likes;
  } finally {
    liking.value = false;
  }
}

onMounted(() => {
  void loadArticle();
});
</script>

<template>
  <div class="article-detail-page">
    <header v-if="article" class="article-detail-header">
      <a class="article-back-link" href="/articles">← 返回文章归档</a>
      <p class="article-kicker">{{ article.category }} / {{ formatDate(article.published_at) }}</p>
      <h1>{{ article.title }}</h1>
      <p class="article-summary">{{ article.summary }}</p>
      <div class="article-detail-meta"><span>作者：{{ article.author }}</span><span>阅读：{{ article.views }}</span><span>更新：{{ formatDate(article.updated_at) }}</span></div>
    </header>

    <main v-if="article" class="article-detail-body">
      <img v-if="article.cover_image_url" class="article-detail-cover" :src="article.cover_image_url" :alt="article.title" />
      <!-- 内容已由 DOMPurify 清洗后再插入，保留 Markdown 的排版能力。 -->
      <!-- eslint-disable-next-line vue/no-v-html -->
      <article class="markdown-body" v-html="renderedContent"></article>
      <footer class="article-detail-footer">
        <div class="article-detail-tags"><span v-for="tag in article.tags" :key="tag">#{{ tag }}</span></div>
        <button class="article-like-button" :disabled="liking" @click="handleLike">喜欢这篇记录 · {{ article.likes }}</button>
      </footer>
      <p v-if="article.is_repost && article.source_url" class="article-source">本文转载自 <a :href="article.source_url" target="_blank" rel="noreferrer">原始来源</a>。</p>
    </main>

    <div v-else-if="loading" class="article-detail-state">正在读取航行记录……</div>
    <div v-else class="article-detail-state">{{ errorText }}</div>
  </div>
</template>

<style scoped>
.article-detail-page {
  min-height: 100vh;
  padding: 4rem 1.5rem 6rem;
  color: #182b36;
  background: #f4f0e6;
}

.article-detail-header,
.article-detail-body {
  width: min(840px, 100%);
  margin: 0 auto;
}

.article-back-link {
  color: #c56b42;
  text-decoration: none;
}

.article-kicker {
  margin: 4rem 0 1rem;
  color: #c56b42;
  font-size: 0.8rem;
  letter-spacing: 0.12em;
}

.article-detail-header h1 {
  margin: 0;
  font-size: clamp(2.7rem, 7vw, 5.6rem);
  line-height: 1.05;
}

.article-summary {
  max-width: 650px;
  margin: 1.5rem 0 0;
  color: #5b6d72;
  font-size: 1.1rem;
  line-height: 1.8;
}

.article-detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1.5rem;
  color: #829093;
  font-size: 0.8rem;
}

.article-detail-body {
  padding-top: 3rem;
}

.article-detail-cover {
  width: 100%;
  max-height: 420px;
  margin-bottom: 3rem;
  border-radius: 10px;
  object-fit: cover;
}

.markdown-body {
  font-family: "Noto Sans SC", sans-serif;
  font-size: 1.05rem;
  line-height: 2;
}

.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin-top: 2.7rem;
  line-height: 1.3;
}

.markdown-body :deep(pre) {
  overflow-x: auto;
  padding: 1.2rem;
  border-radius: 8px;
  color: #e9f5f0;
  background: #142d38;
}

.markdown-body :deep(code) {
  padding: 0.12rem 0.3rem;
  border-radius: 3px;
  background: rgba(197, 107, 66, 0.12);
}

.markdown-body :deep(pre code) {
  padding: 0;
  background: transparent;
}

.markdown-body :deep(blockquote) {
  margin-inline: 0;
  padding: 0.5rem 1rem;
  border-left: 3px solid #c56b42;
  color: #657b7f;
}

.article-detail-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 4rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(24, 43, 54, 0.16);
}

.article-detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  color: #42939a;
}

.article-like-button {
  padding: 0.7rem 1rem;
  border: 1px solid #c56b42;
  border-radius: 999px;
  color: #c56b42;
  background: transparent;
  cursor: pointer;
}

.article-like-button:hover {
  color: #fff9ef;
  background: #c56b42;
}

.article-source {
  margin-top: 1rem;
  color: #829093;
  font-size: 0.85rem;
}

.article-source a {
  color: #c56b42;
}

.article-detail-state {
  display: grid;
  min-height: 70vh;
  place-items: center;
  color: #5b6d72;
}

@media (max-width: 600px) {
  .article-detail-page {
    padding-inline: 1rem;
  }

  .article-detail-footer {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
