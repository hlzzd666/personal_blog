<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import OceanIcon from "../components/OceanIcon.vue";
import { iconCatalog, iconGroups, type IconGroup } from "../icons";
import { useSeo } from "../composables/useSeo";

const { applySeo } = useSeo();
const activeGroup = ref<IconGroup | "all">("all");
const featuredIcons = iconCatalog.slice(0, 6);
const visibleIcons = computed(() =>
  activeGroup.value === "all"
    ? iconCatalog
    : iconCatalog.filter((icon) => icon.group === activeGroup.value),
);

onMounted(() =>
  applySeo({
    title: "图标航海图",
    description: "浏览个人航海日志使用的 24 枚多色图标及其适用场景。",
    canonicalPath: "/icons",
  }),
);
</script>

<template>
  <main class="icon-atlas">
    <!--
      THESIS: 用一张可操作的船员器物清单讲清图标系统，拒绝等大贴纸卡片墙。
      OWN-WORLD: 深海蓝工作台、黄铜刻度、珊瑚红航标、帆布白记录面；图标保持手绘不规则轮廓。
      STORY: 访客先辨认六个核心航向，再按功能筛选并理解每枚图标应该出现在哪里。
      FIRST VIEWPORT: 左侧标题与说明，右侧六枚核心图标沿航线展开；分类控制紧接首屏下缘。
      FORM: 航海器材清单，代码驱动的既有视觉延伸，seed key direct-extension.
      FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
    -->
    <header class="atlas-hero">
      <div class="atlas-introduction">
        <RouterLink class="atlas-back" to="/">
          <OceanIcon name="previous" :size="24" />
          返回首页
        </RouterLink>
        <h1>图标航海图</h1>
        <p>24 枚航海器物构成前台的方向语言。它们先说明功能，再留下伟大航路的记忆点。</p>
        <dl class="atlas-specification">
          <div><dt>文件</dt><dd>透明 PNG</dd></div>
          <div><dt>源尺寸</dt><dd>256 × 256</dd></div>
          <div><dt>界面尺寸</dt><dd>20–64 px</dd></div>
        </dl>
      </div>

      <div class="atlas-route" aria-label="六个核心导航图标">
        <div v-for="(icon, index) in featuredIcons" :key="icon.name" class="route-stop">
          <OceanIcon :name="icon.name" :size="index === 0 || index === 4 ? 88 : 72" />
          <span>{{ icon.label }}</span>
        </div>
      </div>
    </header>

    <section class="atlas-catalog" aria-labelledby="icon-catalog-title">
      <div class="atlas-toolbar">
        <div>
          <h2 id="icon-catalog-title">24 枚航海符号</h2>
          <p>在实际按钮中搭配可见文字；仅在语义明确时单独使用。</p>
        </div>
        <div class="atlas-groups" role="group" aria-label="筛选图标类别">
          <button type="button" :aria-pressed="activeGroup === 'all'" @click="activeGroup = 'all'">全部</button>
          <button
            v-for="group in iconGroups"
            :key="group.id"
            type="button"
            :aria-pressed="activeGroup === group.id"
            @click="activeGroup = group.id"
          >
            {{ group.label }}
          </button>
        </div>
      </div>

      <TransitionGroup name="atlas-list" tag="ul" class="icon-ledger">
        <li v-for="icon in visibleIcons" :key="icon.name">
          <div class="icon-well">
            <OceanIcon :name="icon.name" :size="72" />
          </div>
          <div class="icon-identity">
            <h3>{{ icon.label }}</h3>
            <span>{{ icon.motif }}</span>
          </div>
          <p>{{ icon.usage }}</p>
          <code>{{ icon.name }}</code>
        </li>
      </TransitionGroup>
    </section>

    <aside class="atlas-notice">
      <OceanIcon name="warning" :size="48" />
      <p>本图标系统是用于个人博客界面的非官方同人风格视觉，不代表原作或版权方的官方设计。</p>
    </aside>
  </main>
</template>

<style scoped>
.icon-atlas {
  --atlas-ground: #dce8e9;
  --atlas-panel: #f8f0dc;
  --atlas-ink: #123247;
  --atlas-muted: #536b72;
  --atlas-brass: #754a08;
  --atlas-coral: #a92f2a;
  min-height: 100vh;
  padding: 8.25rem clamp(1rem, 5vw, 5.5rem) 5rem;
  color: var(--atlas-ink);
  background:
    linear-gradient(rgba(18, 50, 71, 0.055) 1px, transparent 1px),
    linear-gradient(90deg, rgba(18, 50, 71, 0.055) 1px, transparent 1px),
    var(--atlas-ground);
  background-size: 32px 32px;
  font-family: "Noto Sans SC", sans-serif;
}

