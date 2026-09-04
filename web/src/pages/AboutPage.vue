<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import { fetchAboutProfile, type AboutProfile } from "../api/about";
import AboutLocationMap from "../components/AboutLocationMap.vue";
import OceanIcon from "../components/OceanIcon.vue";

const fallbackProfile: AboutProfile = {
  id: 1,
  display_name: "王路飞",
  role: "全栈开发者 / 独立创作者",
  headline: "把复杂问题拆成清晰产品，也把沿途的思考写成航海日志。",
  bio: "我关注产品体验、前后端工程与长期可维护的软件设计。工作之外，我会记录技术实践、项目复盘和生活观察，希望这里不仅是一份履历，也是一张持续更新的个人航海图。",
  avatar_url: "/owner-avatar.jpg",
  resume_url: "",
  resume_filename: "",
  status_text: "正在航行，欢迎交流",
  email: null,
  location_name: "中国 · 上海",
  location_longitude: 121.473701,
  location_latitude: 31.230416,
  metrics: [
    { value: "持续", label: "写作状态" },
    { value: "全栈", label: "工程视角" },
    { value: "开放", label: "合作态度" },
  ],
  work_experiences: [
    {
      organization: "独立开发与长期实践",
      role: "产品工程师",
      period: "现在",
    },
  ],
  project_experiences: [
    {
      name: "个人航海日志",
      role: "设计与全栈开发",
      period: "持续维护",
      summary: "一个以航海为叙事线索的个人博客，承载文章、项目复盘与个人档案。",
      link_url: null,
      technologies: ["Vue 3", "TypeScript", "FastAPI", "MySQL"],
    },
  ],
  skills: [
    { name: "Vue", icon_url: "" },
    { name: "TypeScript", icon_url: "" },
    { name: "CSS", icon_url: "" },
    { name: "Vite", icon_url: "" },
    { name: "Python", icon_url: "" },
    { name: "FastAPI", icon_url: "" },
    { name: "SQLAlchemy", icon_url: "" },
    { name: "MySQL", icon_url: "" },
  ],
  social_links: [],
  interests: ["写作", "摄影", "旅行", "开源"],
  site_title: "关于本站",
  site_description:
    "这里是我的长期数字花园。文章不追求即时热度，更在意一次实践真正留下了什么。站点由前后台独立维护，所有公开内容都可以在管理端持续更新。",
  site_launched_at: "持续迭代中",
  site_stack: ["Vue 3", "TypeScript", "FastAPI", "SQLAlchemy", "MySQL"],
  site_repository_url: null,
  updated_at: new Date().toISOString(),
};

const profile = ref<AboutProfile>(fallbackProfile);
const loading = ref(true);
const errorText = ref("");
const mastRoot = ref<HTMLElement | null>(null);
const boardRoot = ref<HTMLElement | null>(null);
const resumePreviewOpen = ref(false);
let revealObserver: IntersectionObserver | undefined;
let activeCard: HTMLElement | null = null;
let tiltFrame = 0;
const revealTimers: number[] = [];

function skillDisplayKey(skill: AboutProfile["skills"][number]) {
  return (skill.icon_url.trim() || skill.name.trim()).toLocaleLowerCase();
}

const uniqueSkills = computed(() => {
  const seen = new Set<string>();
  return profile.value.skills.filter((skill) => {
    const key = skillDisplayKey(skill);
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
});

const profileChips = computed(() => [
  ...profile.value.interests.map((label) => ({ label, tone: "interest" })),
  ...uniqueSkills.value.slice(0, 4).map((skill) => ({ label: skill.name, tone: "skill" })),
]);

const skillRows = computed(() => {
  const midpoint = Math.ceil(uniqueSkills.value.length / 2);
  const first = uniqueSkills.value.slice(0, midpoint);
  const second = uniqueSkills.value.slice(midpoint);
  const fillRow = (skills: typeof first) => {
    if (!skills.length) return [];
    const count = Math.max(6, skills.length);
    const safeCount = skills.length > 1 && count % skills.length === 1 ? count - 1 : count;
    return Array.from({ length: safeCount }, (_, index) => skills[index % skills.length]);
  };
  return [fillRow(first), fillRow(second.length ? second : first)];
});

const coordinateLabel = computed(() => {
  const { location_latitude: latitude, location_longitude: longitude } = profile.value;
  if (latitude === null || longitude === null) return "坐标等待维护";
  return `${latitude >= 0 ? "N" : "S"} ${Math.abs(latitude).toFixed(2)} / ${longitude >= 0 ? "E" : "W"} ${Math.abs(longitude).toFixed(2)}`;
});

const updatedDate = computed(() =>
  new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "long" }).format(
    new Date(profile.value.updated_at),
  ),
);

const hasResume = computed(() => Boolean(profile.value.resume_url.trim()));
const resumeFileName = computed(() => profile.value.resume_filename || `${profile.value.display_name}-简历.pdf`);
const resumeDownloadUrl = computed(() => {
  if (!hasResume.value) return "";
  try {
    const url = new URL(profile.value.resume_url);
    const filename = url.pathname.split("/").pop();
    if (filename && url.pathname.includes("/uploads/resumes/")) {
      return `${url.origin}/api/v1/media/resumes/${encodeURIComponent(filename)}`;
    }
  } catch {
    // 非标准地址直接交给浏览器处理。
  }
  return profile.value.resume_url;
});

function skillMark(skill: string) {
  const ascii = skill.match(/[A-Za-z0-9]+/)?.[0];
  return ascii ? ascii.slice(0, 2).toUpperCase() : skill.slice(0, 1);
}

function handleSkillIconError(event: Event) {
  const image = event.currentTarget as HTMLImageElement;
  image.hidden = true;
  const fallback = image.nextElementSibling as HTMLElement | null;
  if (fallback) fallback.hidden = false;
}

function openResumePreview() {
  if (!hasResume.value) return;
  resumePreviewOpen.value = true;
}

function closeResumePreview() {
  resumePreviewOpen.value = false;
}

function updateMastPerspective(event: PointerEvent) {
  if (event.pointerType === "touch" || !mastRoot.value) return;
  const bounds = mastRoot.value.getBoundingClientRect();
  const x = (event.clientX - bounds.left) / bounds.width - 0.5;
  const y = (event.clientY - bounds.top) / bounds.height - 0.5;
  mastRoot.value.style.setProperty("--mast-center-x", `${(x * 4).toFixed(2)}px`);
  mastRoot.value.style.setProperty("--mast-center-y", `${(y * 3).toFixed(2)}px`);
  mastRoot.value.style.setProperty("--avatar-x", `${(y * -4).toFixed(2)}deg`);
  mastRoot.value.style.setProperty("--avatar-y", `${(x * 5).toFixed(2)}deg`);
  mastRoot.value.style.setProperty("--cloud-left-x", `${(x * -15).toFixed(2)}px`);
  mastRoot.value.style.setProperty("--cloud-left-y", `${(y * -7).toFixed(2)}px`);
  mastRoot.value.style.setProperty("--cloud-right-x", `${(x * 15).toFixed(2)}px`);
  mastRoot.value.style.setProperty("--cloud-right-y", `${(y * 7).toFixed(2)}px`);
}

