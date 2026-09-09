<script setup lang="ts">
import DOMPurify from "dompurify";
import { marked } from "marked";
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { fetchNote, type Note } from "../api/content";
import { ApiError } from "../api/http";
import OceanAtmosphere from "../components/OceanAtmosphere.vue";
import OceanIcon from "../components/OceanIcon.vue";
import { useSeo } from "../composables/useSeo";
import { noteReturnContext } from "../composables/useNoteReturnContext";

type PreviewImage = { src: string; alt: string; caption: string };

const route = useRoute();
const note = ref<Note | null>(null);
const loading = ref(true);
const notFound = ref(false);
const errorText = ref("");
const copyState = ref<"idle" | "copied" | "error">("idle");
const previewImage = ref<PreviewImage | null>(null);
const { applySeo } = useSeo();
let copyTimer: number | undefined;
let bodyOverflowBeforePreview: string | null = null;
const returnPath = computed(() => noteReturnContext.slug === route.params.slug ? noteReturnContext.path : "/notes");

const renderedContent = computed(() => {
  if (!note.value) return "";
  const safeDocument = new DOMParser().parseFromString(DOMPurify.sanitize(marked.parse(note.value.content_markdown) as string), "text/html");
  safeDocument.body.querySelectorAll("img").forEach((image) => {
    image.setAttribute("loading", "lazy");
    image.setAttribute("decoding", "async");
    image.setAttribute("tabindex", "0");
    image.setAttribute("role", "button");
    image.setAttribute("aria-label", image.getAttribute("alt") || "查看动态图片");
  });
  return safeDocument.body.innerHTML;
});

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

function openImagePreview(image: HTMLImageElement) {
  const src = image.currentSrc || image.getAttribute("src");
  if (!src) return;
  const alt = image.getAttribute("alt")?.trim() || "";
  previewImage.value = { src, alt: alt || "动态图片", caption: alt };
}

function handleContentClick(event: MouseEvent) {
  if (!(event.target instanceof Element)) return;
  const target = event.target.closest("img");
  if (!(target instanceof HTMLImageElement)) return;
  event.preventDefault();
  openImagePreview(target);
}

function handleContentKeydown(event: KeyboardEvent) {
  if (event.key !== "Enter" && event.key !== " ") return;
  if (!(event.target instanceof HTMLImageElement)) return;
  event.preventDefault();
  openImagePreview(event.target);
}

function closeImagePreview() {
  previewImage.value = null;
}

function handlePreviewKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") closeImagePreview();
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

watch(previewImage, (image) => {
  if (image) {
    if (bodyOverflowBeforePreview === null) bodyOverflowBeforePreview = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handlePreviewKeydown);
    return;
  }
  window.removeEventListener("keydown", handlePreviewKeydown);
  if (bodyOverflowBeforePreview !== null) document.body.style.overflow = bodyOverflowBeforePreview;
  bodyOverflowBeforePreview = null;
});

onBeforeUnmount(() => {
  window.clearTimeout(copyTimer);
  window.removeEventListener("keydown", handlePreviewKeydown);
  if (bodyOverflowBeforePreview !== null) document.body.style.overflow = bodyOverflowBeforePreview;
});
</script>

<template>
  <main class="content-hub note-detail-hub">
    <OceanAtmosphere variant="notes" />
    <article v-if="note" class="note-document">
      <header>
        <RouterLink :to="returnPath"><OceanIcon name="previous" :size="18" />返回短动态</RouterLink>
        <p>SHORT SIGNAL / {{ note.slug }}</p>
        <time><OceanIcon name="time" :size="18" />{{ formatDate(note.published_at ?? note.created_at) }}</time>
      </header>
      <!-- 内容已使用 DOMPurify 清洗。 -->
      <!-- eslint-disable-next-line vue/no-v-html -->
      <div class="note-markdown" @click="handleContentClick" @keydown="handleContentKeydown" v-html="renderedContent"></div>
      <footer>
        <div><span v-for="tag in note.tags" :key="tag"># {{ tag }}</span></div>
        <a v-if="note.external_url" :href="note.external_url" target="_blank" rel="noreferrer noopener"><OceanIcon name="external" :size="18" />打开相关链接</a>
        <button type="button" :class="{ confirmed: copyState === 'copied' }" @click="copyLink">
          {{ copyState === "copied" ? "链接已复制" : copyState === "error" ? "复制失败" : "复制链接" }}
        </button>
      </footer>
    </article>
    <section v-else-if="loading" class="content-state">正在读取动态信号…</section>
    <section v-else class="content-state error">
      <OceanIcon name="warning" :size="28" />
      <p>{{ errorText }}</p>
      <RouterLink :to="notFound ? returnPath : route.fullPath">{{ notFound ? "返回短动态" : "重新读取" }}</RouterLink>
    </section>
    <Teleport to="body">
      <Transition name="note-image-preview">
        <div v-if="previewImage" class="note-image-preview" role="dialog" aria-modal="true" :aria-label="previewImage.alt" tabindex="-1" @click.self="closeImagePreview" @keydown="handlePreviewKeydown">
          <button class="note-image-preview-close" type="button" aria-label="关闭图片预览" @click="closeImagePreview">×</button>
          <figure>
            <img :src="previewImage.src" :alt="previewImage.alt" />
            <figcaption v-if="previewImage.caption">{{ previewImage.caption }}</figcaption>
          </figure>
        </div>
      </Transition>
    </Teleport>
  </main>
</template>
