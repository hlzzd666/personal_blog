<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  Download,
  FileText,
  Mail,
  Pause,
  Play,
  X,
  Compass,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Code2,
  MapPin,
  QrCode,
  ExternalLink,
} from "lucide-vue-next";
import { fetchAboutProfile, type AboutProfile } from "../api/about";
import AboutLocationMap from "../components/AboutLocationMap.vue";
import { useAboutMotion } from "../composables/useAboutMotion";

const emptyProfile: AboutProfile = {
  id: 0,
  display_name: "",
  role: "",
  headline: "",
  bio: "",
  avatar_url: "",
  resume_url: "",
  resume_filename: "",
  status_text: "",
  email: null,
  location_name: "",
  location_longitude: null,
  location_latitude: null,
  metrics: [],
  work_experiences: [],
  project_experiences: [],
  skills: [],
  social_links: [],
  interests: [],
  site_title: "",
  site_description: "",
  site_launched_at: "",
  site_stack: [],
  site_repository_url: null,
  updated_at: "",
};

const profile = ref<AboutProfile>(emptyProfile);
const loading = ref(true);
const errorText = ref("");
const pageRoot = ref<HTMLElement | null>(null);
const heroRoot = ref<HTMLElement | null>(null);
const selectedProject = ref(0);
const showQr = ref(false);
const resumeDialog = ref<HTMLDialogElement | null>(null);
const resumePreviewOpen = ref(false);
const avatarUnavailable = ref(false);
const heroVisible = ref(true);
const documentVisible = ref(true);
const motionPaused = ref(false);
const reducedMotion = ref(false);
const compactViewport = ref(false);

const baseUrl = import.meta.env.BASE_URL;
const contactQrUrl = `${baseUrl}assets/d75239bce323589ed27f5a4be20c80f7.jpg`;
const motionActive = computed(
  () => !reducedMotion.value && !motionPaused.value && documentVisible.value,
);
let heroObserver: IntersectionObserver | undefined;
let motionPreference: MediaQueryList | undefined;
let compactPreference: MediaQueryList | undefined;
const { refresh: refreshMotion } = useAboutMotion(pageRoot, motionActive);
let pointerFrame = 0;
let disposed = false;

const uniqueSkills = computed(() => {
  const names = new Set<string>();
  return profile.value.skills.filter((skill) => {
    const name = skill.name.trim().toLocaleLowerCase();
    if (!name || names.has(name)) return false;
    names.add(name);
    return true;
  });
});
const hasResume = computed(() => Boolean(profile.value.resume_url.trim()));
const resumeFileName = computed(
  () => profile.value.resume_filename || `${profile.value.display_name}-简历.pdf`,
);
const resumeDownloadUrl = computed(() => {
  if (!hasResume.value) return "";
  try {
    const url = new URL(profile.value.resume_url);
    const filename = url.pathname.split("/").pop();
    if (filename && url.pathname.includes("/uploads/resumes/"))
      return `${url.origin}/api/v1/media/resumes/${encodeURIComponent(filename)}`;
  } catch {
    /* 相对地址由浏览器按站点路径解析。 */
  }
  return profile.value.resume_url;
});
const coordinateLabel = computed(() => {
  const { location_latitude: latitude, location_longitude: longitude } = profile.value;
  if (latitude === null || longitude === null) return "";
  return `${latitude >= 0 ? "N" : "S"} ${Math.abs(latitude).toFixed(2)} / ${longitude >= 0 ? "E" : "W"} ${Math.abs(longitude).toFixed(2)}`;
});
const updatedDate = computed(() => {
  const date = new Date(profile.value.updated_at);
  return Number.isNaN(date.getTime())
    ? ""
    : new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "long" }).format(date);
});

