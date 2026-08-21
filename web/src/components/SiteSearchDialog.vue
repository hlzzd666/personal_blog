<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";

import { fetchArticles, type Article } from "../api/articles";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{ close: [] }>();

const searchInput = ref<HTMLInputElement | null>(null);
const query = ref("");
const results = ref<Article[]>([]);
const total = ref(0);
const loading = ref(false);
const loadingMore = ref(false);
const errorText = ref("");
const loadMoreError = ref("");
const searchRevision = ref(0);
let searchTimer: number | undefined;
let requestVersion = 0;
const searchPageSize = 8;
const currentPage = ref(0);

const keyword = computed(() => query.value.trim());
const hasMoreResults = computed(() => results.value.length < total.value);

function close() {
  emit("close");
}

function formatDate(value: string | null) {
  if (!value) return "时间待定";
  return new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "short", day: "numeric" }).format(new Date(value));
}

async function searchArticles() {
  const currentKeyword = keyword.value;
  const currentRequest = ++requestVersion;

  if (!currentKeyword) {
    results.value = [];
    total.value = 0;
    currentPage.value = 0;
    errorText.value = "";
    loadMoreError.value = "";
    loading.value = false;
    return;
  }

  loading.value = true;
  errorText.value = "";
  loadMoreError.value = "";
  try {
    const response = await fetchArticles({
      search: currentKeyword,
      page: 1,
      page_size: searchPageSize,
    });
    if (currentRequest !== requestVersion) return;
    results.value = response.items;
    total.value = response.total;
    currentPage.value = response.page;
    searchRevision.value += 1;
  } catch {
    if (currentRequest !== requestVersion) return;
    results.value = [];
    total.value = 0;
    errorText.value = "文章索引暂时无法连接，请稍后再试。";
  } finally {
    if (currentRequest === requestVersion) loading.value = false;
  }
}

async function loadMoreResults() {
  if (!keyword.value || loading.value || loadingMore.value || !hasMoreResults.value) return;

  const currentKeyword = keyword.value;
  const currentRequest = requestVersion;
  loadingMore.value = true;
  loadMoreError.value = "";
  try {
    const response = await fetchArticles({
      search: currentKeyword,
      page: currentPage.value + 1,
      page_size: searchPageSize,
    });
    if (currentRequest !== requestVersion || currentKeyword !== keyword.value) return;

    const loadedIds = new Set(results.value.map((article) => article.id));
    results.value = [...results.value, ...response.items.filter((article) => !loadedIds.has(article.id))];
    total.value = response.total;
    currentPage.value = response.page;
  } catch {
    if (currentRequest !== requestVersion) return;
    loadMoreError.value = "更多搜索结果暂时无法读取。";
  } finally {
    if (currentRequest === requestVersion) loadingMore.value = false;
  }
}

function handleResultsScroll(event: Event) {
  const resultsContainer = event.currentTarget as HTMLElement;
  const distanceToBottom =
    resultsContainer.scrollHeight - resultsContainer.scrollTop - resultsContainer.clientHeight;
  if (distanceToBottom <= 72) {
    void loadMoreResults();
  }
}

function scheduleSearch() {
  window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(() => {
    void searchArticles();
  }, 250);
}

function handleKeydown(event: KeyboardEvent) {
  if (props.open && event.key === "Escape") close();
}

watch(query, scheduleSearch);
watch(
  () => props.open,
  async (isOpen) => {
    document.body.classList.toggle("site-search-open", isOpen);
    if (!isOpen) return;
    await nextTick();
    searchInput.value?.focus();
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  window.clearTimeout(searchTimer);
  document.body.classList.remove("site-search-open");
});
</script>

