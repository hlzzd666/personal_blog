<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from "vue";

import OceanIcon from "../components/OceanIcon.vue";
import { fetchGuestbook, submitGuestbook, type GuestbookItem } from "../api/guestbook";
import { useSeo } from "../composables/useSeo";

const { applySeo } = useSeo();
const items = ref<GuestbookItem[]>([]);
const total = ref(0);
const page = ref(1);
const loading = ref(false);
const submitting = ref(false);
const error = ref("");
const success = ref("");
const form = reactive({ nickname: "", content: "", honeypot: "" });
const listPanel = ref<HTMLElement | null>(null);
const pageSize = 6;
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)));
const visiblePages = computed(() => {
  const count = Math.min(5, totalPages.value);
  const start = Math.max(1, Math.min(page.value - 2, totalPages.value - count + 1));
  return Array.from({ length: count }, (_, index) => start + index);
});

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium" }).format(new Date(value));
}

async function loadMessages(targetPage = 1) {
  if (loading.value) return false;
  loading.value = true;
  error.value = "";
  try {
    const result = await fetchGuestbook(targetPage, pageSize);
    items.value = result.items;
    total.value = result.total;
    page.value = result.page;
    return true;
  } catch {
    error.value = "留言读取失败，请稍后重试。";
    return false;
  } finally {
    loading.value = false;
  }
}

async function submit() {
  success.value = "";
  error.value = "";
  if (!form.nickname.trim() || !form.content.trim()) {
    error.value = "请填写昵称和留言内容。";
    return;
  }
  submitting.value = true;
  try {
    await submitGuestbook({ nickname: form.nickname.trim(), content: form.content.trim(), honeypot: form.honeypot });
    form.content = "";
    success.value = "留言已提交，审核通过后会公开显示。";
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "留言提交失败，请稍后重试。";
  } finally {
    submitting.value = false;
  }
}

async function changePage(targetPage: number) {
  const nextPage = Math.min(Math.max(targetPage, 1), totalPages.value);
  if (nextPage === page.value || loading.value) return;
  if (!(await loadMessages(nextPage))) return;
  await nextTick();
  listPanel.value?.scrollIntoView({
    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
    block: "start",
  });
}

onMounted(() => {
  applySeo({ title: "留言板", description: "留下你的航海寄语，审核通过后会展示在留言板。", canonicalPath: "/guestbook" });
  void loadMessages(1);
});
</script>

