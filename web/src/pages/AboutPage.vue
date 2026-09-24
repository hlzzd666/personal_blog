<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  Download,
  FileText,
  Mail,
  Pause,
  Play,
  X,
} from "lucide-vue-next";
import { fetchAboutProfile, type AboutProfile } from "../api/about";
import AboutLocationMap from "../components/AboutLocationMap.vue";
import OceanIcon from "../components/OceanIcon.vue";
import { useViewportReveal } from "../composables/useViewportReveal";

const emptyProfile: AboutProfile = {
  id: 0, display_name: "", role: "", headline: "", bio: "", avatar_url: "",
  resume_url: "", resume_filename: "", status_text: "", email: null,
  location_name: "", location_longitude: null, location_latitude: null,
  metrics: [], work_experiences: [], project_experiences: [], skills: [],
  social_links: [], interests: [], site_title: "", site_description: "",
  site_launched_at: "", site_stack: [], site_repository_url: null, updated_at: "",
};

const profile = ref<AboutProfile>(emptyProfile);
const loading = ref(true);
const errorText = ref("");
const pageRoot = ref<HTMLElement | null>(null);
const heroRoot = ref<HTMLElement | null>(null);
const journeyRoot = ref<HTMLElement | null>(null);
const resumeDialog = ref<HTMLDialogElement | null>(null);
const resumePreviewOpen = ref(false);
const avatarUnavailable = ref(false);
const heroVisible = ref(true);
const documentVisible = ref(true);
const motionPaused = ref(false);
const reducedMotion = ref(false);
const heroReady = ref(false);
const { observe } = useViewportReveal();
const baseUrl = import.meta.env.BASE_URL;
const contactQrUrl = `${baseUrl}assets/d75239bce323589ed27f5a4be20c80f7.jpg`;
const motionActive = computed(
  () => !reducedMotion.value && !motionPaused.value && documentVisible.value,
);
let heroObserver: IntersectionObserver | undefined;
let motionPreference: MediaQueryList | undefined;
let scrollFrame = 0;
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
function updateScroll() {
  scrollFrame = 0;
  if (!pageRoot.value || !documentVisible.value) return;
  const page = pageRoot.value.getBoundingClientRect();
  pageRoot.value.style.setProperty(
    "--reading-progress",
    String(Math.min(1, Math.max(0, -page.top / Math.max(1, page.height - window.innerHeight)))),
  );
  if (journeyRoot.value) {
    const bounds = journeyRoot.value.getBoundingClientRect();
    const progress = Math.min(
      1,
      Math.max(0, (window.innerHeight * 0.62 - bounds.top) / Math.max(1, bounds.height)),
    );
    journeyRoot.value.style.setProperty(
      "--journey-progress",
      motionActive.value ? String(progress) : "1",
    );
  }
  if (heroRoot.value && heroVisible.value) {
    const offset = motionActive.value
      ? Math.min(35, Math.max(0, -heroRoot.value.getBoundingClientRect().top * 0.07))
      : 0;
    heroRoot.value.style.setProperty("--scroll-drift", `${offset.toFixed(1)}px`);
  }
}
function requestScrollUpdate() {
  if (!scrollFrame) scrollFrame = window.requestAnimationFrame(updateScroll);
}
function toggleMotion() {
  motionPaused.value = !motionPaused.value;
  resetPerspective();
  requestScrollUpdate();
}
function syncMotionPreference() {
  reducedMotion.value = motionPreference?.matches ?? false;
  resetPerspective();
  requestScrollUpdate();
}
function handleVisibility() {
  documentVisible.value = !document.hidden;
  resetPerspective();
  requestScrollUpdate();
}
async function loadProfile() {
  loading.value = true;
  errorText.value = "";
  try {
    const result = await fetchAboutProfile();
    if (disposed) return;
    profile.value = result;
    avatarUnavailable.value = false;
  } catch {
    if (!disposed) errorText.value = "个人资料暂时无法加载，请稍后重试。";
  } finally {
    if (!disposed) {
      loading.value = false;
      await nextTick();
      if (!disposed) {
        void observe(pageRoot.value);
        requestScrollUpdate();
      }
    }
  }
}
onMounted(() => {
  motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
  syncMotionPreference();
  motionPreference.addEventListener("change", syncMotionPreference);
  documentVisible.value = !document.hidden;
  document.addEventListener("visibilitychange", handleVisibility);
  window.addEventListener("scroll", requestScrollUpdate, { passive: true });
  window.addEventListener("resize", requestScrollUpdate, { passive: true });
  heroObserver = new IntersectionObserver(([entry]) => {
    heroVisible.value = Boolean(entry?.isIntersecting);
    requestScrollUpdate();
  });
  if (heroRoot.value) heroObserver.observe(heroRoot.value);
  void loadProfile();
});
onBeforeUnmount(() => {
  disposed = true;
  heroObserver?.disconnect();
  motionPreference?.removeEventListener("change", syncMotionPreference);
  document.removeEventListener("visibilitychange", handleVisibility);
  window.removeEventListener("scroll", requestScrollUpdate);
  window.removeEventListener("resize", requestScrollUpdate);
  window.cancelAnimationFrame(scrollFrame);
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
      :class="{ 'is-ready': heroReady, 'is-offscreen': !heroVisible }"
      @pointermove="updatePerspective"
      @pointerleave="resetPerspective"
    >
      <div class="hero-scene" aria-hidden="true">
        <div class="hero-scene-drift">
          <img
            class="hero-art"
            :src="`${baseUrl}about/night-voyage.webp`"
            alt=""
            width="1536"
            height="1024"
            fetchpriority="high"
            @load="heroReady = true"
          />
        </div>
      </div>
      <div class="hero-shade" aria-hidden="true"></div>
      <div class="hero-inner about-width">
        <div class="hero-copy">
          <div class="hero-identity">
            <img
              v-if="profile.avatar_url && !avatarUnavailable"
              class="hero-avatar"
              :src="profile.avatar_url"
              :alt="`${profile.display_name}的头像`"
              width="72"
              height="72"
              @error="handleAvatarError"
            />
            <div>
              <p class="section-label">ABOUT / 夜航手记</p>
              <p v-if="!loading && profile.role" class="hero-role">{{ profile.role }}</p>
            </div>
          </div>
          <h1 v-if="!loading && profile.display_name">
            <span>你好，我是</span><span>{{ profile.display_name }}。</span>
          </h1>
          <h1 v-else>关于我</h1>
          <p class="hero-headline">{{ loading ? "正在展开个人航海日志。" : profile.headline }}</p>
          <p v-if="profile.status_text && !loading" class="sailing-status">
            <span aria-hidden="true"></span>{{ profile.status_text }}
          </p>
          <div class="hero-actions">
            <a class="button-brass" href="#about-contact"><Mail :size="19" aria-hidden="true" />联系我<ArrowUpRight
              :size="17"
              aria-hidden="true"
            /></a><button
              v-if="hasResume && !loading"
              class="text-action"
              type="button"
              @click="openResumePreview"
            >
              <FileText :size="19" aria-hidden="true" />预览简历<ArrowRight
                :size="19"
                aria-hidden="true"
              />
            </button>
          </div>
          <p v-if="errorText" class="profile-notice" role="status">
            {{ errorText }}<button type="button" @click="loadProfile">重新加载</button>
          </p>
        </div>
      </div>
      <div class="hero-bottom about-width">
        <a class="scroll-cue" href="#about-projects"><span>继续探索</span><ArrowDown :size="16" aria-hidden="true" /></a><button
          v-if="!reducedMotion"
          class="motion-toggle"
          type="button"
          :aria-pressed="motionPaused"
          @click="toggleMotion"
        >
          <Pause v-if="!motionPaused" :size="13" aria-hidden="true" /><Play
            v-else
            :size="13"
            aria-hidden="true"
          />{{ motionPaused ? "开启动效" : "暂停动效" }}
        </button>
      </div>
    </header>
    <div class="reading-indicator" aria-hidden="true"><span></span></div>
    <div class="workbench-band">
      <div class="workbench-grid about-width">
        <section
          id="about-projects"
          class="projects-section"
          aria-labelledby="projects-title"
          data-reveal
        >
          <header class="section-heading">
            <p class="section-label">SELECTED WORK</p>
            <h2 id="projects-title">
              项目经历<span class="heading-line" aria-hidden="true"></span>
            </h2>
          </header>
          <div v-if="!loading && profile.project_experiences.length" class="project-list">
            <article
              v-for="(project, index) in profile.project_experiences"
              :key="`${index}-${project.name}`"
              class="project-entry"
            >
              <span class="entry-number" aria-hidden="true">{{
                String(index + 1).padStart(2, "0")
              }}</span>
              <div class="project-content">
                <div v-if="project.period || project.role" class="entry-meta">
                  <span v-if="project.period">{{ project.period }}</span><span v-if="project.role">{{ project.role }}</span>
                </div>
                <h3>
                  <a
                    v-if="project.link_url"
                    :href="project.link_url"
                    target="_blank"
                    rel="noopener noreferrer"
                  >{{ project.name }}<ArrowUpRight :size="19" aria-hidden="true" /></a><template v-else>{{ project.name }}</template>
                </h3>
                <p v-if="project.summary" class="project-summary">{{ project.summary }}</p>
                <ul
                  v-if="project.technologies.length"
                  class="technology-list"
                  aria-label="项目技术栈"
                >
                  <li
                    v-for="(technology, technologyIndex) in project.technologies"
                    :key="`${technologyIndex}-${technology}`"
                  >
                    {{ technology }}
                  </li>
                </ul>
              </div>
            </article>
          </div>
          <p v-else class="quiet-empty" :role="loading ? 'status' : undefined">
            {{ loading ? "正在读取项目档案…" : "新的作品正在路上。" }}
          </p>
        </section>
        <section class="toolbox-section" aria-labelledby="toolbox-title" data-reveal>
          <header class="section-heading">
            <p class="section-label">TOOLBOX</p>
            <h2 id="toolbox-title">
              技术与工具<span class="heading-line" aria-hidden="true"></span>
            </h2>
          </header>
          <ul v-if="!loading && uniqueSkills.length" class="skills-ledger">
            <li v-for="skill in uniqueSkills" :key="skill.name.toLocaleLowerCase()">
              <img
                v-if="skill.icon_url"
                :src="skill.icon_url"
                alt=""
                width="26"
                height="26"
                loading="lazy"
                @error="handleSkillIconError"
              /><span>{{ skill.name }}</span>
            </li>
          </ul>
          <p v-else class="quiet-empty">
            {{ loading ? "正在读取技术栈…" : "技术与工具正在整理中。" }}
          </p>
          <a class="text-action toolbox-next" href="#about-journey">继续阅读我的经历<ArrowRight :size="18" aria-hidden="true" /></a>
        </section>
      </div>
    </div>
    <div class="about-width reading-sections">
      <section class="profile-section section-grid" aria-labelledby="profile-title" data-reveal>
        <header class="section-heading">
          <p class="section-label">BEHIND THE LOG</p>
          <h2 id="profile-title">关于我<span class="heading-line" aria-hidden="true"></span></h2>
          <p class="section-aside">代码之外，也有生活。</p>
        </header>
        <div class="profile-copy">
          <p v-if="!loading && profile.bio" class="biography">{{ profile.bio }}</p>
          <p v-else class="quiet-empty">
            {{ loading ? "正在读取个人介绍…" : "个人介绍正在整理中。" }}
          </p>
          <dl v-if="!loading && profile.metrics.length" class="profile-metrics">
            <div v-for="(metric, index) in profile.metrics" :key="`${index}-${metric.label}`">
              <dt>{{ metric.value }}</dt>
              <dd>{{ metric.label }}</dd>
            </div>
          </dl>
        </div>
      </section>
      <section
        id="about-journey"
        class="journey-section section-grid"
        aria-labelledby="journey-title"
        data-reveal
      >
        <header class="section-heading">
          <p class="section-label">THE JOURNEY</p>
          <h2 id="journey-title">工作经历<span class="heading-line" aria-hidden="true"></span></h2>
          <p class="section-aside">每一站，都留下些新的积累。</p>
          <a
            v-if="hasResume && !loading"
            class="text-action resume-download"
            :href="resumeDownloadUrl"
            :download="resumeFileName"
          ><Download :size="17" aria-hidden="true" />下载完整简历</a>
        </header>
        <ol
          v-if="!loading && profile.work_experiences.length"
          ref="journeyRoot"
          class="journey-list"
        >
          <li
            v-for="(work, index) in profile.work_experiences"
            :key="`${index}-${work.organization}-${work.period}`"
            class="journey-entry"
          >
            <span class="journey-marker" aria-hidden="true"></span>
            <p v-if="work.period" class="entry-meta">{{ work.period }}</p>
            <h3>{{ work.organization }}</h3>
            <p v-if="work.role" class="journey-role">{{ work.role }}</p>
          </li>
        </ol>
        <p v-else class="quiet-empty">
          {{ loading ? "正在读取工作经历…" : "航程记录正在整理中。" }}
        </p>
      </section>
      <section
        v-if="!loading && (profile.interests.length || profile.location_name)"
        class="life-section"
        aria-label="生活与所在地"
        data-reveal
      >
        <div v-if="profile.interests.length" class="interests-section">
          <header class="section-heading">
            <p class="section-label">AWAY FROM THE SCREEN</p>
            <h2>屏幕之外<span class="heading-line" aria-hidden="true"></span></h2>
          </header>
          <p class="section-aside">留一些时间，给生活里的热爱。</p>
          <ul class="interest-list">
            <li v-for="(interest, index) in profile.interests" :key="`${index}-${interest}`">
              <span class="interest-number" aria-hidden="true">{{
                String(index + 1).padStart(2, "0")
              }}</span>{{ interest }}
            </li>
          </ul>
        </div>
        <div v-if="profile.location_name" class="home-port">
          <header class="port-heading">
            <div>
              <p class="section-label">HOME PORT</p>
              <h2>{{ profile.location_name }}</h2>
            </div>
            <OceanIcon name="location" :size="32" />
          </header>
          <AboutLocationMap
            :name="profile.location_name"
            :longitude="profile.location_longitude"
            :latitude="profile.location_latitude"
          />
          <p v-if="coordinateLabel" class="port-coordinates">{{ coordinateLabel }}</p>
        </div>
      </section>
      <section
        v-if="
          !loading && (profile.site_title || profile.site_description || profile.site_stack.length)
        "
        class="site-section section-grid"
        aria-labelledby="site-title"
        data-reveal
      >
        <header class="section-heading">
          <p class="section-label">THIS WEBSITE</p>
          <h2 id="site-title">
            {{ profile.site_title || "关于本站"
            }}<span class="heading-line" aria-hidden="true"></span>
          </h2>
          <p v-if="profile.site_launched_at" class="section-aside">
            启航 · {{ profile.site_launched_at }}
          </p>
        </header>
        <div>
          <p v-if="profile.site_description" class="site-description">
            {{ profile.site_description }}
          </p>
          <ul
            v-if="profile.site_stack.length"
            class="technology-list site-stack"
            aria-label="本站技术栈"
          >
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
          >查看本站源码<ArrowUpRight :size="17" aria-hidden="true" /></a>
        </div>
      </section>
    </div>
    <section id="about-contact" class="contact-section" aria-labelledby="contact-title" data-reveal>
      <div class="contact-inner about-width">
        <div class="contact-copy">
          <p class="section-label">KEEP IN TOUCH</p>
          <h2 id="contact-title">下一段航程，<br />不妨一起聊聊。</h2>
          <p class="contact-description">
            如果你也在做有意思的产品，或者只是想聊聊技术与生活，欢迎来打个招呼。
          </p>
          <div class="contact-links">
            <a
              v-if="profile.email && !loading"
              class="button-brass"
              :href="`mailto:${profile.email}`"
            ><Mail :size="19" aria-hidden="true" />发封邮件<ArrowUpRight
              :size="17"
              aria-hidden="true"
            /></a><a
              v-for="(link, index) in profile.social_links"
              :key="`${index}-${link.url}`"
              class="text-action"
              :href="link.url"
              target="_blank"
              rel="noopener noreferrer"
            >{{ link.label || link.platform }}<ArrowUpRight :size="17" aria-hidden="true" /></a><RouterLink to="/guestbook" class="text-action">
              留下足迹<ArrowRight :size="17" aria-hidden="true" />
            </RouterLink>
          </div>
          <p v-if="profile.status_text && !loading" class="sailing-status contact-status">
            <span aria-hidden="true"></span>{{ profile.status_text }}
          </p>
        </div>
        <figure class="contact-qr">
          <a
            :href="contactQrUrl"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="查看微信二维码大图"
          ><img
            :src="contactQrUrl"
            :alt="`${profile.display_name}的微信二维码`"
            width="888"
            height="1131"
            loading="lazy"
          /></a>
          <figcaption>微信 · 扫码打个招呼<ArrowUpRight :size="14" aria-hidden="true" /></figcaption>
        </figure>
      </div>
      <div class="about-colophon about-width">
        <span>ABOUT / {{ profile.display_name }}</span><span v-if="updatedDate">更新于 {{ updatedDate }}</span><RouterLink to="/articles">
          阅读我的航海日志<ArrowRight :size="15" aria-hidden="true" />
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
            <p class="section-label">RESUME</p>
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
