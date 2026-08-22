<script setup lang="ts">
import { Bottom, Check, Delete, Document, Plus, Top, Upload, View } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { onMounted, ref } from "vue";

import { fetchAboutProfile, updateAboutProfile } from "../api/about";
import { uploadImage, uploadResume } from "../api/site-settings";
import PageHeader from "../components/PageHeader.vue";
import type {
  AboutProfilePayload,
  ProjectExperience,
  SkillItem,
  SocialLink,
  WorkExperience,
} from "../types/about";

const emptyForm: AboutProfilePayload = {
  display_name: "",
  role: "",
  headline: "",
  bio: "",
  avatar_url: "/owner-avatar.jpg",
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
  site_title: "关于本站",
  site_description: "",
  site_launched_at: "",
  site_stack: [],
  site_repository_url: null,
};

const form = ref<AboutProfilePayload>(structuredClone(emptyForm));
const activeSection = ref("profile");
const loading = ref(true);
const saving = ref(false);
const uploadingAvatar = ref(false);
const uploadingResume = ref(false);
const uploadingSkillIndex = ref<number | null>(null);
const avatarInput = ref<HTMLInputElement | null>(null);
const resumeInput = ref<HTMLInputElement | null>(null);
const statusText = ref("正在读取关于我资料...");

function moveItem<T>(items: T[], index: number, offset: -1 | 1) {
  const target = index + offset;
  if (target < 0 || target >= items.length) return;
  [items[index], items[target]] = [items[target], items[index]];
}

async function removeItem<T>(items: T[], index: number, label: string) {
  try {
    await ElMessageBox.confirm(`确定删除这条${label}吗？保存后将同步到前台。`, "删除确认", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });
    items.splice(index, 1);
  } catch {
    // 用户取消时保持当前编辑内容。
  }
}

function addMetric() {
  form.value.metrics.push({ value: "", label: "" });
}

function addWorkExperience() {
  const item: WorkExperience = {
    organization: "",
    role: "",
    period: "",
    summary: "",
    highlights: [],
  };
  form.value.work_experiences.push(item);
}

function addProjectExperience() {
  const item: ProjectExperience = {
    name: "",
    role: "",
    period: "",
    summary: "",
    link_url: null,
    technologies: [],
  };
  form.value.project_experiences.push(item);
}

function addSkill() {
  const item: SkillItem = { name: "", icon_url: "" };
  form.value.skills.push(item);
}

function addSocialLink() {
  const item: SocialLink = { platform: "", label: "", url: "" };
  form.value.social_links.push(item);
}

function normalizeOptionalFields(payload: AboutProfilePayload): AboutProfilePayload {
  return {
    ...payload,
    email: payload.email?.trim() || null,
    resume_url: payload.resume_url.trim(),
    resume_filename: payload.resume_filename.trim(),
    site_repository_url: payload.site_repository_url?.trim() || null,
    project_experiences: payload.project_experiences.map((project) => ({
      ...project,
      link_url: project.link_url?.trim() || null,
    })),
    skills: payload.skills.map((skill) => ({
      name: skill.name.trim(),
      icon_url: skill.icon_url.trim(),
    })),
  };
}

function validateForm() {
  const required = [
    form.value.display_name,
    form.value.role,
    form.value.headline,
    form.value.bio,
    form.value.status_text,
    form.value.location_name,
    form.value.site_title,
    form.value.site_description,
    form.value.site_launched_at,
  ];
  if (required.some((value) => !value.trim())) {
    ElMessage.error("请先补全必填的个人与本站信息");
    return false;
  }
  if ((form.value.location_longitude === null) !== (form.value.location_latitude === null)) {
    ElMessage.error("位置经纬度需要同时填写");
    return false;
  }
  if (form.value.skills.some((skill) => !skill.name.trim() || !skill.icon_url.trim())) {
    ElMessage.error("请为每项技术栈填写名称并上传图标");
    return false;
  }
  const skillNames = form.value.skills.map((skill) => skill.name.trim().toLocaleLowerCase());
  if (skillNames.length !== new Set(skillNames).size) {
    ElMessage.error("技术栈名称不能重复");
    return false;
  }
  return true;
}