<template>
  <main class="guestbook-page">
    <header class="guestbook-hero">
      <div class="guestbook-hero-main">
        <RouterLink class="guestbook-back" to="/"><OceanIcon name="home" :size="18" />返回首页</RouterLink>
        <div class="guestbook-kicker-row">
          <p class="guestbook-kicker">MESSAGE BOARD / 留言板</p>
          <span>OPEN LOG</span>
        </div>
        <h1>把想说的话，留在这段航程里。</h1>
        <p class="guestbook-lead">每一条留言都会先经过审核，再成为航海日志里的一枚航标。</p>
      </div>
      <aside class="guestbook-hero-card" aria-label="留言说明">
        <div class="guestbook-card-stamp"><OceanIcon name="comment" :size="18" /><span>CAPTAIN'S LOG</span></div>
        <p>留下你的航线、问题，或者只是此刻想说的话。</p>
        <dl>
          <div><dt>公开方式</dt><dd>审核后展示</dd></div>
          <div><dt>内容格式</dt><dd>纯文本留言</dd></div>
          <div><dt>联系方式</dt><dd>不会公开</dd></div>
        </dl>
      </aside>
    </header>

    <div class="guestbook-layout">
      <section class="guestbook-form-panel" aria-labelledby="guestbook-form-title">
        <div class="guestbook-section-heading">
          <div><p class="guestbook-section-kicker">01 / WRITE</p><h2 id="guestbook-form-title">写下一条留言</h2></div>
          <span class="guestbook-heading-note">匿名也可以</span>
        </div>
        <form @submit.prevent="submit">
          <label><span>昵称</span><input v-model="form.nickname" maxlength="40" required autocomplete="nickname" /></label>
          <label><span>留言</span><textarea v-model="form.content" maxlength="2000" required rows="7" placeholder="说说你从哪段航线经过……" /></label>
          <input v-model="form.honeypot" class="guestbook-honeypot" tabindex="-1" autocomplete="off" aria-hidden="true" />
          <div class="guestbook-form-footer">
            <p class="guestbook-hint">最多 2000 字，提交后等待审核。<span>{{ form.content.length }} / 2000</span></p>
            <button type="submit" :disabled="submitting">{{ submitting ? "正在提交…" : "提交留言" }}</button>
          </div>
          <p v-if="success" class="guestbook-success" role="status">{{ success }}</p>
          <p v-if="error" class="guestbook-error" role="alert">{{ error }}</p>
        </form>
      </section>

      <section ref="listPanel" class="guestbook-list-panel" aria-labelledby="guestbook-list-title" :aria-busy="loading">
        <div class="guestbook-list-heading">
          <div><p class="guestbook-section-kicker">02 / READ</p><h2 id="guestbook-list-title">已通过的留言</h2></div>
          <span class="guestbook-count" aria-live="polite"><span><b>{{ total }}</b> 条</span><small v-if="totalPages > 1">第 {{ page }} / {{ totalPages }} 页</small></span>
        </div>
        <p v-if="loading && !items.length" class="guestbook-state">正在读取留言……</p>
        <p v-else-if="!items.length && !error" class="guestbook-state">还没有留言，来做第一个留下航标的人。</p>
        <p v-if="error && !items.length" class="guestbook-state guestbook-error" role="alert">{{ error }}</p>
        <ol v-else class="guestbook-list">
          <li v-for="(item, index) in items" :key="item.id">
            <span class="guestbook-item-index" aria-hidden="true">{{ String((page - 1) * pageSize + index + 1).padStart(2, "0") }}</span>
            <div class="guestbook-item-body">
              <div class="guestbook-item-meta"><strong>{{ item.nickname }}</strong><time>{{ formatDate(item.created_at) }}</time></div>
              <p>{{ item.content }}</p>
              <div v-if="item.admin_reply" class="guestbook-reply"><b>站长回复</b><span>{{ item.admin_reply }}</span></div>
            </div>
          </li>
        </ol>
        <p v-if="error && items.length" class="guestbook-list-error" role="alert">{{ error }}</p>
        <nav v-if="totalPages > 1" class="guestbook-pagination" aria-label="留言分页">
          <button type="button" :disabled="page === 1 || loading" @click="changePage(page - 1)">上一页</button>
          <div class="guestbook-page-numbers">
            <button v-for="pageNumber in visiblePages" :key="pageNumber" type="button" :class="{ active: pageNumber === page }" :aria-current="pageNumber === page ? 'page' : undefined" :disabled="loading" :aria-label="`第 ${pageNumber} 页`" @click="changePage(pageNumber)">{{ pageNumber }}</button>
          </div>
          <button type="button" :disabled="page === totalPages || loading" @click="changePage(page + 1)">下一页</button>
        </nav>
      </section>
    </div>
  </main>
</template>