function resetMastPerspective() {
  if (!mastRoot.value) return;
  [
    "--mast-center-x",
    "--mast-center-y",
    "--cloud-left-x",
    "--cloud-left-y",
    "--cloud-right-x",
    "--cloud-right-y",
  ].forEach((property) => mastRoot.value?.style.setProperty(property, "0px"));
  mastRoot.value.style.setProperty("--avatar-x", "0deg");
  mastRoot.value.style.setProperty("--avatar-y", "0deg");
}

function resetActiveCard() {
  if (!activeCard) return;
  activeCard.style.setProperty("--tilt-x", "0deg");
  activeCard.style.setProperty("--tilt-y", "0deg");
  activeCard.classList.remove("is-tilting");
  activeCard = null;
}

function tiltCard(event: PointerEvent) {
  if (event.pointerType === "touch") return;
  const target = event.target as HTMLElement;
  const card = target.closest<HTMLElement>(".bento-card");
  if (!card || !boardRoot.value?.contains(card)) {
    resetActiveCard();
    return;
  }

  if (activeCard !== card) {
    resetActiveCard();
    activeCard = card;
    card.classList.add("is-tilting");
  }

  window.cancelAnimationFrame(tiltFrame);
  tiltFrame = window.requestAnimationFrame(() => {
    const bounds = card.getBoundingClientRect();
    const x = Math.min(1, Math.max(0, (event.clientX - bounds.left) / bounds.width));
    const y = Math.min(1, Math.max(0, (event.clientY - bounds.top) / bounds.height));
    card.style.setProperty("--tilt-x", `${((0.5 - y) * 4).toFixed(2)}deg`);
    card.style.setProperty("--tilt-y", `${((x - 0.5) * 5).toFixed(2)}deg`);
    card.style.setProperty("--shine-x", `${Math.round(x * bounds.width)}px`);
  });
}

async function loadProfile() {
  loading.value = true;
  errorText.value = "";
  try {
    profile.value = await fetchAboutProfile();
  } catch {
    errorText.value = "关于我资料暂时无法读取，当前展示离线档案。";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadProfile();

  const cards = [...(boardRoot.value?.querySelectorAll<HTMLElement>(".bento-card") ?? [])];
  cards.forEach((card, index) => {
    card.dataset.revealIndex = String(index);
    card.style.setProperty("--reveal-delay", `${index * 55}ms`);
  });

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    cards.forEach((card) => card.classList.add("is-visible", "reveal-complete"));
    return;
  }

  revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const card = entry.target as HTMLElement;
        const revealIndex = Number(card.dataset.revealIndex) || 0;
        card.classList.add("is-visible");
        revealTimers.push(
          window.setTimeout(() => card.classList.add("reveal-complete"), 650 + revealIndex * 55),
        );
        revealObserver?.unobserve(card);
      });
    },
    { threshold: 0.12 },
  );
  cards.forEach((card) => revealObserver?.observe(card));
});

onBeforeUnmount(() => {
  revealObserver?.disconnect();
  revealTimers.forEach((timer) => window.clearTimeout(timer));
  window.cancelAnimationFrame(tiltFrame);
});
</script>

