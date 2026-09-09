<script setup lang="ts">
import { computed, nextTick, onActivated, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";

import { fetchNotes, type Note } from "../api/content";
import OceanAtmosphere from "../components/OceanAtmosphere.vue";
import OceanIcon from "../components/OceanIcon.vue";
import { useSeo } from "../composables/useSeo";
import { useViewportReveal } from "../composables/useViewportReveal";
import { noteReturnContext } from "../composables/useNoteReturnContext";

defineOptions({ name: "NotesPage" });

type NoteSignalView = {
  note: Note;
  text: string;
  imageUrl: string;
  imageAlt: string;
  monthKey: string;
  isImageOnly: boolean;
};
type PreviewImage = { src: string; alt: string; caption: string };

const route = useRoute();
const router = useRouter();
const notes = ref<Note[]>([]);
const total = ref(0);
const loading = ref(true);
const errorText = ref("");
const pageRoot = ref<HTMLElement | null>(null);
const previewImage = ref<PreviewImage | null>(null);
const { applySeo } = useSeo();
const { observe } = useViewportReveal();
const activeTag = ref(String(route.query.tag ?? ""));
const tags = computed(() => [...new Set(notes.value.flatMap((note) => note.tags))]);
const noteSignals = computed<NoteSignalView[]>(() => notes.value.map((note) => {
  const signal = parseNoteSignal(note.content_markdown);
  const date = new Date(note.published_at ?? note.created_at);
  return {
    note,
    ...signal,
    monthKey: `${date.getFullYear()}-${date.getMonth()}`,
  };
}));
let loadVersion = 0;
let bodyOverflowBeforePreview: string | null = null;

function normalizeMarkdown(markdown: string) {
  return !markdown.includes("\n") && markdown.includes("\\n") ? markdown.replace(/\\n/g, "\n") : markdown;
}

function stripMarkdown(markdown: string) {
  return markdown.replace(/```[\s\S]*?```/g, " ").replace(/[#>*_`[\]()!-]/g, " ").replace(/\s+/g, " ").trim();
}

function parseNoteSignal(markdown: string) {
  const content = normalizeMarkdown(markdown);
  const htmlImagePattern = new RegExp("<" + "img[^>]*src=[\"']([^\"']+)[\"'][^>]*>", "i");
  const htmlAltPattern = new RegExp("alt=[\"']([^\"']*)[\"']", "i");
  const markdownImage = /!\[([^\]]*)]\(([^)\s]+)(?:\s+"[^"]*")?\)/i.exec(content);
  const htmlImage = htmlImagePattern.exec(content);
  const bareImage = /https?:\/\/[^\s<>"')]+\.(?:png|jpe?g|gif|webp|avif|svg)(?:\?[^\s<>"')]+)?/i.exec(content);
  const imageUrl = markdownImage?.[2] || htmlImage?.[1] || bareImage?.[0] || "";
  const imageAlt = markdownImage?.[1]?.trim() || htmlAltPattern.exec(htmlImage?.[0] ?? "")?.[1]?.trim() || "动态图片";
  const textSource = content
    .replace(/!\[[^\]]*]\([^)]+\)/gi, " ")
    .replace(new RegExp("<" + "img[^>]*>", "gi"), " ")
    .replace(/https?:\/\/[^\s<>"')]+\.(?:png|jpe?g|gif|webp|avif|svg)(?:\?[^\s<>"')]+)?/gi, " ");
  const text = stripMarkdown(textSource).slice(0, 160);
  return { imageUrl, imageAlt, text, isImageOnly: Boolean(imageUrl && !text) };
}

function formatDate(value: string | null) {
  return new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "long", day: "numeric" }).format(
    new Date(value ?? Date.now()),
  );
}

async function loadNotes() {
  const version = ++loadVersion;
  loading.value = true;
  errorText.value = "";
  try {
    const result = await fetchNotes({ page: 1, page_size: 100, tag: activeTag.value || undefined });
    if (version !== loadVersion) return;
    notes.value = result.items;
    total.value = result.total;
  } catch {
    if (version !== loadVersion) return;
    errorText.value = "动态信号暂时无法接收，请稍后重试。";
  } finally {
    if (version === loadVersion) {
      loading.value = false;
      void observe(pageRoot.value);
    }
  }
}

function selectTag(tag: string) {
  void router.push({ path: "/notes", query: tag ? { tag } : {} });
}

function openImagePreview(signal: NoteSignalView) {
  if (!signal.imageUrl) return;
  const caption = signal.imageAlt === "动态图片" ? "" : signal.imageAlt;
  previewImage.value = { src: signal.imageUrl, alt: signal.imageAlt, caption };
}

function closeImagePreview() {
  previewImage.value = null;
}

function handlePreviewKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") closeImagePreview();
}