<template>
  <Teleport to="body">
    <Transition name="site-search">
      <section v-if="open" class="site-search-layer" role="dialog" aria-modal="true" aria-labelledby="site-search-title" @keydown="handleKeydown">
        <button class="site-search-backdrop" type="button" tabindex="-1" aria-label="关闭文章搜索" @click="close"></button>
        <div class="site-search-dialog">
          <header class="site-search-header">
            <div>
              <p>ARTICLE FINDER</p>
              <h2 id="site-search-title">搜索航海日志</h2>
            </div>
            <button class="site-search-close" type="button" aria-label="关闭搜索" @click="close">×</button>
          </header>

          <label class="site-search-field">
            <span class="site-search-field-icon" aria-hidden="true"></span>
            <input ref="searchInput" v-model="query" type="search" placeholder="搜索标题、摘要或文章内容" autocomplete="off" />
            <kbd>ESC</kbd>
          </label>

          <div class="site-search-status" aria-live="polite">
            <span v-if="loading">正在校准文章索引…</span>
            <span v-else-if="keyword && !errorText">定位到 {{ total }} 条相关记录</span>
            <span v-else-if="!keyword">输入关键词，开始检索文章。</span>
            <span v-else>{{ errorText }}</span>
          </div>

          <div v-if="results.length" class="site-search-results" @scroll="handleResultsScroll">
            <RouterLink
              v-for="(article, index) in results"
              :key="`${searchRevision}-${article.id}`"
              class="site-search-result"
              :style="{ '--result-delay': `${index * 48}ms` }"
              :to="{ path: `/articles/${article.slug}` }"
              @click="close"
            >
              <span class="site-search-result-marker">{{ String(index + 1).padStart(2, "0") }}</span>
              <span class="site-search-result-content">
                <span class="site-search-result-meta">{{ article.category }} <i></i> {{ formatDate(article.published_at ?? article.created_at) }}</span>
                <strong>{{ article.title }}</strong>
                <small>{{ article.summary || "打开文章查看完整航行记录。" }}</small>
              </span>
              <span class="site-search-result-arrow" aria-hidden="true">→</span>
            </RouterLink>
            <div v-if="loadingMore || loadMoreError || hasMoreResults" class="site-search-load-more">
              <span v-if="loadingMore">正在继续定位记录…</span>
              <button v-else-if="loadMoreError" type="button" @click="loadMoreResults">
                {{ loadMoreError }} 点击重试
              </button>
              <span v-else>继续向下加载更多记录</span>
            </div>
          </div>

          <div v-else-if="keyword && !loading && !errorText" class="site-search-empty">
            没有找到相关航线，换一个关键词试试。
          </div>
        </div>
      </section>
    </Transition>
  </Teleport>
</template>

<style scoped lang="scss">
:global(body.site-search-open) {
  overflow: hidden;
}

.site-search-layer {
  position: fixed;
  z-index: 100;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 1.5rem;
}

.site-search-backdrop {
  position: absolute;
  inset: 0;
  border: 0;
  background: rgba(4, 20, 29, 0.48);
  backdrop-filter: blur(0.35rem);
  cursor: default;
  will-change: opacity, backdrop-filter;
}

.site-search-dialog {
  position: relative;
  isolation: isolate;
  width: min(46rem, 100%);
  max-height: min(44rem, calc(100vh - 3rem));
  overflow: hidden;
  border: 1px solid rgba(239, 231, 206, 0.26);
  border-radius: 8px;
  color: #f7f2df;
  background:
    linear-gradient(116deg, rgba(224, 132, 97, 0.13), transparent 42%),
    repeating-linear-gradient(90deg, transparent 0 3.5rem, rgba(135, 210, 199, 0.04) 3.55rem 3.61rem),
    #09222e;
  box-shadow: 0 1.8rem 6rem rgba(0, 0, 0, 0.46);
}