<template>
  <main class="about-page" :aria-busy="loading">
    <p v-if="errorText" class="about-offline-notice" role="status"><OceanIcon name="warning" :size="20" />{{ errorText }}</p>

    <header
      ref="mastRoot"
      class="about-mast"
      @pointermove="updateMastPerspective"
      @pointerleave="resetMastPerspective"
    >
      <div class="mast-chip-cloud mast-chip-cloud-left" aria-label="兴趣标签">
        <span
          v-for="chip in profileChips.slice(0, 4)"
          :key="chip.label"
          :class="`mast-chip mast-chip-${chip.tone}`"
        >
          <i aria-hidden="true"></i>{{ chip.label }}
        </span>
      </div>

      <div class="mast-identity">
        <figure class="mast-avatar">
          <img :src="profile.avatar_url" :alt="`${profile.display_name}的照片`" />
          <i aria-hidden="true"></i>
        </figure>
        <h1>关于我</h1>
        <p>
          <strong>{{ profile.display_name }}</strong><span>/</span>{{ profile.role }}
        </p>
        <small>{{ profile.status_text }}</small>
        <div v-if="hasResume" class="mast-resume-actions" aria-label="简历入口">
          <button type="button" @click="openResumePreview">预览简历</button>
          <a :href="resumeDownloadUrl" :download="resumeFileName"><OceanIcon name="download" :size="18" />下载 PDF</a>
        </div>
      </div>

      <div class="mast-chip-cloud mast-chip-cloud-right" aria-label="能力标签">
        <span
          v-for="chip in profileChips.slice(4, 8)"
          :key="chip.label"
          :class="`mast-chip mast-chip-${chip.tone}`"
        >
          <i aria-hidden="true"></i>{{ chip.label }}
        </span>
      </div>
    </header>

    <section
      ref="boardRoot"
      class="bento-board"
      aria-label="个人档案"
      @pointermove="tiltCard"
      @pointerleave="resetActiveCard"
    >
      <article class="bento-card intro-card card-span-7" style="--card-index: 0">
        <p class="card-kicker">HELLO / PROFILE</p>
        <h2>你好，我是 {{ profile.display_name }}</h2>
        <p class="intro-role">{{ profile.role }}</p>
        <p class="intro-copy">{{ profile.bio }}</p>
        <dl v-if="profile.metrics.length" class="metric-row">
          <div v-for="metric in profile.metrics" :key="`${metric.value}-${metric.label}`">
            <dt>{{ metric.value }}</dt>
            <dd>{{ metric.label }}</dd>
          </div>
        </dl>
      </article>

      <article class="bento-card headline-card card-span-5" style="--card-index: 1">
        <p class="card-kicker">MY COMPASS</p>
        <h2>{{ profile.headline }}</h2>
        <div class="headline-status"><i aria-hidden="true"></i>{{ profile.status_text }}</div>
      </article>

      <article
        class="bento-card skills-card card-span-7"
        style="--card-index: 2"
        aria-label="技术栈，鼠标移入后显示技术名称"
      >
        <header class="card-heading">
          <div>
            <p class="card-kicker">TOOLBOX</p>
            <h2>技术栈</h2>
          </div>
          <span>{{ uniqueSkills.length }} 项技术</span>
        </header>
        <div v-if="uniqueSkills.length" class="skill-showcase">
          <div class="skill-icon-stage" aria-hidden="true">
            <div
              v-for="(row, rowIndex) in skillRows"
              :key="rowIndex"
              class="skill-marquee"
              :class="{ 'is-reverse': rowIndex === 1 }"
            >
              <div class="skill-marquee-track">
                <div
                  v-for="copyIndex in 2"
                  :key="copyIndex"
                  class="skill-marquee-sequence"
                  :aria-hidden="copyIndex === 2"
                >
                  <span
                    v-for="(skill, skillIndex) in row"
                    :key="`${copyIndex}-${skillIndex}-${skill.name}`"
                    class="skill-cube"
                  >
                    <span class="skill-icon-frame">
                      <img
                        v-if="skill.icon_url"
                        :src="skill.icon_url"
                        alt=""
                        @error="handleSkillIconError"
                      />
                      <b :hidden="Boolean(skill.icon_url)">{{ skillMark(skill.name) }}</b>
                    </span>
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div class="skill-tag-stage" aria-label="技术栈名称">
            <span v-for="skill in uniqueSkills" :key="skillDisplayKey(skill)" class="skill-pill">
              <span class="skill-icon-frame">
                <img
                  v-if="skill.icon_url"
                  :src="skill.icon_url"
                  alt=""
                  @error="handleSkillIconError"
                />
                <b :hidden="Boolean(skill.icon_url)">{{ skillMark(skill.name) }}</b>
              </span>
              <strong>{{ skill.name }}</strong>
            </span>
          </div>
        </div>
        <p v-else class="compact-empty">技术栈正在整理中。</p>
      </article>

      <article class="bento-card work-card card-span-5" style="--card-index: 3">
        <header class="card-heading">
          <div>
            <p class="card-kicker">WORK LOG</p>
            <h2>工作经历</h2>
          </div>
          <span>{{ profile.work_experiences.length }} 段</span>
        </header>
        <div v-if="profile.work_experiences.length" class="work-timeline">
          <div
            v-for="(work, index) in profile.work_experiences"
            :key="`${work.organization}-${work.period}`"
            class="work-timeline-item"
          >
            <span class="work-timeline-marker" aria-hidden="true">
              {{ String(index + 1).padStart(2, "0") }}
            </span>
            <div class="work-timeline-body">
              <div class="work-timeline-meta">
                <span>航线记录 {{ String(index + 1).padStart(2, "0") }}</span>
                <time>{{ work.period }}</time>
              </div>
              <strong>{{ work.organization }}</strong>
              <b>{{ work.role }}</b>
            </div>
          </div>
        </div>
        <p v-else class="compact-empty">新的工作经历正在整理中。</p>
      </article>

      <article class="bento-card project-card card-span-6" style="--card-index: 4">
        <header class="card-heading">
          <div>
            <p class="card-kicker">SELECTED BUILDS</p>
            <h2>项目经历</h2>
          </div>
          <span>{{ profile.project_experiences.length }} 个项目</span>
        </header>
        <div v-if="profile.project_experiences.length" class="project-list">
          <article
            v-for="(project, index) in profile.project_experiences"
            :key="`${project.name}-${project.period}`"
          >
            <span class="project-index">{{ String(index + 1).padStart(2, "0") }}</span>
            <div>
              <p v-if="project.period.trim() || project.role.trim()">
                <span v-if="project.period.trim()">{{ project.period }}</span>
                <span v-if="project.period.trim() && project.role.trim()" aria-hidden="true">
                  ·
                </span>
                <span v-if="project.role.trim()">{{ project.role }}</span>
              </p>
              <h3>{{ project.name }}</h3>
              <p class="project-summary">{{ project.summary }}</p>
              <div class="project-tags">
                <span v-for="technology in project.technologies" :key="technology">{{
                  technology
                }}</span>
              </div>
            </div>
            <a
              v-if="project.link_url"
              :href="project.link_url"
              target="_blank"
              rel="noreferrer noopener"
              :aria-label="`打开项目：${project.name}`"
              :title="`打开项目：${project.name}`"
            ><OceanIcon name="external" :size="20" /></a>
          </article>
        </div>
        <p v-else class="compact-empty">代表项目正在整理中。</p>
      </article>

      <article class="bento-card location-card card-span-6" style="--card-index: 5">
        <header class="location-card-heading">
          <div>
            <p class="card-kicker">HOME PORT</p>
            <h2><OceanIcon name="location" :size="24" /><span>我现在住在</span> {{ profile.location_name }}</h2>
          </div>
          <small>{{ coordinateLabel }}</small>
        </header>
        <AboutLocationMap
          :name="profile.location_name"
          :longitude="profile.location_longitude"
          :latitude="profile.location_latitude"
        />
      </article>

      <article class="bento-card site-card card-span-6" style="--card-index: 6">
        <div class="site-stamp" aria-hidden="true">航</div>
        <div>
          <p class="card-kicker">THIS WEBSITE</p>
          <h2>{{ profile.site_title }}</h2>
          <p>{{ profile.site_description }}</p>
          <div class="site-meta">
            <span>启航 · {{ profile.site_launched_at }}</span>
            <span>更新 · {{ updatedDate }}</span>
          </div>
        </div>
        <div class="site-stack" aria-label="本站技术栈">
          <span v-for="item in profile.site_stack" :key="item">{{ item }}</span>
        </div>
      </article>

      <article
        v-if="hasResume"
        class="bento-card resume-card card-span-3"
        style="--card-index: 7"
      >
        <div class="resume-doc-mark" aria-hidden="true">
          <span></span>
          <i></i>
        </div>
        <p class="card-kicker">RESUME</p>
        <h2>简历</h2>
        <p>{{ resumeFileName }}</p>
        <div class="resume-actions">
          <button type="button" @click="openResumePreview">在线预览</button>
          <a :href="resumeDownloadUrl" :download="resumeFileName"><OceanIcon name="download" :size="18" />下载 PDF</a>
        </div>
      </article>

      <article class="bento-card connect-card card-span-3" style="--card-index: 8">
        <p class="card-kicker">KEEP IN TOUCH</p>
        <h2>保持联系</h2>
        <p>{{ profile.status_text }}</p>
        <div class="connect-links">
          <a v-if="profile.email" :href="`mailto:${profile.email}`">邮件</a>
          <a
            v-for="link in profile.social_links"
            :key="link.url"
            :href="link.url"
            target="_blank"
            rel="noreferrer noopener"
          ><OceanIcon name="external" :size="18" />{{ link.platform }}</a>
          <a
            v-if="profile.site_repository_url"
            :href="profile.site_repository_url"
            target="_blank"
            rel="noreferrer noopener"
          ><OceanIcon name="external" :size="18" />本站源码</a>
          <RouterLink to="/articles">阅读文章 <OceanIcon name="next" :size="18" /></RouterLink>
        </div>
      </article>
    </section>

    <Teleport to="body">
      <div
        v-if="resumePreviewOpen && hasResume"
        class="resume-preview-layer"
        role="presentation"
        @click.self="closeResumePreview"
      >
        <section
          class="resume-preview-dialog"
          role="dialog"
          aria-modal="true"
          aria-label="在线预览简历"
        >
          <header>
            <div>
              <p class="card-kicker">RESUME PREVIEW</p>
              <h2>{{ resumeFileName }}</h2>
            </div>
            <button type="button" aria-label="关闭简历预览" @click="closeResumePreview">×</button>
          </header>
          <iframe :src="profile.resume_url" title="在线预览简历"></iframe>
          <footer>
            <a :href="resumeDownloadUrl" :download="resumeFileName"><OceanIcon name="download" :size="18" />下载 PDF</a>
          </footer>
        </section>
      </div>
    </Teleport>

    <footer class="about-footer">
      <span>ABOUT / {{ profile.display_name }}</span>
      <RouterLink to="/"><OceanIcon name="home" :size="18" />返回首页</RouterLink>
    </footer>
  </main>