<style scoped>
.guestbook-page {
  --guestbook-ink: #143640;
  --guestbook-deep: #0d2b35;
  --guestbook-tide: #2e7776;
  --guestbook-brass: #d8a94e;
  --guestbook-coral: #d66f56;
  --guestbook-fog: #e8f0ef;
  --guestbook-paper: #fbf4e4;
  --guestbook-line: rgba(20, 54, 64, 0.16);
  position: relative;
  min-height: 100vh;
  overflow: clip;
  padding: 8.5rem clamp(1rem, 7vw, 7rem) 5.5rem;
  color: var(--guestbook-ink);
  background:
    radial-gradient(circle at 8% 8%, rgba(216, 169, 78, 0.13), transparent 20rem),
    radial-gradient(circle at 96% 46%, rgba(46, 119, 118, 0.1), transparent 24rem),
    linear-gradient(145deg, #eef4f3 0%, var(--guestbook-fog) 54%, #e2ecec 100%);
  font-family: "Noto Sans SC", sans-serif;
}
.guestbook-page::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  content: "";
  opacity: 0.2;
  background-image: repeating-linear-gradient(105deg, transparent 0 11rem, rgba(20, 54, 64, 0.08) 11rem 11.08rem, transparent 11.08rem 22rem);
}
.guestbook-hero, .guestbook-layout { position: relative; width: min(1180px, 100%); margin: 0 auto; }
.guestbook-hero { display: grid; grid-template-columns: minmax(0, 1fr) minmax(16rem, 19rem); gap: clamp(2rem, 7vw, 7rem); align-items: end; padding-bottom: 3.5rem; border-bottom: 1px solid var(--guestbook-line); }
.guestbook-hero-main { min-width: 0; }
.guestbook-back { display: inline-flex; gap: .4rem; align-items: center; color: var(--guestbook-coral); font-size: .9rem; font-weight: 700; text-decoration: none; transition: gap 180ms ease, color 180ms ease; }
.guestbook-back:hover, .guestbook-back:focus-visible { gap: .65rem; color: var(--guestbook-deep); }
.guestbook-kicker-row { display: flex; flex-wrap: wrap; gap: .8rem 1rem; align-items: center; margin: 3.3rem 0 1rem; }
.guestbook-kicker, .guestbook-kicker-row > span, .guestbook-section-kicker { margin: 0; color: var(--guestbook-coral); font: 700 .67rem "IBM Plex Mono", monospace; letter-spacing: .08em; }
.guestbook-kicker-row > span { padding: .28rem .5rem; border: 1px solid rgba(214, 111, 86, .4); color: var(--guestbook-tide); }
h1 { max-width: 13ch; margin: 0; color: var(--guestbook-deep); font-family: var(--display-font); font-size: clamp(3.25rem, 7vw, 6.2rem); letter-spacing: -.045em; line-height: 1.03; text-wrap: balance; }
.guestbook-lead { max-width: 38rem; margin: 1.3rem 0 0; color: rgba(20, 54, 64, .72); font-size: clamp(.96rem, 1.3vw, 1.08rem); line-height: 1.85; }
.guestbook-hero-card { position: relative; padding: 1.35rem 1.35rem 1.5rem; overflow: hidden; border: 1px solid rgba(216, 169, 78, .45); border-radius: 16px 4px 16px 4px; color: #f7eedc; background: var(--guestbook-deep); box-shadow: 0 1.5rem 2.8rem rgba(13, 43, 53, .16); }
.guestbook-hero-card::after { position: absolute; right: -2.3rem; bottom: -3rem; width: 8rem; height: 8rem; border: 1px solid rgba(216, 169, 78, .35); border-radius: 50%; content: ""; box-shadow: 0 0 0 1.2rem rgba(216, 169, 78, .07), 0 0 0 2.4rem rgba(216, 169, 78, .04); }
.guestbook-card-stamp { display: flex; gap: .45rem; align-items: center; color: var(--guestbook-brass); font: 700 .68rem "IBM Plex Mono", monospace; letter-spacing: .07em; }
.guestbook-hero-card > p { margin: 1.2rem 0 1.35rem; color: rgba(247, 238, 220, .9); font-family: var(--display-font); font-size: 1.1rem; line-height: 1.55; }
.guestbook-hero-card dl { display: grid; gap: .55rem; margin: 0; }
.guestbook-hero-card dl > div { display: flex; justify-content: space-between; gap: 1rem; padding-top: .55rem; border-top: 1px solid rgba(247, 238, 220, .16); font-size: .72rem; }
.guestbook-hero-card dt { color: rgba(247, 238, 220, .58); }
.guestbook-hero-card dd { margin: 0; color: #f7eedc; font-weight: 700; }
.guestbook-layout { display: grid; grid-template-columns: minmax(280px, .78fr) minmax(0, 1.22fr); gap: 1.25rem; align-items: start; margin-top: 1.35rem; }
.guestbook-form-panel, .guestbook-list-panel { position: relative; padding: clamp(1.35rem, 3vw, 2.4rem); border: 1px solid var(--guestbook-line); border-radius: 16px; box-shadow: 0 1.2rem 2.8rem rgba(20, 54, 64, .08); }
.guestbook-form-panel { border-top: 4px solid var(--guestbook-brass); background: rgba(251, 244, 228, .92); }
.guestbook-list-panel { border-top: 4px solid var(--guestbook-tide); background: rgba(255, 252, 245, .78); }
.guestbook-section-heading, .guestbook-list-heading { display: flex; align-items: end; justify-content: space-between; gap: 1rem; }
.guestbook-section-kicker { margin-bottom: .4rem; color: var(--guestbook-tide); }
.guestbook-heading-note, .guestbook-count { color: rgba(20, 54, 64, .56); font-size: .75rem; }
.guestbook-count { display: grid; gap: .2rem; justify-items: end; font-family: "IBM Plex Mono", monospace; white-space: nowrap; }
.guestbook-count b { color: var(--guestbook-deep); font-size: 1.1rem; }
.guestbook-count small { color: rgba(20, 54, 64, .5); font-size: .62rem; }
h2 { margin: 0; color: var(--guestbook-deep); font-family: var(--display-font); font-size: clamp(1.4rem, 2.3vw, 1.8rem); line-height: 1.2; }
form { display: grid; gap: 1rem; margin-top: 1.8rem; }
label { display: grid; gap: .45rem; color: rgba(20, 54, 64, .68); font-size: .82rem; font-weight: 700; }
input, textarea { width: 100%; box-sizing: border-box; border: 1px solid rgba(20, 54, 64, .2); border-radius: 10px; padding: .82rem .9rem; color: var(--guestbook-ink); background: rgba(255, 255, 255, .56); font: inherit; transition: border-color 180ms ease, background-color 180ms ease, box-shadow 180ms ease; }
input:hover, textarea:hover { border-color: rgba(46, 119, 118, .5); }
input:focus, textarea:focus { border-color: var(--guestbook-tide); background: #fffdf8; box-shadow: 0 0 0 4px rgba(46, 119, 118, .1); outline: none; }
textarea { min-height: 10.5rem; resize: vertical; line-height: 1.75; }
input:focus-visible, textarea:focus-visible, button:focus-visible { outline: 3px solid rgba(214, 111, 86, .8); outline-offset: 3px; }
.guestbook-form-footer { display: flex; gap: 1rem; align-items: center; justify-content: space-between; }
button { border: 0; border-radius: 9px; padding: .78rem 1.05rem; color: #fff8e9; background: var(--guestbook-deep); font: inherit; font-weight: 800; cursor: pointer; box-shadow: 0 .5rem 1.2rem rgba(13, 43, 53, .15); transition: transform 180ms ease, background-color 180ms ease, box-shadow 180ms ease; }
button:hover:not(:disabled) { background: var(--guestbook-tide); box-shadow: 0 .75rem 1.4rem rgba(46, 119, 118, .2); transform: translateY(-2px); }
button:disabled { cursor: wait; opacity: .55; }
.guestbook-hint, .guestbook-state { color: rgba(20, 54, 64, .58); font-size: .78rem; line-height: 1.7; }
.guestbook-hint { margin: 0; }
.guestbook-hint span { display: inline-block; margin-left: .4rem; color: var(--guestbook-tide); font-family: "IBM Plex Mono", monospace; font-size: .68rem; }
.guestbook-honeypot { position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none; }
.guestbook-success, .guestbook-error { margin: 0; font-size: .82rem; line-height: 1.6; }
.guestbook-success { color: #277464; }
.guestbook-error { color: #b44b3e; }
.guestbook-list-panel { scroll-margin-top: 5.5rem; }
.guestbook-list { display: grid; gap: 0; padding: 0; margin: 1.5rem 0 0; list-style: none; }
.guestbook-list li { display: grid; grid-template-columns: 2.25rem minmax(0, 1fr); gap: 1rem; padding: 1.25rem 0 1.35rem; border-top: 1px solid var(--guestbook-line); }
.guestbook-item-index { padding-top: .05rem; color: var(--guestbook-brass); font: 700 .68rem "IBM Plex Mono", monospace; letter-spacing: .06em; }
.guestbook-item-body { min-width: 0; }
.guestbook-item-meta { display: flex; justify-content: space-between; gap: 1rem; }
.guestbook-item-meta strong { color: var(--guestbook-deep); font-size: .95rem; }
.guestbook-item-meta time { color: rgba(20, 54, 64, .52); font: .68rem "IBM Plex Mono", monospace; }
.guestbook-item-body > p { margin: .65rem 0 0; white-space: pre-wrap; line-height: 1.85; }
.guestbook-reply { display: grid; gap: .25rem; margin-top: .9rem; padding: .75rem .85rem; border-left: 1px solid var(--guestbook-coral); border-radius: 0 8px 8px 0; color: rgba(20, 54, 64, .7); background: rgba(214, 111, 86, .08); font-size: .82rem; line-height: 1.65; }
.guestbook-reply b { color: #b44b3e; }
.guestbook-state { margin: 2.25rem 0 .75rem; padding: 2.5rem 1rem; border: 1px dashed rgba(20, 54, 64, .22); border-radius: 10px; text-align: center; }
.guestbook-list-error { margin: .75rem 0 0; color: #b44b3e; font-size: .78rem; }
.guestbook-pagination { display: flex; gap: .75rem; align-items: center; justify-content: space-between; padding-top: 1.15rem; border-top: 1px solid var(--guestbook-line); }
.guestbook-pagination button { min-height: 2.55rem; padding: .55rem .85rem; border: 1px solid rgba(20, 54, 64, .2); border-radius: 4px; color: var(--guestbook-ink); background: transparent; box-shadow: none; font-size: .76rem; }
.guestbook-pagination button:hover:not(:disabled), .guestbook-pagination button:focus-visible, .guestbook-pagination button.active { color: #fff8e9; background: var(--guestbook-deep); border-color: var(--guestbook-deep); transform: none; }
.guestbook-pagination button:disabled { cursor: default; opacity: .38; }
.guestbook-page-numbers { display: flex; gap: .35rem; align-items: center; justify-content: center; }
.guestbook-page-numbers button { width: 2.55rem; padding-inline: 0; font-family: "IBM Plex Mono", monospace; }
@media (min-width: 801px) { .guestbook-form-panel { position: sticky; top: 5.5rem; } }
@media (max-width: 900px) { .guestbook-hero { grid-template-columns: 1fr; gap: 2rem; } .guestbook-hero-card { max-width: 28rem; margin-top: 0; } }
@media (max-width: 800px) { .guestbook-layout { grid-template-columns: 1fr; } }
@media (max-width: 560px) { .guestbook-page { padding: 7.6rem 1rem 4rem; } h1 { font-size: clamp(2.75rem, 14vw, 4.3rem); } .guestbook-kicker-row { margin-top: 2.5rem; } .guestbook-form-footer { align-items: stretch; flex-direction: column; } .guestbook-form-footer button { width: 100%; } .guestbook-list li { grid-template-columns: 1.8rem minmax(0, 1fr); gap: .65rem; } .guestbook-item-meta { align-items: flex-start; flex-direction: column; gap: .35rem; } .guestbook-pagination { gap: .4rem; } .guestbook-pagination > button { padding-inline: .65rem; } .guestbook-page-numbers { gap: .25rem; } .guestbook-page-numbers button { width: 2.35rem; } }
@media (prefers-reduced-motion: reduce) { .guestbook-back, input, textarea, button { transition: none; } }
</style>