async function loadProfile() {
  loading.value = true;
  try {
    const profile = await fetchAboutProfile();
    const { id, updated_at: updatedAt, ...payload } = profile;
    void id;
    void updatedAt;
    form.value = payload;
    statusText.value = `资料已加载 · 最近更新 ${new Intl.DateTimeFormat("zh-CN", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(profile.updated_at))}`;
  } catch {
    statusText.value = "读取失败，请确认后端服务和数据库迁移已就绪。";
    ElMessage.error("关于我资料读取失败");
  } finally {
    loading.value = false;
  }
}

async function saveProfile() {
  if (!validateForm()) return;
  saving.value = true;
  statusText.value = "正在保存关于我资料...";
  try {
    const profile = await updateAboutProfile(normalizeOptionalFields(form.value));
    const { id, updated_at: updatedAt, ...payload } = profile;
    void id;
    void updatedAt;
    form.value = payload;
    statusText.value = "保存成功，前台“关于我”页面刷新后即可看到更新。";
    ElMessage.success("关于我资料已保存");
  } catch {
    statusText.value = "保存失败，请检查必填项、链接格式和数组内容。";
    ElMessage.error("保存失败，请检查表单内容");
  } finally {
    saving.value = false;
  }
}

async function handleAvatarSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    ElMessage.error("请选择图片文件");
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error("图片大小不能超过 10 MB");
    return;
  }
  uploadingAvatar.value = true;
  try {
    form.value.avatar_url = (await uploadImage(file)).url;
    ElMessage.success("头像已上传，请保存资料");
  } catch {
    ElMessage.error("头像上传失败");
  } finally {
    uploadingAvatar.value = false;
  }
}

async function handleResumeSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
  if (!isPdf) {
    ElMessage.error("请选择 PDF 简历");
    return;
  }
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.error("简历大小不能超过 20 MB");
    return;
  }
  uploadingResume.value = true;
  try {
    const result = await uploadResume(file);
    form.value.resume_url = result.url;
    form.value.resume_filename = result.original_filename;
    ElMessage.success("简历已上传，请保存资料");
  } catch {
    ElMessage.error("简历上传失败");
  } finally {
    uploadingResume.value = false;
  }
}

async function clearResume() {
  if (!form.value.resume_url) return;
  try {
    await ElMessageBox.confirm("确定移除当前简历入口吗？保存后前台将不再展示下载和预览。", "移除确认", {
      type: "warning",
      confirmButtonText: "移除",
      cancelButtonText: "取消",
    });
    form.value.resume_url = "";
    form.value.resume_filename = "";
    ElMessage.success("已移除简历，请保存资料");
  } catch {
    // 用户取消时保持当前简历。
  }
}

function selectSkillIcon(index: number) {
  document.getElementById(`about-skill-icon-${index}`)?.click();
}

async function handleSkillIconSelected(event: Event, index: number) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    ElMessage.error("请选择图片文件");
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error("图片大小不能超过 10 MB");
    return;
  }

  const skill = form.value.skills[index];
  if (!skill) return;
  uploadingSkillIndex.value = index;
  try {
    skill.icon_url = (await uploadImage(file)).url;
    ElMessage.success("技术图标已上传，请保存资料");
  } catch {
    ElMessage.error("技术图标上传失败");
  } finally {
    uploadingSkillIndex.value = null;
  }
}

onMounted(() => {
  void loadProfile();
});
</script>