</template>

<style scoped>
.about-page {
  --board-bg: #edf2f5;
  --card-bg: #ffffff;
  --ink: #102a36;
  --muted: #667780;
  --border: #d8e1e6;
  --sea: #15939b;
  --coral: #ef735b;
  --brass: #f1b94e;
  min-height: 100vh;
  overflow-x: clip;
  padding: 7.2rem 1.25rem 2rem;
  color: var(--ink);
  background: var(--board-bg);
}

.about-offline-notice {
  position: fixed;
  top: 5.4rem;
  left: 50%;
  z-index: 25;
  margin: 0;
  padding: 0.55rem 0.8rem;
  border-radius: 5px;
  color: #fff;
  background: #a04736;
  font-size: 0.74rem;
  transform: translateX(-50%);
}

.about-mast {
  --avatar-x: 0deg;
  --avatar-y: 0deg;
  --cloud-left-x: 0px;
  --cloud-left-y: 0px;
  --cloud-right-x: 0px;
  --cloud-right-y: 0px;
  --mast-center-x: 0px;
  --mast-center-y: 0px;
  display: grid;
  grid-template-columns: minmax(180px, 1fr) auto minmax(180px, 1fr);
  gap: 1.5rem;
  align-items: center;
  width: min(100%, 920px);
  margin: 0 auto 2.8rem;
  perspective: 900px;
}

.mast-identity {
  display: grid;
  justify-items: center;
  min-width: 280px;
  text-align: center;
  transform: translate3d(var(--mast-center-x), var(--mast-center-y), 0);
  transition: transform 260ms ease-out;
}

.mast-avatar {
  position: relative;
  width: 132px;
  aspect-ratio: 1;
  margin: 0 0 0.8rem;
  transform: rotateX(var(--avatar-x)) rotateY(var(--avatar-y));
  transition: transform 260ms cubic-bezier(0.2, 0.75, 0.2, 1);
}

.mast-avatar::before {
  content: "";
  position: absolute;
  inset: -7px;
  border: 1px dashed rgba(16, 42, 54, 0.26);
  border-radius: 50%;
  animation: avatar-orbit 18s linear infinite;
}

.mast-avatar img {
  display: block;
  width: 100%;
  height: 100%;
  border: 5px solid #fff;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 14px 35px rgba(16, 42, 54, 0.16);
}

.mast-avatar > i {
  position: absolute;
  right: 3px;
  bottom: 8px;
  width: 22px;
  height: 22px;
  border: 4px solid var(--board-bg);
  border-radius: 50%;
  background: #32be7b;
}

.mast-identity h1 {
  margin: 0;
  font-size: 2.35rem;
  line-height: 1.2;
  letter-spacing: 0;
}

.mast-identity > p {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  justify-content: center;
  margin: 0.55rem 0 0;
  color: var(--muted);
  font-size: 0.84rem;
}

.mast-identity > p strong {
  color: var(--ink);
}

.mast-identity > small {
  margin-top: 0.5rem;
  color: var(--sea);
  font-size: 0.72rem;
  font-weight: 700;
}

.mast-resume-actions {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  justify-content: center;
  margin-top: 0.85rem;
}

.mast-resume-actions a,
.mast-resume-actions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 32px;
  padding: 0.42rem 0.72rem;
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--ink);
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 6px 16px rgba(16, 42, 54, 0.08);
  cursor: pointer;
  font: inherit;
  font-size: 0.7rem;
  font-weight: 800;
  text-decoration: none;
  transition:
    color 160ms ease,
    border-color 160ms ease,
    background-color 160ms ease,
    transform 180ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.mast-resume-actions button {
  border-color: rgba(21, 147, 155, 0.32);
  color: #fff;
  background: var(--sea);
}

.mast-resume-actions a:hover,
.mast-resume-actions button:hover,
.mast-resume-actions a:focus-visible,
.mast-resume-actions button:focus-visible {
  transform: translateY(-2px);
}

.mast-chip-cloud {
  display: grid;
  gap: 0.45rem;
  transition: transform 300ms cubic-bezier(0.2, 0.75, 0.2, 1);
}

.mast-chip-cloud-left {
  justify-items: end;
  transform: translate3d(var(--cloud-left-x), var(--cloud-left-y), 0) rotate(-1.2deg);
}

.mast-chip-cloud-right {
  justify-items: start;
  transform: translate3d(var(--cloud-right-x), var(--cloud-right-y), 0) rotate(1.2deg);
}

.mast-chip {
  display: inline-flex;
  gap: 0.5rem;
  align-items: center;
  min-height: 30px;
  padding: 0.28rem 0.7rem;
  border: 1px solid var(--border);
  border-radius: 999px;
  color: #354b55;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 3px 12px rgba(16, 42, 54, 0.05);
  font-size: 0.72rem;
  font-weight: 700;
  animation: chip-in 0.5s ease both;
  transition:
    color 180ms ease,
    border-color 180ms ease,
    background-color 180ms ease,
    transform 180ms cubic-bezier(0.2, 0.8, 0.2, 1),
    box-shadow 180ms ease;
}

.mast-chip:hover {
  border-color: color-mix(in srgb, var(--coral) 48%, var(--border));
  color: var(--ink);
  background: #fff;
  box-shadow: 0 8px 18px rgba(16, 42, 54, 0.1);
  transform: translateY(-3px) rotate(-1deg);
}

.mast-chip-skill:hover {
  border-color: color-mix(in srgb, var(--sea) 52%, var(--border));
  transform: translateY(-3px) rotate(1deg);
}

.mast-chip i {
  width: 7px;
  height: 7px;
  border-radius: 2px;
  background: var(--coral);
}

.mast-chip-skill i {
  background: var(--sea);
}

.bento-board {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 0 0.9rem;
  align-items: start;
  width: min(100%, 1160px);
  margin: 0 auto;
  padding: 0 0.75rem;
}