watch(() => [route.path, route.query.tag], () => {
  if (route.path !== "/notes") return;
  const tag = String(route.query.tag ?? "");
  if (tag === activeTag.value) return;
  activeTag.value = tag;
  void loadNotes();
});

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

onBeforeRouteLeave((to) => {
  noteReturnContext.path = route.fullPath;
  noteReturnContext.scrollY = window.scrollY;
  noteReturnContext.slug = to.path.startsWith("/notes/") ? String(to.params.slug) : "";
});

onActivated(async () => {
  applySeo({ title: "短动态", description: "开发进度、即时想法和沿途记录。", canonicalPath: "/notes" });
  await nextTick();
  window.requestAnimationFrame(() => {
    if (route.path !== "/notes") return;
    if (!loading.value && noteReturnContext.path === route.fullPath) {
      window.scrollTo({ top: noteReturnContext.scrollY, left: 0, behavior: "instant" });
    }
    void observe(pageRoot.value);
  });
});
onMounted(() => void loadNotes());

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handlePreviewKeydown);
  if (bodyOverflowBeforePreview !== null) document.body.style.overflow = bodyOverflowBeforePreview;
});
</script>

<template>
  <main ref="pageRoot" class="content-hub notes-hub">
    <OceanAtmosphere variant="notes" />
    <header class="content-hub-hero hub-masthead notes-masthead">
      <div class="hub-hero-copy">
        <RouterLink class="hub-back" to="/"><OceanIcon name="home" :size="18" />返回首页</RouterLink>
        <h1>短动态</h1>
        <p>不必展开成长文，也值得留下坐标。</p>
        <div class="hub-hero-meta"><span>SHORT SIGNALS</span><strong>{{ total }} 条信号</strong></div>
      </div>
      <div class="hub-hero-aside">
        <p>把灵感、进度和小事留在时间轴上，沿着日期回看每一个坐标。</p>
        <div class="hub-instrument hub-instrument--signal" aria-hidden="true">
          <span class="hub-instrument-label">LIVE LOG</span>
          <div class="signal-meter"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
          <span class="hub-instrument-note">LISTEN FOR SMALL THINGS</span>
        </div>
      </div>
    </header>
    <nav v-if="tags.length" class="notes-tags" aria-label="动态标签">
      <button :class="{ active: !activeTag }" type="button" @click="selectTag('')">全部</button>
      <button v-for="tag in tags" :key="tag" :class="{ active: activeTag === tag }" type="button" @click="selectTag(tag)"># {{ tag }}</button>
    </nav>
    <div class="hub-section-lead notes-section-lead"><span>信号记录</span><span>最新在前</span></div>
    <section v-if="noteSignals.length" class="notes-stream">
      <article
        v-for="(signal, index) in noteSignals"
        :key="signal.note.id"
        class="note-signal reveal-item"
        :class="{ 'has-image': signal.imageUrl, 'image-only': signal.isImageOnly, 'is-month-end': index < noteSignals.length - 1 && signal.monthKey !== noteSignals[index + 1].monthKey }"
        data-reveal
      >
        <time>{{ formatDate(signal.note.published_at ?? signal.note.created_at) }}</time>
        <div class="note-signal-pulse" aria-hidden="true"><i></i></div>
        <div>
          <button v-if="signal.imageUrl" class="note-image-card" type="button" :aria-label="`查看${signal.imageAlt}`" @click="openImagePreview(signal)">
            <span class="note-image-card-label">IMAGE SIGNAL / 影像信号</span>
            <img :src="signal.imageUrl" :alt="signal.imageAlt" loading="lazy" decoding="async" />
          </button>
          <p v-if="signal.text">{{ signal.text }}</p>
          <p v-else-if="signal.imageUrl" class="note-image-summary">一张影像信号已靠岸。</p>
          <footer>
            <span v-for="tag in signal.note.tags" :key="tag"># {{ tag }}</span>
            <RouterLink :to="`/notes/${signal.note.slug}`">读取完整信号 <OceanIcon name="next" :size="18" /></RouterLink>
          </footer>
        </div>
      </article>
    </section>
    <section v-else-if="loading" class="content-state">正在监听动态信号…</section>
    <section v-else-if="errorText" class="content-state error"><OceanIcon name="warning" :size="28" />{{ errorText }}</section>
    <section v-else class="content-state">当前没有匹配的动态。</section>
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