<template>
  <div v-loading="loading" class="page-stack about-admin-page">
    <PageHeader
      eyebrow="ABOUT PROFILE"
      title="关于我"
      description="维护访客在关于我页面看到的个人档案、职业航迹、项目、能力与本站信息。"
    />

    <div class="about-admin-toolbar">
      <div class="about-save-status">
        <el-icon><Check /></el-icon>
        <span>{{ statusText }}</span>
      </div>
      <el-button type="primary" size="large" :loading="saving" @click="saveProfile">
        保存全部资料
      </el-button>
    </div>

    <el-tabs v-model="activeSection" class="about-editor-tabs">
      <el-tab-pane label="个人名片" name="profile">
        <div class="about-form-grid about-form-grid-profile">
          <section class="about-form-section">
            <div class="about-section-heading">
              <div>
                <h3>基础资料</h3>
                <p>用于页面首屏与联系入口。</p>
              </div>
            </div>
            <el-form label-position="top">
              <div class="about-field-pair">
                <el-form-item label="姓名 / 昵称" required>
                  <el-input v-model="form.display_name" maxlength="80" show-word-limit />
                </el-form-item>
                <el-form-item label="当前身份" required>
                  <el-input v-model="form.role" maxlength="120" />
                </el-form-item>
              </div>
              <el-form-item label="一句话介绍" required>
                <el-input v-model="form.headline" maxlength="160" show-word-limit />
              </el-form-item>
              <el-form-item label="个人介绍" required>
                <el-input
                  v-model="form.bio"
                  type="textarea"
                  :rows="6"
                  maxlength="2000"
                  show-word-limit
                />
              </el-form-item>
              <div class="about-field-pair">
                <el-form-item label="当前状态" required>
                  <el-input v-model="form.status_text" maxlength="100" />
                </el-form-item>
                <el-form-item label="公开邮箱">
                  <el-input v-model="form.email" placeholder="不填写则前台不展示" />
                </el-form-item>
              </div>
            </el-form>
          </section>

          <div class="about-profile-side">
            <section class="about-form-section about-avatar-editor">
              <div class="about-section-heading">
                <div>
                  <h3>人物头像</h3>
                  <p>建议使用清晰正方形图片。</p>
                </div>
              </div>
              <img :src="form.avatar_url" alt="关于我头像预览" />
              <input
                ref="avatarInput"
                class="image-picker-input"
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                @change="handleAvatarSelected"
              />
              <el-button :loading="uploadingAvatar" @click="avatarInput?.click()">
                <el-icon><Upload /></el-icon>更换头像
              </el-button>
            </section>

            <section class="about-form-section about-resume-editor">
              <div class="about-section-heading">
                <div>
                  <h3>个人简历</h3>
                  <p>上传 PDF，前台支持下载和在线预览。</p>
                </div>
              </div>
              <div class="about-resume-preview" :class="{ 'is-empty': !form.resume_url }">
                <el-icon><Document /></el-icon>
                <strong>{{ form.resume_filename || "暂未上传简历" }}</strong>
                <small>{{ form.resume_url ? "PDF 简历已就绪" : "支持 20 MB 以内 PDF" }}</small>
              </div>
              <input
                ref="resumeInput"
                class="image-picker-input"
                type="file"
                accept="application/pdf,.pdf"
                @change="handleResumeSelected"
              />
              <div class="about-resume-actions">
                <el-button :loading="uploadingResume" @click="resumeInput?.click()">
                  <el-icon><Upload /></el-icon>{{ form.resume_url ? "更换简历" : "上传简历" }}
                </el-button>
                <el-button
                  v-if="form.resume_url"
                  :icon="View"
                  tag="a"
                  :href="form.resume_url"
                  target="_blank"
                >
                  预览
                </el-button>
                <el-button v-if="form.resume_url" :icon="Delete" @click="clearResume">移除</el-button>
              </div>
            </section>
          </div>
        </div>

        <section class="about-form-section">
          <div class="about-section-heading">
            <div>
              <h3>个人指标</h3>
              <p>首屏最多展示 6 项简短信息。</p>
            </div>
            <el-button :icon="Plus" @click="addMetric">添加指标</el-button>
          </div>
          <div class="about-metric-editor">
            <div v-for="(metric, index) in form.metrics" :key="index" class="about-metric-item">
              <el-input v-model="metric.value" placeholder="例如：5 年+" maxlength="20" />
              <el-input v-model="metric.label" placeholder="例如：开发经验" maxlength="30" />
              <el-button
                :icon="Delete"
                circle
                title="删除指标"
                @click="removeItem(form.metrics, index, '指标')"
              />
            </div>
          </div>
        </section>

        <section class="about-form-section">
          <div class="about-section-heading">
            <div>
              <h3>城市与地图</h3>
              <p>坐标用于高德地图定位；不填写坐标时前台显示城市信息占位。</p>
            </div>
          </div>
          <el-form label-position="top">
            <el-form-item label="城市名称" required>
              <el-input v-model="form.location_name" placeholder="例如：中国 · 南京" />
            </el-form-item>
            <div class="about-field-pair">
              <el-form-item label="经度">
                <el-input-number
                  v-model="form.location_longitude"
                  :min="-180"
                  :max="180"
                  :precision="6"
                  controls-position="right"
                />
              </el-form-item>
              <el-form-item label="纬度">
                <el-input-number
                  v-model="form.location_latitude"
                  :min="-90"
                  :max="90"
                  :precision="6"
                  controls-position="right"
                />
              </el-form-item>
            </div>
            <el-form-item label="兴趣标签">
              <el-select
                v-model="form.interests"
                multiple
                filterable
                allow-create
                default-first-option
                placeholder="输入后回车添加"
              >
                <el-option
                  v-for="interest in form.interests"
                  :key="interest"
                  :label="interest"
                  :value="interest"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </section>
      </el-tab-pane>

      <el-tab-pane label="工作经历" name="work">
        <section class="about-form-section">
          <div class="about-section-heading">
            <div>
              <h3>工作经历</h3>
              <p>按前台展示顺序排列，支持补充关键成果。</p>
            </div>
            <el-button type="primary" plain :icon="Plus" @click="addWorkExperience">
              添加经历
            </el-button>
          </div>
          <div class="about-repeat-list">
            <article
              v-for="(item, index) in form.work_experiences"
              :key="index"
              class="about-repeat-item"
            >
              <div class="about-repeat-title">
                <strong>{{ item.organization || `工作经历 ${index + 1}` }}</strong>
                <div class="about-order-actions">
                  <el-button
                    :icon="Top"
                    circle
                    title="上移"
                    :disabled="index === 0"
                    @click="moveItem(form.work_experiences, index, -1)"
                  />
                  <el-button
                    :icon="Bottom"
                    circle
                    title="下移"
                    :disabled="index === form.work_experiences.length - 1"
                    @click="moveItem(form.work_experiences, index, 1)"
                  />
                  <el-button
                    :icon="Delete"
                    circle
                    title="删除"
                    @click="removeItem(form.work_experiences, index, '工作经历')"
                  />
                </div>
              </div>
              <el-form label-position="top">
                <div class="about-field-triple">
                  <el-form-item label="组织 / 公司" required>
                    <el-input v-model="item.organization" />
                  </el-form-item>
                  <el-form-item label="职位 / 角色" required>
                    <el-input v-model="item.role" />
                  </el-form-item>
                  <el-form-item label="时间范围" required>
                    <el-input v-model="item.period" placeholder="2024.01 - 至今" />
                  </el-form-item>
                </div>
                <el-form-item label="经历简介" required>
                  <el-input
                    v-model="item.summary"
                    type="textarea"
                    :rows="3"
                    maxlength="500"
                    show-word-limit
                  />
                </el-form-item>
                <el-form-item label="关键成果">
                  <el-select
                    v-model="item.highlights"
                    multiple
                    filterable
                    allow-create
                    default-first-option
                    placeholder="输入一条成果后回车"
                  >
                    <el-option
                      v-for="highlight in item.highlights"
                      :key="highlight"
                      :label="highlight"
                      :value="highlight"
                    />
                  </el-select>
                </el-form-item>
              </el-form>
            </article>
            <el-empty v-if="form.work_experiences.length === 0" description="还没有工作经历" />
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="项目经历" name="projects">
        <section class="about-form-section">
          <div class="about-section-heading">
            <div>
              <h3>项目经历</h3>
              <p>展示有代表性的项目、职责与技术组合。</p>
            </div>
            <el-button type="primary" plain :icon="Plus" @click="addProjectExperience">
              添加项目
            </el-button>
          </div>
          <div class="about-repeat-list">
            <article
              v-for="(item, index) in form.project_experiences"
              :key="index"
              class="about-repeat-item"
            >
              <div class="about-repeat-title">
                <strong>{{ item.name || `项目 ${index + 1}` }}</strong>
                <div class="about-order-actions">
                  <el-button
                    :icon="Top"
                    circle
                    title="上移"
                    :disabled="index === 0"
                    @click="moveItem(form.project_experiences, index, -1)"
                  />
                  <el-button
                    :icon="Bottom"
                    circle
                    title="下移"
                    :disabled="index === form.project_experiences.length - 1"
                    @click="moveItem(form.project_experiences, index, 1)"
                  />
                  <el-button
                    :icon="Delete"
                    circle
                    title="删除"
                    @click="removeItem(form.project_experiences, index, '项目经历')"
                  />
                </div>
              </div>
              <el-form label-position="top">
                <div class="about-field-triple">
                  <el-form-item label="项目名称" required>
                    <el-input v-model="item.name" />
                  </el-form-item>
                  <el-form-item label="项目角色" required>
                    <el-input v-model="item.role" />
                  </el-form-item>
                  <el-form-item label="项目时间" required>
                    <el-input v-model="item.period" />
                  </el-form-item>
                </div>
                <el-form-item label="项目简介" required>
                  <el-input
                    v-model="item.summary"
                    type="textarea"
                    :rows="3"
                    maxlength="500"
                    show-word-limit
                  />
                </el-form-item>
                <div class="about-field-pair">
                  <el-form-item label="项目链接">
                    <el-input v-model="item.link_url" placeholder="https://" />
                  </el-form-item>
                  <el-form-item label="技术栈">
                    <el-select
                      v-model="item.technologies"
                      multiple
                      filterable
                      allow-create
                      default-first-option
                      placeholder="输入后回车添加"
                    >
                      <el-option
                        v-for="technology in item.technologies"
                        :key="technology"
                        :label="technology"
                        :value="technology"
                      />
                    </el-select>
                  </el-form-item>
                </div>
              </el-form>
            </article>
            <el-empty v-if="form.project_experiences.length === 0" description="还没有项目经历" />
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="技术与链接" name="skills">
        <div class="about-form-grid">
          <section class="about-form-section">
            <div class="about-section-heading">
              <div>
                <h3>技术栈</h3>
                <p>每项维护一个名称和一个清晰的正方形图标，前台按此顺序展示。</p>
              </div>
              <el-button :icon="Plus" @click="addSkill">添加技术栈</el-button>
            </div>
            <div class="about-skill-editor-list">
              <article
                v-for="(skill, index) in form.skills"
                :key="index"
                class="about-skill-editor-item"
              >
                <div class="about-skill-icon-editor">
                  <small>技术图标 *</small>
                  <img v-if="skill.icon_url" :src="skill.icon_url" :alt="`${skill.name}图标预览`" />
                  <span v-else aria-hidden="true">{{ skill.name.slice(0, 1) || "+" }}</span>
                  <input
                    :id="`about-skill-icon-${index}`"
                    class="image-picker-input"
                    type="file"
                    accept="image/jpeg,image/png,image/webp,image/gif"
                    @change="handleSkillIconSelected($event, index)"
                  />
                  <el-button
                    size="small"
                    :loading="uploadingSkillIndex === index"
                    @click="selectSkillIcon(index)"
                  >
                    <el-icon><Upload /></el-icon>{{ skill.icon_url ? "更换图标" : "上传图标" }}
                  </el-button>
                </div>
                <el-form-item label="技术栈名称" required>
                  <el-input v-model="skill.name" maxlength="50" placeholder="例如：Vue" />
                </el-form-item>
                <div class="about-order-actions">
                  <el-button
                    :icon="Top"
                    circle
                    title="上移"
                    :disabled="index === 0"
                    @click="moveItem(form.skills, index, -1)"
                  />
                  <el-button
                    :icon="Bottom"
                    circle
                    title="下移"
                    :disabled="index === form.skills.length - 1"
                    @click="moveItem(form.skills, index, 1)"
                  />
                  <el-button
                    :icon="Delete"
                    circle
                    title="删除"
                    @click="removeItem(form.skills, index, '技术栈')"
                  />
                </div>
              </article>
              <el-empty v-if="form.skills.length === 0" description="还没有添加技术栈" />
            </div>
          </section>

          <section class="about-form-section">
            <div class="about-section-heading">
              <div>
                <h3>社交与联系</h3>
                <p>仅添加希望公开展示的链接。</p>
              </div>
              <el-button :icon="Plus" @click="addSocialLink">添加链接</el-button>
            </div>
            <div class="about-repeat-list">
              <article
                v-for="(link, index) in form.social_links"
                :key="index"
                class="about-repeat-item about-repeat-item-compact"
              >
                <div class="about-repeat-title">
                  <strong>{{ link.platform || `链接 ${index + 1}` }}</strong>
                  <el-button
                    :icon="Delete"
                    circle
                    title="删除"
                    @click="removeItem(form.social_links, index, '社交链接')"
                  />
                </div>
                <el-form label-position="top">
                  <div class="about-field-pair">
                    <el-form-item label="平台" required>
                      <el-input v-model="link.platform" placeholder="GitHub" />
                    </el-form-item>
                    <el-form-item label="展示名称" required>
                      <el-input v-model="link.label" />
                    </el-form-item>
                  </div>
                  <el-form-item label="链接" required>
                    <el-input v-model="link.url" placeholder="https://" />
                  </el-form-item>
                </el-form>
              </article>
              <el-empty v-if="form.social_links.length === 0" description="未公开任何社交链接" />
            </div>
          </section>
        </div>
      </el-tab-pane>

      <el-tab-pane label="关于本站" name="site">
        <section class="about-form-section about-site-editor">
          <div class="about-section-heading">
            <div>
              <h3>本站说明</h3>
              <p>向访客说明这个博客为何存在、如何构建。</p>
            </div>
          </div>
          <el-form label-position="top">
            <div class="about-field-pair">
              <el-form-item label="模块标题" required>
                <el-input v-model="form.site_title" />
              </el-form-item>
              <el-form-item label="启航时间" required>
                <el-input v-model="form.site_launched_at" placeholder="例如：2024 年 6 月" />
              </el-form-item>
            </div>
            <el-form-item label="本站介绍" required>
              <el-input
                v-model="form.site_description"
                type="textarea"
                :rows="7"
                maxlength="1200"
                show-word-limit
              />
            </el-form-item>
            <el-form-item label="本站技术栈">
              <el-select
                v-model="form.site_stack"
                multiple
                filterable
                allow-create
                default-first-option
                placeholder="输入后回车添加"
              >
                <el-option
                  v-for="item in form.site_stack"
                  :key="item"
                  :label="item"
                  :value="item"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="源码地址">
              <el-input v-model="form.site_repository_url" placeholder="不公开可留空" />
            </el-form-item>
          </el-form>
        </section>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