.bento-card {
  --card-rotate: 0deg;
  --card-y: 24px;
  --card-scale: 0.985;
  --shine-x: 50%;
  --tilt-x: 0deg;
  --tilt-y: 0deg;
  position: relative;
  min-width: 0;
  overflow: hidden;
  padding: 1.25rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--card-bg);
  box-shadow: 0 9px 28px rgba(16, 42, 54, 0.055);
  opacity: 0;
  transform: perspective(1000px) translate3d(0, var(--card-y), 0) rotateX(var(--tilt-x))
    rotateY(var(--tilt-y)) rotateZ(var(--card-rotate)) scale(var(--card-scale));
  transform-origin: 50% 50%;
  transition:
    opacity 520ms var(--reveal-delay, 0ms) ease,
    transform 620ms var(--reveal-delay, 0ms) cubic-bezier(0.16, 0.8, 0.22, 1),
    box-shadow 220ms ease,
    border-color 220ms ease;
}

.bento-card::after {
  content: "";
  position: absolute;
  top: -45%;
  bottom: -45%;
  left: -42%;
  z-index: 3;
  width: 26%;
  pointer-events: none;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.44), transparent);
  opacity: 0;
  transform: translateX(var(--shine-x)) rotate(12deg);
  transition: opacity 180ms ease;
}

.bento-card.is-visible {
  --card-y: 0px;
  --card-scale: 1;
  opacity: 1;
}

.bento-card.reveal-complete {
  transition-delay: 0s;
}

.bento-card.is-tilting {
  will-change: transform;
  transition:
    transform 90ms linear,
    box-shadow 220ms ease,
    border-color 220ms ease;
}

.bento-card.is-visible:hover {
  --card-y: -6px;
  z-index: 2;
  border-color: #becbd2;
  box-shadow: 0 20px 44px rgba(16, 42, 54, 0.13);
}

.bento-card.is-tilting::after {
  opacity: 0.22;
}

.card-span-4 {
  grid-column: span 4;
}

.card-span-3 {
  grid-column: span 3;
}

.card-span-5 {
  grid-column: span 5;
}

.card-span-6 {
  grid-column: span 6;
}

.card-span-7 {
  grid-column: span 7;
}

.card-span-8 {
  grid-column: span 8;
}

.intro-card {
  --card-rotate: -0.35deg;
  grid-column: 1 / span 7;
  grid-row: 1;
}

.headline-card {
  --card-rotate: 0.55deg;
  grid-column: 8 / span 5;
  grid-row: 1;
  margin: 1.8rem 0 0 0.25rem;
}

.skills-card {
  --card-rotate: 0.22deg;
  grid-column: 1 / span 6;
  grid-row: 2;
  margin-top: 1.1rem;
}

.work-card {
  --card-rotate: -0.45deg;
  grid-column: 7 / span 6;
  grid-row: 2;
  margin: 0.2rem 0 0 0.45rem;
}

.project-card {
  --card-rotate: -0.65deg;
  grid-column: 2 / span 5;
  grid-row: 3;
  margin-top: 1.65rem;
}

.location-card {
  --card-rotate: 0.42deg;
  grid-column: 7 / span 6;
  grid-row: 3;
  margin-top: 0.6rem;
}

.site-card {
  --card-rotate: -0.28deg;
  grid-column: 1 / span 6;
  grid-row: 4;
  margin-top: 1.25rem;
}

.resume-card {
  --card-rotate: 0.48deg;
  grid-column: 7 / span 3;
  grid-row: 4;
  margin: 2.1rem 0 0 -0.15rem;
}

.connect-card {
  --card-rotate: 0.72deg;
  grid-column: 10 / span 3;
  grid-row: 4;
  align-self: end;
  margin: 0 0 1.2rem -0.35rem;
}

.card-kicker {
  margin: 0;
  color: var(--coral);
  font:
    600 0.64rem "IBM Plex Mono",
    monospace;
  letter-spacing: 0;
}

.bento-card h2 {
  margin: 0.45rem 0 0;
  font-size: 1.65rem;
  line-height: 1.3;
  letter-spacing: 0;
}

.intro-card,
.headline-card {
  min-height: 250px;
}

.intro-card {
  display: flex;
  flex-direction: column;
  color: #f9fbfb;
  background: #155766;
  border-color: #155766;
}

.intro-card .card-kicker {
  color: #8bdad6;
}

.intro-card h2 {
  font-size: 2rem;
}

.intro-role {
  margin: 0.35rem 0 0;
  color: #f1c66e;
  font-weight: 700;
}

.intro-copy {
  max-width: 42rem;
  margin: 0.9rem 0 0;
  color: rgba(249, 251, 251, 0.78);
  font:
    400 0.86rem/1.75 "Noto Sans SC",
    sans-serif;
}

.metric-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin: auto 0 0;
  padding-top: 1rem;
}

.metric-row div {
  display: grid;
  gap: 0.1rem;
}

.metric-row dt {
  font-size: 1.05rem;
  font-weight: 800;
}

.metric-row dd {
  margin: 0;
  color: rgba(249, 251, 251, 0.58);
  font-size: 0.65rem;
}

.headline-card {
  display: flex;
  flex-direction: column;
  background: var(--brass);
  border-color: var(--brass);
}

.headline-card .card-kicker {
  color: rgba(16, 42, 54, 0.58);
}

.headline-card h2 {
  max-width: 29rem;
  font-size: 1.75rem;
}

.headline-status {
  display: inline-flex;
  gap: 0.5rem;
  align-items: center;
  margin-top: auto;
  font-size: 0.75rem;
  font-weight: 700;
}

.headline-status i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #2d9564;
  box-shadow: 0 0 0 5px rgba(45, 149, 100, 0.13);
  animation: status-pulse 2.2s ease-in-out infinite;
}

.card-heading,
.location-card-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.card-heading > span,
.location-card-heading > small {
  flex: 0 0 auto;
  color: var(--muted);
  font:
    600 0.64rem "IBM Plex Mono",
    monospace;
}

.skills-card,
.work-card {
  min-height: 330px;
}

.skills-card {
  outline: none;
}

.skills-card:focus-visible {
  border-color: var(--sea);
  box-shadow:
    0 0 0 3px rgba(21, 147, 155, 0.14),
    0 18px 40px rgba(16, 42, 54, 0.11);
}

.skill-showcase {
  position: relative;
  height: 238px;
  margin: 0.9rem -1.25rem -1.25rem;
  overflow: hidden;
}

.skill-icon-stage,
.skill-tag-stage {
  position: absolute;
  inset: 0;
  transition:
    opacity 280ms ease,
    transform 360ms cubic-bezier(0.2, 0.78, 0.2, 1);
}

.skill-icon-stage {
  display: grid;
  gap: 0.75rem;
  align-content: center;
  opacity: 1;
  transform: translateY(0) scale(1);
}

