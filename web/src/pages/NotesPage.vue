<script setup lang="ts">
import { computed, nextTick, onActivated, onMounted, ref, watch } from "vue";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";

import { fetchNotes, type Note } from "../api/content";
import OceanAtmosphere from "../components/OceanAtmosphere.vue";
import OceanIcon from "../components/OceanIcon.vue";
import { useSeo } from "../composables/useSeo";
import { useViewportReveal } from "../composables/useViewportReveal";
import { noteReturnContext } from "../composables/useNoteReturnContext";

defineOptions({ name: "NotesPage" });

const route = useRoute();
const router = useRouter();
const notes = ref<Note[]>([]);
const total = ref(0);
const loading = ref(true);
const errorText = ref("");
const pageRoot = ref<HTMLElement | null>(null);
const { applySeo } = useSeo();
const { observe } = useViewportReveal();
const activeTag = ref(String(route.query.tag ?? ""));
const tags = computed(() => [...new Set(notes.value.flatMap((note) => note.tags))]);
const noteMonths = computed(() => notes.value.map((note) => {
  const date = new Date(note.published_at ?? note.created_at);
  return `${date.getFullYear()}-${date.getMonth()}`;
}));
let loadVersion = 0;

function excerpt(markdown: string) {
  return markdown.replace(/```[\s\S]*?```/g, " ").replace(/[#>*_`[\]()!-]/g, " ").replace(/\s+/g, " ").trim().slice(0, 160);
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

watch(() => [route.path, route.query.tag], () => {
  if (route.path !== "/notes") return;
  const tag = String(route.query.tag ?? "");
  if (tag === activeTag.value) return;
  activeTag.value = tag;
  void loadNotes();
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
    <section v-if="notes.length" class="notes-stream">
      <article
        v-for="(note, index) in notes"
        :key="note.id"
        class="note-signal reveal-item"
        :class="{ 'is-month-end': index < notes.length - 1 && noteMonths[index] !== noteMonths[index + 1] }"
        data-reveal
      >
        <time>{{ formatDate(note.published_at ?? note.created_at) }}</time>
        <div class="note-signal-pulse" aria-hidden="true"><i></i></div>
        <div>
          <p>{{ excerpt(note.content_markdown) }}</p>
          <footer>
            <span v-for="tag in note.tags" :key="tag"># {{ tag }}</span>
            <RouterLink :to="`/notes/${note.slug}`">读取完整信号 <OceanIcon name="next" :size="18" /></RouterLink>
          </footer>
        </div>
      </article>
    </section>
    <section v-else-if="loading" class="content-state">正在监听动态信号…</section>
    <section v-else-if="errorText" class="content-state error"><OceanIcon name="warning" :size="28" />{{ errorText }}</section>
    <section v-else class="content-state">当前没有匹配的动态。</section>
  </main>
</template>