.site-search-dialog::before {
  content: "";
  position: absolute;
  z-index: 2;
  top: 0;
  right: 8%;
  left: 8%;
  height: 1px;
  background: linear-gradient(90deg, transparent, #ffd36f, transparent);
  opacity: 0.75;
}

.site-search-dialog::after {
  content: "";
  position: absolute;
  z-index: 0;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(
    104deg,
    transparent 34%,
    rgba(255, 211, 111, 0.05) 45%,
    rgba(135, 210, 199, 0.16) 50%,
    rgba(255, 211, 111, 0.05) 55%,
    transparent 66%
  );
  transform: translateX(-120%) skewX(-10deg);
}

.site-search-header,
.site-search-field,
.site-search-status,
.site-search-results,
.site-search-empty {
  position: relative;
  z-index: 1;
}

.site-search-header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.75rem 1.9rem 1.2rem;
}

.site-search-header p {
  margin: 0 0 0.4rem;
  color: #ffd36f;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.17em;
}

.site-search-header h2 {
  margin: 0;
  font-size: 1.85rem;
  line-height: 1.1;
}

.site-search-close {
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  padding: 0 0 0.1rem;
  border: 1px solid rgba(247, 242, 223, 0.16);
  border-radius: 50%;
  color: rgba(247, 242, 223, 0.72);
  background: transparent;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 1.45rem;
  line-height: 1;
  cursor: pointer;
  transition: color 0.22s ease, border-color 0.22s ease, transform 0.22s ease;

  &:hover,
  &:focus-visible {
    border-color: #ffd36f;
    color: #ffd36f;
    transform: rotate(90deg);
  }
}

.site-search-field {
  position: relative;
  display: flex;
  align-items: center;
  margin: 0 1.9rem;
  border-bottom: 2px solid #87d2c7;
  background: rgba(3, 14, 22, 0.24);
  box-shadow: inset 0 -1px 0 rgba(255, 211, 111, 0.12);

  &:focus-within {
    border-color: #ffd36f;
    box-shadow: inset 0 -1px 0 #ffd36f, 0 0 1.5rem rgba(255, 211, 111, 0.12);
  }

  input {
    width: 100%;
    min-width: 0;
    height: 3.55rem;
    padding: 0.7rem 4rem 0.7rem 3rem;
    border: 0;
    outline: 0;
    color: #f7f2df;
    background: transparent;
    font-family: "Noto Sans SC", sans-serif;
    font-size: 1rem;

    &::placeholder {
      color: rgba(247, 242, 223, 0.4);
    }

    &::-webkit-search-cancel-button {
      appearance: none;
    }
  }

  kbd {
    position: absolute;
    right: 0.85rem;
    padding: 0.16rem 0.35rem;
    border: 1px solid rgba(247, 242, 223, 0.18);
    color: rgba(247, 242, 223, 0.42);
    font-family: "Noto Sans SC", sans-serif;
    font-size: 0.58rem;
  }
}

.site-search-field-icon {
  position: absolute;
  z-index: 1;
  left: 1rem;
  width: 0.86rem;
  height: 0.86rem;
  border: 2px solid #87d2c7;
  border-radius: 50%;

  &::after {
    content: "";
    position: absolute;
    right: -0.38rem;
    bottom: -0.24rem;
    width: 0.43rem;
    height: 2px;
    background: #87d2c7;
    transform: rotate(45deg);
    transform-origin: left center;
  }
}

.site-search-status {
  min-height: 3.25rem;
  padding: 0.95rem 1.9rem 0;
  color: rgba(247, 242, 223, 0.56);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.76rem;
}

.site-search-results {
  display: grid;
  max-height: min(29.5rem, calc(100vh - 14rem));
  overflow-y: auto;
  overscroll-behavior: contain;
  border-top: 1px solid rgba(247, 242, 223, 0.14);
  scrollbar-width: thin;
  scrollbar-color: rgba(135, 210, 199, 0.48) transparent;

  &::-webkit-scrollbar {
    width: 0.38rem;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    border-radius: 99px;
    background: rgba(135, 210, 199, 0.48);
  }
}