.skill-marquee {
  --marquee-direction: normal;
  --marquee-duration: 22s;
  display: flex;
  width: 100%;
  overflow: hidden;
  mask-image: linear-gradient(90deg, transparent, #000 7%, #000 93%, transparent);
}

.skill-marquee.is-reverse {
  --marquee-direction: reverse;
  --marquee-duration: 27s;
}

.skill-marquee-track {
  display: flex;
  flex: 0 0 max-content;
  width: max-content;
  animation: skill-marquee var(--marquee-duration) linear infinite var(--marquee-direction);
  will-change: transform;
}

.skill-marquee-sequence {
  display: flex;
  flex: 0 0 auto;
  gap: 0.8rem;
  padding-right: 0.8rem;
}

.skill-cube {
  display: grid;
  flex: 0 0 82px;
  place-items: center;
  width: 82px;
  height: 82px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  box-shadow: none;
}

.skill-icon-frame {
  display: grid;
  place-items: center;
  width: 58px;
  height: 58px;
  overflow: hidden;
  border-radius: 7px;
  background: transparent;
}

.skill-icon-frame img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.skill-icon-frame b {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  color: var(--sea-deep);
  background: rgba(21, 147, 155, 0.08);
  font:
    700 0.82rem "IBM Plex Mono",
    monospace;
}

.skill-tag-stage {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  align-content: flex-start;
  padding: 0.55rem 1.25rem 1.25rem;
  overflow-y: auto;
  opacity: 0;
  pointer-events: none;
  transform: translateY(12px) scale(0.98);
  scrollbar-width: thin;
}

.skill-pill {
  display: inline-flex;
  gap: 0.5rem;
  align-items: center;
  min-height: 38px;
  padding: 0.3rem 0.75rem 0.3rem 0.35rem;
  border: 1px solid #dce5ea;
  border-radius: 999px;
  color: #354b55;
  background: #f8fafb;
  box-shadow: 0 3px 9px rgba(16, 42, 54, 0.06);
  font-size: 0.76rem;
  transition:
    color 180ms ease,
    border-color 180ms ease,
    background-color 180ms ease,
    transform 180ms ease;
}

.skill-pill .skill-icon-frame {
  width: 28px;
  height: 28px;
  border-radius: 50%;
}

.skill-pill .skill-icon-frame b {
  font-size: 0.54rem;
}

.skill-pill:hover {
  border-color: rgba(21, 147, 155, 0.42);
  color: var(--ink);
  background: #fff;
  transform: translateY(-2px);
}

.skills-card:hover .skill-icon-stage {
  opacity: 0;
  pointer-events: none;
  transform: translateY(-10px) scale(0.97);
}

.skills-card:hover .skill-tag-stage {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0) scale(1);
}

.skills-card:hover .skill-marquee-track {
  animation-play-state: paused;
}

.work-timeline {
  position: relative;
  display: grid;
  max-height: 248px;
  margin-top: 1rem;
  overflow-x: hidden;
  overflow-y: auto;
  scrollbar-width: thin;
}

.work-timeline-item {
  position: relative;
  display: grid;
  grid-template-columns: 2rem minmax(0, 1fr);
  gap: 0.8rem;
  min-width: 0;
  padding: 0.95rem 0;
  border-top: 1px solid var(--border);
}

.work-timeline-item:not(:last-child)::after {
  position: absolute;
  top: 1.9rem;
  bottom: -1.9rem;
  left: 0.95rem;
  width: 1px;
  background: color-mix(in srgb, var(--sea) 64%, var(--border));
  content: "";
  opacity: 0.62;
}

.work-timeline-item:last-child {
  border-bottom: 1px solid var(--border);
}

.work-timeline-marker {
  position: relative;
  z-index: 1;
  display: grid;
  width: 1.9rem;
  height: 1.9rem;
  place-items: center;
  border: 1px solid rgba(198, 79, 58, 0.58);
  border-radius: 50%;
  color: var(--coral);
  background: var(--card-bg);
  font:
    600 0.62rem "IBM Plex Mono",
    monospace;
  transition: color 180ms ease, background-color 180ms ease, border-color 180ms ease;
}

.work-timeline-body {
  display: grid;
  align-content: center;
  gap: 0.3rem;
  min-width: 0;
}

.work-timeline-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem 0.8rem;
  align-items: baseline;
  justify-content: space-between;
  color: var(--muted);
  font:
    600 0.58rem "IBM Plex Mono",
    monospace;
  letter-spacing: 0.02em;
}

.work-timeline-meta time {
  color: var(--sea);
  white-space: nowrap;
}

.work-timeline-body > strong {
  overflow: hidden;
  color: var(--ink);
  font-size: 0.82rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.work-timeline-body > b {
  color: var(--sea);
  font-size: 0.7rem;
  font-weight: 700;
}

.work-timeline-item:hover {
  transform: none;
}

.work-timeline-item:hover .work-timeline-marker {
  color: var(--ink);
  border-color: var(--sea);
  background: #e4f4f1;
}

.work-timeline-item:hover .work-timeline-body > strong {
  color: var(--sea);
}

.project-card,
.location-card {
  min-height: 330px;
}

.project-list {
  display: grid;
  gap: 0.35rem;
  max-height: 248px;
  margin-top: 1rem;
  padding: 0 0.45rem 0.1rem 0;
  overflow-x: hidden;
  overflow-y: auto;
  scrollbar-gutter: stable;
  scrollbar-width: thin;
}

.project-list > article {
  position: relative;
  isolation: isolate;
  display: grid;
  grid-template-columns: 2rem minmax(0, 1fr) auto;
  gap: 0.7rem;
  min-width: 0;
  box-sizing: border-box;
  overflow: hidden;
  padding: 0.85rem 0.6rem 0.85rem 0.5rem;
  border-top: 1px solid var(--border);
  border-radius: 6px;
  transform: translate3d(0, 0, 0);
  transition:
    background-color 200ms ease,
    box-shadow 200ms ease,
    transform 160ms cubic-bezier(0.22, 1, 0.36, 1);
}

.project-list > article::before {
  content: "";
  position: absolute;
  inset: 0.2rem 0;
  z-index: -1;
  border-radius: 8px;
  background:
    radial-gradient(circle at 18% 12%, rgba(236, 111, 83, 0.12), transparent 36%),
    linear-gradient(100deg, rgba(244, 247, 248, 0.92), rgba(232, 241, 245, 0.64));
  opacity: 0;
  transform: scaleX(0.985);
  transform-origin: left center;
  transition:
    opacity 180ms ease,
    transform 180ms cubic-bezier(0.22, 1, 0.36, 1);
}

@media (hover: hover) and (pointer: fine) {
  .project-list > article:hover {
    background: transparent;
    box-shadow: inset 3px 0 0 rgba(236, 111, 83, 0.7);
    transform: translate3d(3px, -1px, 0);
  }

  .project-list > article:hover::before {
    opacity: 1;
    transform: scaleX(1);
  }
}

.project-list > article > div {
  min-width: 0;
}

.project-index,
.project-list > article > div > p:first-child {
  color: var(--coral);
  font:
    600 0.62rem "IBM Plex Mono",
    monospace;
}

.project-list h3 {
  margin: 0.3rem 0 0;
  font-size: 1rem;
}

.project-list > article > div > p:first-child,
.project-summary {
  margin: 0;
}

.project-summary {
  margin-top: 0.35rem;
  color: var(--muted);
  font:
    400 0.7rem/1.65 "Noto Sans SC",
    sans-serif;
  overflow-wrap: anywhere;
}

.project-list > article > a {
  color: var(--sea);
  text-decoration: none;
}

.project-tags,
.site-stack,
.connect-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.project-tags {
  margin-top: 0.55rem;
  min-width: 0;
  overflow: hidden;
}

.project-tags span,
.site-stack span {
  max-width: 100%;
  padding: 0.25rem 0.45rem;
  overflow: hidden;
  border-radius: 4px;
  background: #eef3f5;
  font-size: 0.6rem;
  font-weight: 700;
  text-overflow: ellipsis;
}

.location-card {
  display: grid;
  grid-template-rows: auto minmax(190px, 1fr);
  gap: 0.7rem;
  padding: 0.9rem;
}

.location-card-heading h2 {
  display: flex;
  gap: 0.45rem;
  align-items: center;
  font-size: 1.2rem;
}

.location-card-heading h2 span {
  font-size: inherit;
  font-weight: 400;
}

.site-card,
.connect-card {
  min-height: 235px;
}

.site-card {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) minmax(160px, 0.55fr);
  gap: 1.2rem;
  align-items: center;
  background: #dcece8;
  border-color: #cadfd9;
}