.atlas-hero,
.atlas-catalog,
.atlas-notice {
  width: min(1260px, 100%);
  margin-inline: auto;
}

.atlas-hero {
  display: grid;
  grid-template-columns: minmax(18rem, 0.78fr) minmax(32rem, 1.22fr);
  gap: clamp(2rem, 7vw, 7rem);
  align-items: center;
  min-height: min(35rem, calc(100vh - 9rem));
  padding-bottom: 4rem;
}

.atlas-back {
  display: inline-flex;
  gap: 0.45rem;
  align-items: center;
  color: var(--atlas-coral);
  font-weight: 800;
  text-decoration: none;
}

.atlas-back:hover :deep(.ocean-icon),
.atlas-back:focus-visible :deep(.ocean-icon) {
  transform: translateX(-0.18rem);
}

h1,
h2,
h3,
p,
dl,
dd {
  margin: 0;
}

h1,
h2,
h3 {
  font-family: var(--display-font);
  letter-spacing: 0;
}

h1 {
  max-width: 7ch;
  margin-top: 2.4rem;
  font-size: clamp(3.6rem, 7vw, 5.8rem);
  line-height: 0.96;
}

.atlas-introduction > p {
  max-width: 34rem;
  margin-top: 1.6rem;
  color: var(--atlas-muted);
  font-size: 1.05rem;
  line-height: 1.85;
}

.atlas-specification {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(18, 50, 71, 0.18);
}

.atlas-specification div {
  display: grid;
  gap: 0.2rem;
}

.atlas-specification dt {
  color: var(--atlas-muted);
  font-size: 0.72rem;
}

.atlas-specification dd {
  font-weight: 800;
}

.atlas-route {
  position: relative;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 2.5rem 1.1rem;
  isolation: isolate;
}

.atlas-route::before {
  content: "";
  position: absolute;
  inset: 20% 8% 18%;
  z-index: -1;
  border: 2px dashed rgba(184, 124, 32, 0.42);
  border-radius: 50%;
  transform: rotate(-7deg);
}

.route-stop {
  display: grid;
  place-items: center;
  min-width: 0;
  color: var(--atlas-ink);
  font-size: 0.82rem;
  font-weight: 900;
}

.route-stop:nth-child(2),
.route-stop:nth-child(5) {
  transform: translateY(1.4rem);
}

.route-stop :deep(.ocean-icon) {
  margin-bottom: 0.35rem;
}

.atlas-catalog {
  padding: clamp(2rem, 5vw, 4.2rem);
  border: 1px solid rgba(18, 50, 71, 0.16);
  border-radius: 6px;
  background: color-mix(in srgb, var(--atlas-panel) 93%, transparent);
  box-shadow: 0 1.3rem 3rem rgba(16, 43, 52, 0.12);
}

.atlas-toolbar {
  display: flex;
  gap: 2rem;
  align-items: end;
  justify-content: space-between;
  padding-bottom: 2rem;
}

.atlas-toolbar h2 {
  font-size: clamp(2rem, 4vw, 3.5rem);
}

.atlas-toolbar p {
  margin-top: 0.55rem;
  color: var(--atlas-muted);
}

.atlas-groups {
  display: inline-flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  border: 1px solid rgba(18, 50, 71, 0.2);
  border-radius: 4px;
  overflow: hidden;
}

.atlas-groups button {
  min-height: 2.55rem;
  padding: 0.55rem 0.85rem;
  border: 0;
  border-right: 1px solid rgba(18, 50, 71, 0.16);
  color: var(--atlas-muted);
  background: transparent;
  font: inherit;
  font-size: 0.82rem;
  font-weight: 800;
  cursor: pointer;
}

.atlas-groups button:last-child {
  border-right: 0;
}

.atlas-groups button[aria-pressed="true"] {
  color: #fffaf0;
  background: var(--atlas-ink);
}

.atlas-groups button:focus-visible {
  position: relative;
  z-index: 1;
  outline: 3px solid var(--atlas-coral);
  outline-offset: -4px;
}

.icon-ledger {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 0;
  padding: 0;
  border-top: 1px solid rgba(18, 50, 71, 0.16);
  list-style: none;
}

.icon-ledger li {
  display: grid;
  grid-template-columns: 5.2rem minmax(0, 1fr);
  grid-template-rows: auto auto 1fr;
  column-gap: 1rem;
  min-width: 0;
  padding: 1.5rem 1.1rem 1.6rem 0;
  border-bottom: 1px solid rgba(18, 50, 71, 0.13);
}

.icon-ledger li:not(:nth-child(3n + 1)) {
  padding-left: 1.1rem;
  border-left: 1px solid rgba(18, 50, 71, 0.13);
}