const activeProject = computed(() => profile.value.project_experiences[selectedProject.value]);
const normalizeTechnology = (value: string) => value.toLowerCase().replace(/[\s._-]|\d+/g, "");
const activeTechnologies = computed(
  () => new Set((activeProject.value?.technologies ?? []).map(normalizeTechnology)),
);
function isRelatedSkill(name: string) {
  return activeTechnologies.value.has(normalizeTechnology(name));
}
function selectProject(index: number, focus = false) {
  const count = profile.value.project_experiences.length;
  if (!count) return;
  selectedProject.value = (index + count) % count;
  void nextTick(() => {
    const tab = pageRoot.value?.querySelector<HTMLButtonElement>(
      `#project-tab-${selectedProject.value}`,
    );
    if (!tab) return;
    if (focus) tab.focus({ preventScroll: true });
    const list = tab.parentElement;
    if (!list || list.scrollWidth <= list.clientWidth) return;
    const bounds = list.getBoundingClientRect();
    const target = tab.getBoundingClientRect();
    const offset =
      target.left < bounds.left
        ? target.left - bounds.left
        : target.right > bounds.right
          ? target.right - bounds.right
          : 0;
    list.scrollBy({ left: offset, behavior: motionActive.value ? "smooth" : "instant" });
  });
}
function projectKeydown(event: KeyboardEvent, index: number) {
  const count = profile.value.project_experiences.length;
  const destination =
    event.key === "ArrowDown" || event.key === "ArrowRight"
      ? (index + 1) % count
      : event.key === "ArrowUp" || event.key === "ArrowLeft"
        ? (index - 1 + count) % count
        : event.key === "Home"
          ? 0
          : event.key === "End"
            ? count - 1
            : null;
  if (destination === null) return;
  event.preventDefault();
  selectProject(destination, true);
}
function updateCardPerspective(event: PointerEvent) {
  const surface = event.currentTarget as HTMLElement;
  if (!motionActive.value || event.pointerType !== "mouse") return;
  const rect = surface.getBoundingClientRect();
  surface.style.setProperty(
    "--card-x",
    `${((event.clientX - rect.left) / rect.width - 0.5) * 4}deg`,
  );
  surface.style.setProperty(
    "--card-y",
    `${((event.clientY - rect.top) / rect.height - 0.5) * -4}deg`,
  );
}
function resetCardPerspective(event: PointerEvent) {
  const surface = event.currentTarget as HTMLElement;
  surface.style.setProperty("--card-x", "0deg");
  surface.style.setProperty("--card-y", "0deg");
}