.site-stamp {
  display: grid;
  place-items: center;
  width: 64px;
  aspect-ratio: 1;
  border: 1px solid rgba(16, 42, 54, 0.25);
  border-radius: 50%;
  color: var(--sea);
  font-size: 1.8rem;
  font-weight: 800;
  transform: rotate(-7deg);
  transition:
    color 240ms ease,
    background-color 240ms ease,
    transform 420ms cubic-bezier(0.16, 0.85, 0.2, 1);
}

.site-card:hover .site-stamp {
  color: #fff;
  background: var(--sea);
  transform: rotate(8deg) scale(1.06);
}

.site-card > div:nth-child(2) > p:not(.card-kicker) {
  max-width: 38rem;
  margin: 0.7rem 0 0;
  color: #50676f;
  font:
    400 0.76rem/1.7 "Noto Sans SC",
    sans-serif;
}

.site-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
  margin-top: 0.9rem;
  color: var(--sea);
  font:
    600 0.62rem "IBM Plex Mono",
    monospace;
}

.site-stack {
  align-content: center;
}

.site-stack span {
  color: #fff;
  background: var(--sea);
}

.resume-card {
  min-height: 250px;
  color: #f9fbfb;
  background:
    linear-gradient(150deg, rgba(239, 115, 91, 0.14), transparent 46%),
    #176b73;
  border-color: #176b73;
}

.resume-card .card-kicker {
  color: #f1c66e;
}

.resume-doc-mark {
  position: absolute;
  top: 1rem;
  right: 1rem;
  display: grid;
  place-items: center;
  width: 56px;
  height: 72px;
  border: 1px solid rgba(249, 251, 251, 0.36);
  border-radius: 6px 6px 12px;
  background: rgba(249, 251, 251, 0.12);
  transform: rotate(5deg);
  transition:
    transform 320ms cubic-bezier(0.2, 0.8, 0.2, 1),
    background-color 220ms ease;
}

.resume-doc-mark::before {
  content: "";
  position: absolute;
  top: -1px;
  right: -1px;
  border-top: 18px solid rgba(249, 251, 251, 0.76);
  border-left: 18px solid transparent;
  border-radius: 0 6px 0 0;
}

.resume-doc-mark span,
.resume-doc-mark i {
  display: block;
  width: 26px;
  height: 2px;
  border-radius: 999px;
  background: rgba(249, 251, 251, 0.72);
}

.resume-doc-mark i {
  width: 18px;
  margin-top: -0.9rem;
}

.resume-card:hover .resume-doc-mark {
  background: rgba(249, 251, 251, 0.18);
  transform: rotate(-4deg) translateY(-3px);
}

.resume-card h2 {
  margin-top: 2.1rem;
}

.resume-card > p:not(.card-kicker) {
  max-width: 11rem;
  margin: 0.55rem 0 0;
  overflow: hidden;
  color: rgba(249, 251, 251, 0.72);
  font-size: 0.72rem;
  line-height: 1.6;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.resume-actions {
  display: grid;
  gap: 0.55rem;
  margin-top: 1.35rem;
}

.resume-actions a,
.resume-actions button,
.resume-preview-dialog footer a,
.resume-preview-dialog header button {
  border: 0;
  border-radius: 5px;
  cursor: pointer;
  font: inherit;
  text-decoration: none;
}

.resume-actions a,
.resume-actions button,
.resume-preview-dialog footer a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0.48rem 0.72rem;
  font-size: 0.72rem;
  font-weight: 800;
  transition:
    color 160ms ease,
    background-color 160ms ease,
    transform 180ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.resume-actions button {
  color: var(--ink);
  background: var(--brass);
}

.resume-actions a {
  color: #f9fbfb;
  background: rgba(249, 251, 251, 0.14);
}

.resume-actions a:hover,
.resume-actions button:hover,
.resume-actions a:focus-visible,
.resume-actions button:focus-visible {
  transform: translateY(-2px);
}

.resume-preview-layer {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: grid;
  place-items: center;
  padding: 1.25rem;
  background: rgba(8, 27, 35, 0.72);
  backdrop-filter: blur(14px);
  animation: preview-fade 180ms ease both;
}

.resume-preview-dialog {
  --preview-ink: #102a36;
  --preview-muted: #667780;
  --preview-border: #d8e1e6;
  --preview-sea: #15939b;
  --preview-coral: #ef735b;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  width: min(100%, 980px);
  height: min(88vh, 780px);
  overflow: hidden;
  border: 1px solid rgba(249, 251, 251, 0.16);
  border-radius: 8px;
  background: #f7fafb;
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.34);
  animation: preview-rise 220ms cubic-bezier(0.16, 0.85, 0.2, 1) both;
}

.resume-preview-dialog header,
.resume-preview-dialog footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 1rem;
  background: #fff;
}

.resume-preview-dialog header {
  color: var(--preview-ink);
  border-bottom: 1px solid var(--preview-border);
}

.resume-preview-dialog header .card-kicker {
  color: var(--preview-coral);
}

.resume-preview-dialog header h2 {
  margin: 0.25rem 0 0;
  color: var(--preview-ink);
  font-size: 1rem;
}

.resume-preview-dialog header button {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 34px;
  height: 34px;
  color: var(--preview-ink);
  background: #edf2f5;
  font-size: 1.2rem;
  line-height: 1;
}