.icon-well {
  grid-row: 1 / span 3;
  display: grid;
  place-items: center;
  width: 5.2rem;
  height: 5.2rem;
  border-radius: 50%;
  background: rgba(93, 183, 198, 0.13);
}

.icon-ledger li:hover :deep(.ocean-icon),
.icon-ledger li:focus-within :deep(.ocean-icon) {
  filter: drop-shadow(0 0.28rem 0.3rem rgba(4, 19, 29, 0.28)) saturate(1.08);
  transform: translateY(-0.2rem) rotate(-1deg);
}

.icon-identity {
  display: flex;
  gap: 0.6rem;
  align-items: baseline;
}

.icon-identity h3 {
  font-size: 1.18rem;
}

.icon-identity span {
  color: var(--atlas-brass);
  font-size: 0.72rem;
  font-weight: 900;
}

.icon-ledger p {
  margin-top: 0.45rem;
  color: var(--atlas-muted);
  font-size: 0.82rem;
  line-height: 1.65;
}

.icon-ledger code {
  align-self: end;
  margin-top: 0.65rem;
  color: var(--atlas-coral);
  font-size: 0.72rem;
}

.atlas-notice {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-top: 2rem;
  padding: 1rem 0;
  color: var(--atlas-muted);
  font-size: 0.82rem;
  line-height: 1.65;
}

.atlas-list-enter-active,
.atlas-list-leave-active {
  transition: opacity 180ms ease, transform 220ms cubic-bezier(0.2, 0.76, 0.26, 1);
}

.atlas-list-enter-from,
.atlas-list-leave-to {
  opacity: 0;
  transform: translateY(0.4rem);
}

@media (max-width: 980px) {
  .atlas-hero {
    grid-template-columns: 1fr;
    gap: 3rem;
  }

  .atlas-route {
    width: min(38rem, 100%);
    margin-inline: auto;
  }

  .icon-ledger {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .icon-ledger li:not(:nth-child(3n + 1)) {
    padding-left: 0;
    border-left: 0;
  }

  .icon-ledger li:nth-child(even) {
    padding-left: 1.1rem;
    border-left: 1px solid rgba(18, 50, 71, 0.13);
  }
}

@media (max-width: 680px) {
  .icon-atlas {
    padding: 7.8rem 1rem 3.5rem;
  }

  .atlas-hero {
    min-height: auto;
    padding-bottom: 3rem;
  }

  h1 {
    font-size: 3.6rem;
  }

  .atlas-route {
    gap: 1.6rem 0.3rem;
  }

  .route-stop:nth-child(2),
  .route-stop:nth-child(5) {
    transform: translateY(0.7rem);
  }

  .atlas-catalog {
    padding: 1.35rem;
  }

  .atlas-toolbar {
    display: grid;
    align-items: start;
  }

  .atlas-groups {
    justify-self: stretch;
  }

  .atlas-groups button {
    flex: 1 1 auto;
  }

  .icon-ledger {
    grid-template-columns: 1fr;
  }

  .icon-ledger li,
  .icon-ledger li:nth-child(even) {
    padding-right: 0;
    padding-left: 0;
    border-left: 0;
  }
}

@media (prefers-color-scheme: dark) {
  .icon-atlas {
    --atlas-ground: #071c29;
    --atlas-panel: #0e2938;
    --atlas-ink: #f6ebd4;
    --atlas-muted: #b8c9c7;
    --atlas-brass: #f0c162;
    --atlas-coral: #ff7868;
    background:
      linear-gradient(rgba(93, 183, 198, 0.07) 1px, transparent 1px),
      linear-gradient(90deg, rgba(93, 183, 198, 0.07) 1px, transparent 1px),
      var(--atlas-ground);
  }

  .atlas-specification,
  .atlas-catalog,
  .atlas-groups,
  .icon-ledger,
  .icon-ledger li,
  .icon-ledger li:nth-child(even) {
    border-color: rgba(246, 235, 212, 0.15);
  }

  .atlas-catalog {
    box-shadow: 0 1.5rem 3.4rem rgba(0, 0, 0, 0.28);
  }

  .atlas-groups button {
    border-color: rgba(246, 235, 212, 0.15);
    color: var(--atlas-muted);
  }

  .atlas-groups button[aria-pressed="true"] {
    color: #071c29;
    background: var(--atlas-brass);
  }

  .icon-well {
    background: rgba(93, 183, 198, 0.1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .atlas-list-enter-active,
  .atlas-list-leave-active {
    transition: none;
  }

  .atlas-back:hover :deep(.ocean-icon),
  .atlas-back:focus-visible :deep(.ocean-icon),
  .icon-ledger li:hover :deep(.ocean-icon),
  .icon-ledger li:focus-within :deep(.ocean-icon) {
    transform: none;
  }
}
</style>