function handleAvatarError(event: Event) {
  const image = event.currentTarget as HTMLImageElement;
  if (image.dataset.fallback) avatarUnavailable.value = true;
  else {
    image.dataset.fallback = "true";
    image.src = `${baseUrl}owner-avatar.jpg`;
  }
}
function handleSkillIconError(event: Event) {
  (event.currentTarget as HTMLImageElement).hidden = true;
}
function openResumePreview() {
  if (!hasResume.value) return;
  resumePreviewOpen.value = true;
  resumeDialog.value?.showModal();
}
function closeResumePreview() {
  resumeDialog.value?.close();
}
function resetPerspective() {
  window.cancelAnimationFrame(pointerFrame);
  heroRoot.value?.style.setProperty("--pointer-x", "0px");
  heroRoot.value?.style.setProperty("--pointer-y", "0px");
}
function updatePerspective(event: PointerEvent) {
  if (!motionActive.value || event.pointerType !== "mouse" || !heroRoot.value) return;
  window.cancelAnimationFrame(pointerFrame);
  pointerFrame = window.requestAnimationFrame(() => {
    if (!heroRoot.value) return;
    const bounds = heroRoot.value.getBoundingClientRect();
    heroRoot.value.style.setProperty(
      "--pointer-x",
      `${(((event.clientX - bounds.left) / bounds.width - 0.5) * -12).toFixed(2)}px`,
    );
    heroRoot.value.style.setProperty(
      "--pointer-y",
      `${(((event.clientY - bounds.top) / bounds.height - 0.5) * -8).toFixed(2)}px`,
    );
  });
}
function toggleMotion() {
  motionPaused.value = !motionPaused.value;
  resetPerspective();
}
function syncMotionPreference() {
  reducedMotion.value = motionPreference?.matches ?? false;
  resetPerspective();
}
function syncCompactViewport() {
  compactViewport.value = compactPreference?.matches ?? false;
}
function handleVisibility() {
  documentVisible.value = !document.hidden;
  resetPerspective();
}
async function loadProfile() {
  loading.value = true;
  errorText.value = "";
  try {
    const result = await fetchAboutProfile();
    if (disposed) return;
    profile.value = result;
    selectedProject.value = 0;
    avatarUnavailable.value = false;
  } catch {
    if (!disposed) errorText.value = "个人资料暂时无法加载，请稍后重试。";
  } finally {
    if (!disposed) {
      loading.value = false;
      await nextTick();
      if (!disposed) {
        void refreshMotion();
      }
    }
  }
}
onMounted(() => {
  motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
  syncMotionPreference();
  motionPreference.addEventListener("change", syncMotionPreference);
  compactPreference = window.matchMedia("(max-width: 650px)");
  syncCompactViewport();
  compactPreference.addEventListener("change", syncCompactViewport);
  documentVisible.value = !document.hidden;
  document.addEventListener("visibilitychange", handleVisibility);
  if (typeof IntersectionObserver !== "undefined")
    heroObserver = new IntersectionObserver(([entry]) => {
      heroVisible.value = Boolean(entry?.isIntersecting);
    });
  if (heroRoot.value) heroObserver?.observe(heroRoot.value);
  void loadProfile();
});
onBeforeUnmount(() => {
  disposed = true;
  heroObserver?.disconnect();
  motionPreference?.removeEventListener("change", syncMotionPreference);
  compactPreference?.removeEventListener("change", syncCompactViewport);
  document.removeEventListener("visibilitychange", handleVisibility);
  window.cancelAnimationFrame(pointerFrame);
  resumeDialog.value?.close();
});
</script>