.resume-preview-dialog iframe {
  width: 100%;
  height: 100%;
  border: 0;
  background: #dce5ea;
}

.resume-preview-dialog footer {
  justify-content: flex-end;
  color: var(--preview-ink);
  border-top: 1px solid var(--preview-border);
}

.resume-preview-dialog footer a {
  color: #fff;
  background: var(--preview-sea);
}

.connect-card {
  display: flex;
  flex-direction: column;
  color: #f8fbfc;
  background: var(--ink);
  border-color: var(--ink);
}

.connect-card .card-kicker {
  color: #72d0cb;
}

.connect-card > p:not(.card-kicker) {
  margin: 0.65rem 0 0;
  color: rgba(248, 251, 252, 0.62);
  font-size: 0.75rem;
}

.connect-links {
  margin-top: auto;
  padding-top: 1rem;
}

.connect-links a {
  display: inline-flex;
  gap: 0.28rem;
  align-items: center;
  padding: 0.42rem 0.6rem;
  border: 1px solid rgba(248, 251, 252, 0.28);
  border-radius: 4px;
  color: #f8fbfc;
  font-size: 0.68rem;
  text-decoration: none;
  transition:
    color 160ms ease,
    background 160ms ease;
}

.connect-links a:hover,
.connect-links a:focus-visible {
  color: var(--ink);
  background: var(--brass);
}

.compact-empty {
  display: grid;
  place-items: center;
  min-height: 180px;
  margin: 1rem 0 0;
  color: var(--muted);
  font-size: 0.75rem;
}

.about-footer {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  width: min(100%, 1160px);
  margin: 1.2rem auto 0;
  color: var(--muted);
  font:
    600 0.64rem "IBM Plex Mono",
    monospace;
}

.about-footer a {
  color: var(--ink);
  text-decoration: none;
}

@keyframes avatar-orbit {
  to {
    transform: rotate(360deg);
  }
}

@keyframes chip-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
}

@keyframes detail-in {
  from {
    opacity: 0;
    transform: translateY(-5px) scaleY(0.96);
  }
}

@keyframes status-pulse {
  50% {
    box-shadow: 0 0 0 8px rgba(45, 149, 100, 0.05);
    transform: scale(1.08);
  }
}

@keyframes skill-marquee {
  to {
    transform: translateX(-50%);
  }
}

@keyframes preview-fade {
  from {
    opacity: 0;
  }
}

@keyframes preview-rise {
  from {
    opacity: 0;
    transform: translateY(18px) scale(0.98);
  }
}

@media (max-width: 900px) {
  .about-mast {
    grid-template-columns: 1fr auto 1fr;
    gap: 0.7rem;
  }

  .mast-identity {
    min-width: 240px;
  }

  .intro-card,
  .headline-card,
  .skills-card,
  .work-card,
  .project-card,
  .location-card,
  .site-card,
  .resume-card,
  .connect-card {
    grid-row: auto;
    align-self: auto;
    margin: 0.7rem 0 0;
  }

  .card-span-4,
  .card-span-3,
  .card-span-5,
  .card-span-6,
  .card-span-7,
  .card-span-8 {
    grid-column: span 6;
  }

  .site-card {
    grid-template-columns: 64px minmax(0, 1fr);
  }

  .site-stack {
    grid-column: 2;
  }
}

@media (max-width: 680px) {
  .about-page {
    padding: 6.4rem 0.65rem 1.25rem;
  }

  .about-mast {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.65rem;
    margin-bottom: 1.25rem;
  }

  .mast-identity {
    grid-column: 1 / -1;
    grid-row: 1;
    min-width: 0;
  }

  .mast-avatar {
    width: 108px;
  }

  .mast-identity h1 {
    font-size: 2rem;
  }

  .mast-chip-cloud {
    grid-row: 2;
    align-content: start;
  }

  .mast-chip-cloud-left {
    justify-items: end;
  }

  .mast-chip {
    max-width: 100%;
    min-height: 28px;
    font-size: 0.66rem;
  }

  .bento-board {
    grid-template-columns: 1fr;
    gap: 0.7rem;
    padding: 0;
  }

  .card-span-4,
  .card-span-3,
  .card-span-5,
  .card-span-6,
  .card-span-7,
  .card-span-8 {
    grid-column: auto;
  }

  .intro-card,
  .headline-card,
  .skills-card,
  .work-card,
  .project-card,
  .location-card,
  .site-card,
  .resume-card,
  .connect-card {
    --card-rotate: 0deg;
    margin: 0;
  }

  .intro-card,
  .headline-card,
  .site-card,
  .resume-card,
  .connect-card {
    min-height: 220px;
  }

  .intro-card h2 {
    font-size: 1.65rem;
  }

  .headline-card h2 {
    font-size: 1.5rem;
  }

  .skills-card,
  .work-card,
  .project-card,
  .location-card {
    min-height: 310px;
  }

  .skill-showcase {
    height: 220px;
  }

  .site-card {
    grid-template-columns: 52px minmax(0, 1fr);
  }

  .site-stamp {
    width: 48px;
    font-size: 1.25rem;
  }

  .site-stack {
    grid-column: 1 / -1;
  }

  .resume-preview-layer {
    padding: 0.65rem;
  }

  .resume-preview-dialog {
    height: 90vh;
  }
}

@media (max-width: 380px) {
  .mast-chip-cloud-right {
    justify-items: end;
  }

  .mast-chip-cloud-left {
    justify-items: start;
  }

  .mast-chip {
    width: 100%;
  }

  .location-card-heading {
    display: grid;
  }
}

@media (hover: none) {
  .bento-card.is-visible:hover {
    --card-y: 0px;
  }

  .project-list > article:hover {
    box-shadow: none;
    transform: none;
  }

  .site-card:hover .site-stamp {
    color: var(--sea);
    background: transparent;
    transform: rotate(-7deg);
  }

  .resume-card:hover .resume-doc-mark {
    transform: rotate(5deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .mast-avatar::before,
  .mast-chip,
  .bento-card,
  .headline-status i,
  .resume-preview-layer,
  .resume-preview-dialog {
    animation: none;
  }

  .bento-card {
    opacity: 1;
    transform: none;
    transition: none;
  }

  .mast-identity,
  .mast-avatar,
  .mast-chip-cloud,
  .skill-icon-stage,
  .skill-tag-stage,
  .skill-pill,
  .site-stamp,
  .resume-doc-mark,
  .mast-resume-actions a,
  .mast-resume-actions button,
  .resume-actions a,
  .resume-actions button,
  .work-timeline-item,
  .work-timeline-body,
  .work-timeline-marker,
  .project-list > article,
  .project-list > article::before {
    transition: none;
  }

  .mast-identity,
  .mast-avatar,
  .mast-chip-cloud {
    transform: none;
  }

  .bento-card::after {
    display: none;
  }

  .skill-marquee-track {
    animation: none;
  }
}
</style>