.site-search-result {
  display: grid;
  grid-template-columns: 2.35rem minmax(0, 1fr) auto;
  gap: 0.95rem;
  align-items: center;
  padding: 1.05rem 1.9rem;
  border-bottom: 1px solid rgba(247, 242, 223, 0.11);
  color: inherit;
  text-decoration: none;
  animation: result-arrive 0.42s calc(var(--result-delay) + 40ms) cubic-bezier(0.2, 0.76, 0.26, 1) both;
  transition: background-color 0.25s ease, padding-left 0.25s ease;

  &:hover,
  &:focus-visible {
    padding-left: 2.25rem;
    background: linear-gradient(90deg, rgba(255, 211, 111, 0.12), transparent 76%);
  }
}

.site-search-result-marker {
  color: #ffd36f;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.68rem;
  font-weight: 700;
}

.site-search-result-content {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
}

.site-search-result-meta {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  color: #87d2c7;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.67rem;

  i {
    width: 0.22rem;
    height: 0.22rem;
    border-radius: 50%;
    background: rgba(247, 242, 223, 0.35);
  }
}

.site-search-result strong {
  overflow: hidden;
  color: #f7f2df;
  font-size: 1.08rem;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.site-search-result small {
  overflow: hidden;
  color: rgba(247, 242, 223, 0.58);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.76rem;
  line-height: 1.55;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.site-search-result-arrow {
  color: rgba(247, 242, 223, 0.42);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 1.1rem;
  transition: color 0.2s ease, transform 0.2s ease;
}

.site-search-result:hover .site-search-result-arrow,
.site-search-result:focus-visible .site-search-result-arrow {
  color: #ffd36f;
  transform: translateX(0.24rem);
}

.site-search-load-more {
  display: grid;
  min-height: 3.75rem;
  place-items: center;
  border-bottom: 1px solid rgba(247, 242, 223, 0.11);
  color: rgba(135, 210, 199, 0.66);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.7rem;
  letter-spacing: 0.08em;
}

.site-search-load-more button {
  padding: 0.35rem 0.55rem;
  border: 0;
  color: #ffd36f;
  background: transparent;
  font: inherit;
  cursor: pointer;
}

.site-search-load-more button:hover,
.site-search-load-more button:focus-visible {
  color: #fff0a7;
  text-decoration: underline;
}

.site-search-empty {
  min-height: 10rem;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  border-top: 1px solid rgba(247, 242, 223, 0.14);
  color: rgba(247, 242, 223, 0.55);
  font-family: "Noto Sans SC", sans-serif;
  font-size: 0.84rem;
  text-align: center;
}

.site-search-enter-active,
.site-search-leave-active {
  transition: opacity 0.66s cubic-bezier(0.22, 0.72, 0.25, 1);

  .site-search-dialog {
    transition: opacity 0.58s cubic-bezier(0.2, 0.76, 0.26, 1), transform 0.58s cubic-bezier(0.2, 0.76, 0.26, 1);
  }
}

.site-search-enter-active {
  .site-search-backdrop {
    animation: search-backdrop-in 0.9s cubic-bezier(0.22, 0.72, 0.25, 1) both;
  }

  .site-search-dialog::before {
    animation: search-horizon-lock 0.78s 0.1s cubic-bezier(0.2, 0.76, 0.26, 1) both;
  }

  .site-search-dialog::after {
    animation: search-scan-pass 1.1s 0.16s cubic-bezier(0.2, 0.76, 0.26, 1) both;
  }

  .site-search-header {
    animation: search-header-lock 0.48s 0.12s cubic-bezier(0.2, 0.76, 0.26, 1) both;
  }

  .site-search-close {
    animation: search-close-lock 0.44s 0.25s cubic-bezier(0.2, 0.76, 0.26, 1) both;
  }

  .site-search-field {
    animation: search-field-lock 0.5s 0.22s cubic-bezier(0.2, 0.76, 0.26, 1) both;
  }

  .site-search-status {
    animation: search-status-lock 0.42s 0.31s ease both;
  }

  .site-search-results,
  .site-search-empty {
    animation: search-results-unfold 0.54s 0.38s cubic-bezier(0.2, 0.76, 0.26, 1) both;
  }
}

.site-search-leave-active {
  .site-search-backdrop {
    animation: search-backdrop-out 0.78s cubic-bezier(0.4, 0, 0.2, 1) both;
  }

  .site-search-dialog {
    transition-duration: 0.72s;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  }
}

.site-search-enter-from,
.site-search-leave-to {
  opacity: 0;

  .site-search-dialog {
    opacity: 0;
    transform: translateY(1.5rem) scale(0.97);
  }
}

@keyframes result-arrive {
  from {
    opacity: 0;
    transform: translateX(0.8rem);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes search-backdrop-in {
  from {
    opacity: 0;
    backdrop-filter: blur(0);
  }
  55% {
    opacity: 0.72;
    backdrop-filter: blur(0.18rem);
  }
  to {
    opacity: 1;
    backdrop-filter: blur(0.35rem);
  }
}

@keyframes search-backdrop-out {
  from {
    opacity: 1;
    backdrop-filter: blur(0.35rem);
  }
  45% {
    opacity: 0.62;
    backdrop-filter: blur(0.2rem);
  }
  to {
    opacity: 0;
    backdrop-filter: blur(0);
  }
}

@keyframes search-horizon-lock {
  from {
    opacity: 0;
    transform: scaleX(0.12);
  }
  to {
    opacity: 0.75;
    transform: scaleX(1);
  }
}

@keyframes search-scan-pass {
  0% {
    opacity: 0;
    transform: translateX(-120%) skewX(-10deg);
  }
  18% {
    opacity: 0.95;
  }
  82%,
  100% {
    opacity: 0;
    transform: translateX(120%) skewX(-10deg);
  }
}

@keyframes search-header-lock {
  from {
    opacity: 0;
    transform: translateY(1rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes search-close-lock {
  from {
    opacity: 0;
    transform: rotate(-100deg) scale(0.6);
  }
  to {
    opacity: 1;
    transform: rotate(0) scale(1);
  }
}

@keyframes search-field-lock {
  from {
    opacity: 0;
    transform: translateY(0.5rem) scaleX(0.78);
  }
  to {
    opacity: 1;
    transform: translateY(0) scaleX(1);
  }
}

@keyframes search-status-lock {
  from {
    opacity: 0;
    clip-path: inset(0 100% 0 0);
  }
  to {
    opacity: 1;
    clip-path: inset(0);
  }
}

@keyframes search-results-unfold {
  from {
    opacity: 0;
    transform: translateY(0.8rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 600px) {
  .site-search-layer {
    align-items: end;
    padding: 0;
  }

  .site-search-dialog {
    max-height: min(42rem, calc(100vh - 1rem));
    border-right: 0;
    border-bottom: 0;
    border-left: 0;
    border-radius: 8px 8px 0 0;
  }

  .site-search-header,
  .site-search-result {
    padding-right: 1.15rem;
    padding-left: 1.15rem;
  }

  .site-search-field {
    margin-inline: 1.15rem;
  }

  .site-search-status {
    padding-inline: 1.15rem;
  }

  .site-search-result {
    grid-template-columns: 1.8rem minmax(0, 1fr) auto;
    gap: 0.65rem;

    &:hover,
    &:focus-visible {
      padding-left: 1.4rem;
    }
  }

  .site-search-results {
    max-height: calc(100vh - 13rem);
  }
}

@media (prefers-reduced-motion: reduce) {
  .site-search-enter-active,
  .site-search-leave-active,
  .site-search-enter-active .site-search-dialog,
  .site-search-leave-active .site-search-dialog,
  .site-search-result,
  .site-search-close,
  .site-search-result-arrow,
  .site-search-result,
  .site-search-backdrop,
  .site-search-dialog::before,
  .site-search-dialog::after,
  .site-search-header,
  .site-search-field,
  .site-search-status,
  .site-search-results,
  .site-search-empty {
    animation: none;
    transition: none;
  }
}
</style>