<template>
  <main
    ref="pageRoot"
    class="about-page"
    :class="{ 'motion-paused': !motionActive }"
    :aria-busy="loading"
  >
    <header
      ref="heroRoot"
      class="night-hero"
      :class="{ 'is-offscreen': !heroVisible }"
      data-about-scene
      @pointermove="updatePerspective"
      @pointerleave="resetPerspective"
    >
      <div class="hero-seascape" aria-hidden="true">
        <img
          :src="`${baseUrl}about/night-sea.webp`"
          alt=""
          width="1536"
          height="1024"
          fetchpriority="high"
        />
      </div>
      <div class="hero-veil" aria-hidden="true"></div>
      <div class="hero-inner about-width">
        <div class="hero-copy">
          <div class="hero-identity">
            <img
              v-if="profile.avatar_url && !avatarUnavailable"
              class="hero-avatar"
              :src="profile.avatar_url"
              :alt="`${profile.display_name}的头像`"
              width="64"
              height="64"
              @error="handleAvatarError"
            />
            <div>
              <p class="identity-caption">ABOUT / 夜航手记</p>
              <p v-if="!loading && profile.role" class="hero-role">{{ profile.role }}</p>
            </div>
          </div>
          <h1 v-if="!loading && profile.display_name">
            你好，我是<br /><span>{{ profile.display_name }}。</span>
          </h1>
          <h1 v-else>关于我</h1>
          <p class="hero-headline">{{ loading ? "正在展开个人航海日志。" : profile.headline }}</p>
          <p v-if="profile.status_text && !loading" class="sailing-status">
            <span aria-hidden="true"></span>{{ profile.status_text }}
          </p>
          <div class="hero-actions">
            <a class="button-brass" href="#about-contact"><Mail :size="18" aria-hidden="true" />联系我<ArrowUpRight
              :size="17"
              aria-hidden="true"
            /></a><button
              v-if="hasResume && !loading"
              class="text-action"
              type="button"
              @click="openResumePreview"
            >
              <FileText :size="18" aria-hidden="true" />预览简历<ArrowRight
                :size="18"
                aria-hidden="true"
              />
            </button>
          </div>
          <p v-if="errorText" class="profile-notice" role="status">
            {{ errorText }}<button type="button" @click="loadProfile">重新加载</button>
          </p>
        </div>
      </div>
      <div class="hero-workbench" aria-hidden="true">
        <div class="workbench-float">
          <img
            :src="`${baseUrl}about/night-workbench.webp`"
            alt=""
            width="1536"
            height="1024"
            fetchpriority="high"
          />
        </div>
      </div>
      <div class="hero-footer about-width">
        <a class="scroll-cue" href="#about-projects"><span class="scroll-line" aria-hidden="true"></span>向下翻开我的航海日志<ArrowDown
          :size="15"
          aria-hidden="true"
        /></a><span class="hero-side-note" aria-hidden="true">KEEP EXPLORING<br />ALWAYS CURIOUS.</span>
      </div>
    </header>

    <nav class="chapter-dock" aria-label="关于页章节">
      <div class="about-width dock-inner">
        <span class="dock-title"><Compass :size="19" aria-hidden="true" />本次航程</span>
        <div class="dock-links">
          <a href="#about-projects">项目档案</a><a href="#about-profile">关于我</a><a href="#about-journey">工作航程</a><a v-if="profile.interests.length || profile.location_name" href="#about-life">屏幕之外</a><a href="#about-contact">联系</a>
        </div>
        <button
          v-if="!reducedMotion"
          class="motion-toggle"
          type="button"
          :aria-pressed="motionPaused"
          @click="toggleMotion"
        >
          <Pause v-if="!motionPaused" :size="14" aria-hidden="true" /><Play
            v-else
            :size="14"
            aria-hidden="true"
          />{{ motionPaused ? "开启动效" : "暂停动效" }}
        </button>
      </div>
      <div class="reading-track" aria-hidden="true"><span></span></div>
    </nav>

    <section
      id="about-projects"
      class="projects-section about-width"
      data-about-scene
      aria-labelledby="projects-title"
    >
      <header class="section-heading" data-about-reveal>
        <div>
          <h2 id="projects-title">把想法，<span>做成作品。</span></h2>
          <p>项目经历 · 每一份实践，都有自己的航向。</p>
        </div>
        <span v-if="profile.project_experiences.length" class="archive-count"><b>{{ String(profile.project_experiences.length).padStart(2, "0") }}</b> 份项目档案</span>
      </header>
      <div v-if="!loading && activeProject" class="project-workspace" data-about-reveal>
        <div
          class="project-index"
          role="tablist"
          aria-label="选择项目档案"
          :aria-orientation="compactViewport ? 'horizontal' : 'vertical'"
        >
          <button
            v-for="(project, index) in profile.project_experiences"
            :id="`project-tab-${index}`"
            :key="`${index}-${project.name}`"
            class="project-tab"
            :class="{ active: index === selectedProject }"
            type="button"
            role="tab"
            :aria-selected="index === selectedProject"
            aria-controls="project-dossier"
            :tabindex="index === selectedProject ? 0 : -1"
            @click="selectProject(index)"
            @keydown="projectKeydown($event, index)"
          >
            <span class="project-number">{{ String(index + 1).padStart(2, "0") }}</span><span class="project-tab-copy"><strong>{{ project.name }}</strong><small v-if="project.period || project.role">{{
              project.period || project.role
            }}</small></span><ArrowUpRight :size="17" aria-hidden="true" />
          </button>
        </div>
        <div
          id="project-dossier"
          class="project-dossier"
          role="tabpanel"
          :aria-labelledby="`project-tab-${selectedProject}`"
          tabindex="0"
          @pointermove="updateCardPerspective"
          @pointerleave="resetCardPerspective"
        >
          <div class="dossier-top">
            <span><BookOpen :size="17" aria-hidden="true" />项目档案</span><span>{{ String(selectedProject + 1).padStart(2, "0") }} /
              {{ String(profile.project_experiences.length).padStart(2, "0") }}</span>
          </div>
          <Transition name="dossier" mode="out-in">
            <article :key="selectedProject" class="dossier-content">
              <div class="dossier-meta">
                <span v-if="activeProject.period">{{ activeProject.period }}</span><span v-if="activeProject.role">{{ activeProject.role }}</span>
              </div>
              <h3>{{ activeProject.name }}</h3>
              <p v-if="activeProject.summary" class="project-summary">
                {{ activeProject.summary }}
              </p>
              <ul
                v-if="activeProject.technologies.length"
                class="technology-list"
                aria-label="当前项目技术栈"
              >
                <li
                  v-for="(technology, index) in activeProject.technologies"
                  :key="`${index}-${technology}`"
                >
                  {{ technology }}
                </li>
              </ul>
              <a
                v-if="activeProject.link_url"
                class="dossier-link"
                :href="activeProject.link_url"
                target="_blank"
                rel="noopener noreferrer"
              >查看项目<ArrowUpRight :size="19" aria-hidden="true" /></a>
            </article>
          </Transition>
          <div class="dossier-bottom">
            <span>从想法，到真实的使用场景。</span>
            <div v-if="profile.project_experiences.length > 1">
              <button
                type="button"
                aria-label="上一个项目"
                @click="selectProject(selectedProject - 1)"
              >
                <ChevronLeft :size="21" aria-hidden="true" />
              </button><button
                type="button"
                aria-label="下一个项目"
                @click="selectProject(selectedProject + 1)"
              >
                <ChevronRight :size="21" aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
      </div>
      <p v-else class="quiet-empty" role="status">
        {{ loading ? "正在读取项目档案…" : "项目档案正在整理中。" }}
      </p>
      <div class="toolbox" data-about-reveal>
        <div class="toolbox-heading">
          <Code2 :size="22" aria-hidden="true" />
          <div>
            <h3>随行工具箱</h3>
            <p>
              技术与工具<span v-if="activeProject?.technologies.length">
                · 高亮当前项目所用技术</span>
            </p>
          </div>
        </div>
        <ul v-if="uniqueSkills.length" class="skills-ledger">
          <li
            v-for="skill in uniqueSkills"
            :key="skill.name.toLowerCase()"
            :class="{ related: isRelatedSkill(skill.name) }"
          >
            <img
              v-if="skill.icon_url"
              :src="skill.icon_url"
              alt=""
              width="25"
              height="25"
              loading="lazy"
              @error="handleSkillIconError"
            /><span>{{ skill.name }}</span><span v-if="isRelatedSkill(skill.name)" class="sr-only">，当前项目使用</span>
          </li>
        </ul>
        <p v-else class="quiet-empty">技术与工具正在整理中。</p>
      </div>
    </section>

    <section
      id="about-profile"
      class="profile-section"
      data-about-scene
      aria-labelledby="profile-title"
    >
      <div class="about-width profile-sheet" data-about-reveal>
        <div class="profile-side">
          <span class="sheet-note">写在航海日志的扉页</span>
          <h2 id="profile-title">保持好奇，<br />持续<span>航行。</span></h2>
          <span class="signature">{{ profile.display_name || "关于我" }}</span>
        </div>
        <div class="profile-copy">
          <p v-if="profile.bio" class="biography">{{ profile.bio }}</p>
          <p v-else class="quiet-empty">
            {{ loading ? "正在读取个人介绍…" : "个人介绍正在整理中。" }}
          </p>
          <dl v-if="profile.metrics.length" class="profile-metrics">
            <div v-for="(metric, index) in profile.metrics" :key="`${index}-${metric.label}`">
              <dt>{{ metric.label }}</dt>
              <dd>{{ metric.value }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </section>

    <section
      id="about-journey"
      class="journey-section about-width"
      data-about-scene
      aria-labelledby="journey-title"
    >
      <div class="journey-heading">
        <span class="small-caption">每一站，都留下新的积累</span>
        <h2 id="journey-title">走过的路，<br />成为<span>我的坐标。</span></h2>
        <p>工作经历</p>
        <a v-if="hasResume" class="text-action" :href="resumeDownloadUrl" :download="resumeFileName"><Download :size="17" aria-hidden="true" />下载完整简历<ArrowDown
          :size="16"
          aria-hidden="true"
        /></a>
        <div class="journey-bearing" aria-hidden="true">
          <Compass :size="76" stroke-width="0.7" /><span>THE JOURNEY CONTINUES</span>
        </div>
      </div>
      <ol v-if="profile.work_experiences.length" class="journey-list">
        <li
          v-for="(work, index) in profile.work_experiences"
          :key="`${index}-${work.organization}`"
          class="journey-entry"
          data-about-scene
          data-about-reveal
        >
          <div class="journey-marker" aria-hidden="true"><span></span></div>
          <span class="station-index">{{ String(index + 1).padStart(2, "0") }}</span>
          <p v-if="work.period" class="journey-period">{{ work.period }}</p>
          <h3>{{ work.organization }}</h3>
          <p v-if="work.role" class="journey-role">{{ work.role }}</p>
          <span class="station-rule" aria-hidden="true"></span>
        </li>
      </ol>
      <p v-else class="quiet-empty">{{ loading ? "正在读取工作经历…" : "航程记录正在整理中。" }}</p>
    </section>

    <section
      v-if="!loading && (profile.interests.length || profile.location_name)"
      id="about-life"
      class="life-section"
      data-about-scene
      aria-labelledby="life-title"
    >
      <div class="life-scene" aria-hidden="true">
        <img
          :src="`${baseUrl}about/quiet-harbor.webp`"
          alt=""
          width="1536"
          height="1024"
          loading="lazy"
        />
      </div>
      <div class="life-shade" aria-hidden="true"></div>
      <div class="about-width life-content">
        <div class="life-copy" data-about-reveal>
          <h2 id="life-title">关掉屏幕，<br />世界<span>还有很多页。</span></h2>
          <p>屏幕之外 · 留一些时间，给生活里的热爱。</p>
          <ul class="interest-list">
            <li v-for="(interest, index) in profile.interests" :key="`${index}-${interest}`">
              {{ interest }}
            </li>
          </ul>
        </div>
        <div v-if="profile.location_name" class="port-card" data-about-reveal>
          <header>
            <div>
              <span class="small-caption">此刻的停泊地</span>
              <h3><MapPin :size="19" aria-hidden="true" />{{ profile.location_name }}</h3>
            </div>
            <span class="port-beacon" aria-hidden="true"></span>
          </header>
          <AboutLocationMap
            :name="profile.location_name"
            :longitude="profile.location_longitude"
            :latitude="profile.location_latitude"
          />
          <p v-if="coordinateLabel" class="port-coordinates">{{ coordinateLabel }}</p>
        </div>
      </div>
    </section>

    <section
      v-if="
        !loading && (profile.site_title || profile.site_description || profile.site_stack.length)
      "
      class="site-section about-width"
      data-about-scene
      aria-labelledby="site-title"
    >
      <div class="site-heading" data-about-reveal>
        <Code2 :size="28" stroke-width="1.2" aria-hidden="true" />
        <h2 id="site-title">{{ profile.site_title || "关于本站" }}</h2>
        <span v-if="profile.site_launched_at" class="site-launch">启航 · {{ profile.site_launched_at }}</span>
      </div>
      <div class="site-copy" data-about-reveal>
        <p v-if="profile.site_description">{{ profile.site_description }}</p>
        <ul v-if="profile.site_stack.length" class="site-stack" aria-label="本站技术栈">
          <li v-for="(technology, index) in profile.site_stack" :key="`${index}-${technology}`">
            {{ technology }}
          </li>
        </ul>
        <a
          v-if="profile.site_repository_url"
          class="text-action"
          :href="profile.site_repository_url"
          target="_blank"
          rel="noopener noreferrer"
        >查看本站源码<ExternalLink :size="16" aria-hidden="true" /></a>
      </div>
    </section>

    <section
      id="about-contact"
      class="contact-section"
      data-about-scene
      aria-labelledby="contact-title"
    >
      <div class="about-width contact-inner">
        <div class="contact-copy" data-about-reveal>
          <p class="contact-opening"><span aria-hidden="true"></span>航程未完，期待下一次相遇。</p>
          <h2 id="contact-title">下一段航程，<br /><span>不妨一起聊聊。</span></h2>
          <p class="contact-description">
            如果你也在做有意思的产品，或者只是想聊聊技术与生活，欢迎来打个招呼。
          </p>
          <div class="contact-links">
            <a v-if="profile.email" class="contact-email" :href="`mailto:${profile.email}`">{{ profile.email }}<ArrowUpRight :size="25" aria-hidden="true" /></a>
            <div class="social-links">
              <a
                v-for="(link, index) in profile.social_links"
                :key="`${index}-${link.url}`"
                class="text-action"
                :href="link.url"
                target="_blank"
                rel="noopener noreferrer"
              >{{ link.label || link.platform }}<ArrowUpRight :size="16" aria-hidden="true" /></a><RouterLink to="/guestbook" class="text-action">
                留下足迹<ArrowRight :size="17" aria-hidden="true" />
              </RouterLink>
            </div>
          </div>
        </div>
        <div
          class="contact-postcard"
          data-about-reveal
          @pointermove="updateCardPerspective"
          @pointerleave="resetCardPerspective"
        >
          <div class="postcard-top">
            <span>一张来自夜航的明信片</span><Mail :size="30" stroke-width="1" aria-hidden="true" />
          </div>
          <Transition name="postcard" mode="out-in">
            <div v-if="!showQr" key="front" class="postcard-front">
              <img
                :src="`${baseUrl}about/quiet-harbor.webp`"
                alt="海岸旅行主题插画"
                width="1536"
                height="1024"
                loading="lazy"
              />
              <p>很高兴，<br />在这里遇见你。</p>
              <span>{{ profile.display_name }}</span>
            </div>
            <figure v-else key="qr" class="postcard-qr">
              <a
                :href="contactQrUrl"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="查看微信二维码大图"
              ><img :src="contactQrUrl" alt="微信联系二维码" width="888" height="1131" /></a>
              <figcaption>扫码添加微信</figcaption>
            </figure>
          </Transition><button
            class="postcard-toggle"
            type="button"
            :aria-expanded="showQr"
            @click="showQr = !showQr"
          >
            <QrCode v-if="!showQr" :size="17" aria-hidden="true" /><ArrowLeft
              v-else
              :size="17"
              aria-hidden="true"
            />{{ showQr ? "返回明信片" : "翻到背面 · 微信联系"
            }}<ArrowRight :size="17" aria-hidden="true" />
          </button>
        </div>
      </div>
      <div class="about-colophon about-width">
        <span>ABOUT / {{ profile.display_name }}</span><span v-if="updatedDate">更新于 {{ updatedDate }}</span><RouterLink to="/articles">
          继续阅读航海日志<ArrowRight :size="15" aria-hidden="true" />
        </RouterLink>
      </div>
    </section>

    <dialog
      ref="resumeDialog"
      class="night-resume-dialog"
      aria-labelledby="resume-title"
      @click="$event.target === resumeDialog && closeResumePreview()"
      @close="resumePreviewOpen = false"
    >
      <section class="resume-dialog-content">
        <header>
          <div>
            <p class="small-caption">简历预览</p>
            <h2 id="resume-title">{{ resumeFileName }}</h2>
          </div>
          <button
            class="dialog-close"
            type="button"
            aria-label="关闭简历预览"
            autofocus
            @click="closeResumePreview"
          >
            <X :size="22" aria-hidden="true" />
          </button>
        </header>
        <iframe
          v-if="resumePreviewOpen && hasResume"
          :src="profile.resume_url"
          title="在线预览简历"
        ></iframe>
        <footer>
          <span>若预览未显示，可下载查看。</span><a class="text-action" :href="resumeDownloadUrl" :download="resumeFileName"><Download :size="17" aria-hidden="true" />下载 PDF</a>
        </footer>
      </section>
    </dialog>
  </main>
</template>

<style scoped src="../about-page.css"></style>
