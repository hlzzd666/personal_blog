<script setup lang="ts">
import DOMPurify from "dompurify";
import { marked } from "marked";
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { fetchNote, type Note } from "../api/content";
import { ApiError } from "../api/http";
import OceanAtmosphere from "../components/OceanAtmosphere.vue";
import { useSeo } from "../composables/useSeo";

const route = useRoute();
const note = ref<Note | null>(null);
const loading = ref(true);
const notFound = ref(false);
const errorText = ref("");
const copyState = ref<"idle" | "copied" | "error">("idle");
const { applySeo } = useSeo();
let copyTimer: number | undefined;

const renderedContent = computed(() =>
  note.value ? DOMPurify.sanitize(marked.parse(note.value.content_markdown) as string) : "",
);

function plainText(markdown: string) {
  return markdown.replace(/```[\s\S]*?```/g, " ").replace(/[#>*_`[\]()!-]/g, " ").replace(/\s+/g, " ").trim();
}

function formatDate(value: string | null) {
  return new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "long", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false }).format(
    new Date(value ?? Date.now()),
  );
}

async function copyLink() {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(window.location.href);
    } else {
      throw new Error("clipboard unavailable");
    }
    copyState.value = "copied";
  } catch {
    const input = document.createElement("textarea");
    input.value = window.location.href;
    input.style.position = "fixed";
    input.style.opacity = "0";
    document.body.appendChild(input);
    input.select();
    copyState.value = document.execCommand("copy") ? "copied" : "error";
    input.remove();
  }
  window.clearTimeout(copyTimer);
  copyTimer = window.setTimeout(() => { copyState.value = "idle"; }, 1600);
}

async function loadNote() {
  loading.value = true;
  notFound.value = false;
  errorText.value = "";
  try {
    note.value = await fetchNote(String(route.params.slug));
    const description = plainText(note.value.content_markdown).slice(0, 160);
    applySeo({
      title: description.slice(0, 36) || "短动态",
      description,
      canonicalPath: `/notes/${note.value.slug}`,
      type: "article",
      jsonLd: {
        "@context": "https://schema.org",
        "@type": "SocialMediaPosting",
        articleBody: description,
        datePublished: note.value.published_at ?? note.value.created_at,
      },
    });
  } catch (error) {
    note.value = null;
    notFound.value = error instanceof ApiError && error.status === 404;
    errorText.value = notFound.value ? "这条动态信号不存在。" : "动态信号暂时无法读取。";
  } finally {
    loading.value = false;
  }
}

watch(() => route.params.slug, loadNote, { immediate: true });
onBeforeUnmount(() => window.clearTimeout(copyTimer));
</script>

<template>
  <main class="content-hub note-detail-hub">
    <OceanAtmosphere variant="notes" />
    <article v-if="note" class="note-document">
      <header>
        <RouterLink to="/notes">← 返回短动态</RouterLink>
        <p>SHORT SIGNAL / {{ note.slug }}</p>
        <time>{{ formatDate(note.published_at ?? note.created_at) }}</time>
      </header>
      <!-- 内容已使用 DOMPurify 清洗。 -->
      <!-- eslint-disable-next-line vue/no-v-html -->
      <div class="note-markdown" v-html="renderedContent"></div>
      <footer>
        <div><span v-for="tag in note.tags" :key="tag"># {{ tag }}</span></div>
        <a v-if="note.external_url" :href="note.external_url" target="_blank" rel="noreferrer noopener">打开相关链接 ↗</a>
        <button type="button" :class="{ confirmed: copyState === 'copied' }" @click="copyLink">
          {{ copyState === "copied" ? "链接已复制" : copyState === "error" ? "复制失败" : "复制链接" }}
        </button>
      </footer>
    </article>
    <section v-else-if="loading" class="content-state">正在读取动态信号…</section>
    <section v-else class="content-state error">
      <p>{{ errorText }}</p>
      <RouterLink :to="notFound ? '/notes' : route.fullPath">{{ notFound ? "返回短动态" : "重新读取" }}</RouterLink>
    </section>
  </main>
</template>
