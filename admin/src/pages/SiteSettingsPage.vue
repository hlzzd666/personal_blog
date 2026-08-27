<script setup lang="ts">
import { Check, Picture, Upload } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { computed, onMounted, ref } from "vue";

import { fetchSiteSettings, updateSiteSettings, uploadImage } from "../api/site-settings";
import PageHeader from "../components/PageHeader.vue";
import type { QuoteItem, SiteSettings, VisualAssetItem } from "../types/site";

function createVisualAssetDraft(): VisualAssetItem {
  return {
    key: "article_list_background",
    name: "文章列表页背景",
    usage: "background",
    image_url: "",
    enabled: false,
    opacity: 0.68,
    note: "用于文章列表页背景，建议上传清晰横图。",
  };
}

const form = ref<SiteSettings>({
  site_subtitle: "自由、梦想、伙伴，这里记录我向前航行的每一步。",
  hero_image_url: "https://images.hdqwalls.com/download/one-piece-anime-artwork-i6-2560x1440.jpg",
  nav_brand: "某某某的个人空间",
  site_launched_on: "2026-01-01",
  owner_avatar_url: "/owner-avatar.jpg",
  owner_location_name: "未设置站长地址",
  owner_latitude: null,
  owner_longitude: null,
  visual_assets: [createVisualAssetDraft()],
  quotes: [],
});
const statusText = ref("正在读取站点设置...");
const saving = ref(false);
const quoteDraft = ref("");
const avatarInput = ref<HTMLInputElement | null>(null);
const heroInput = ref<HTMLInputElement | null>(null);
const visualAssetInputs = ref<Array<HTMLInputElement | null>>([]);
const uploadingImage = ref<"avatar" | "hero" | `asset-${number}` | "">("");

const previewQuotes = computed(() => quoteDraft.value.split("\n").filter(Boolean).slice(0, 3));
const previewVisualAssets = computed(() => form.value.visual_assets.filter((asset) => asset.image_url));

function disableFutureDate(value: Date) {
  const today = new Date();
  today.setHours(23, 59, 59, 999);
  return value.getTime() > today.getTime();
}

function normalizeVisualAssets(assets: VisualAssetItem[]) {
  const backgroundAssets = assets.filter((asset) => asset.usage === "background");
  const normalizedAssets = backgroundAssets.length ? backgroundAssets : [createVisualAssetDraft()];
  return normalizedAssets.map((asset, index) => ({
    ...asset,
    key: asset.key || (index === 0 ? "article_list_background" : `asset_${Date.now()}_${index}`),
    name: asset.name || "文章列表页背景",
    usage: "background" as const,
    opacity: Number.isFinite(asset.opacity) ? asset.opacity : 0.68,
  }));
}

function formatQuotes(quotes: QuoteItem[]) {
  quoteDraft.value = quotes
    .map((item) => `${item.author}|${item.text}`)
    .join("\n");
}

function parseQuotes(): QuoteItem[] {
  return quoteDraft.value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [author, text] = line.split("|").map((item) => item.trim());
      return { author, text };
    });
}

function openImagePicker(type: "avatar" | "hero") {
  const input = type === "avatar" ? avatarInput.value : heroInput.value;
  input?.click();
}

function setVisualAssetInputRef(index: number, element: HTMLInputElement | null) {
  visualAssetInputs.value[index] = element;
}

function openVisualAssetPicker(index: number) {
  visualAssetInputs.value[index]?.click();
}

function addVisualAsset() {
  form.value.visual_assets.push({
    ...createVisualAssetDraft(),
    key: `asset_${Date.now()}`,
    name: "新的背景图",
  });
}

function removeVisualAsset(index: number) {
  form.value.visual_assets.splice(index, 1);
  if (!form.value.visual_assets.length) {
    form.value.visual_assets.push(createVisualAssetDraft());
  }
}

async function handleImageSelected(type: "avatar" | "hero", event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) {
    return;
  }
  if (!file.type.startsWith("image/")) {
    ElMessage.error("请选择图片文件");
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error("图片大小不能超过 10 MB");
    return;
  }

  uploadingImage.value = type;
  try {
    const result = await uploadImage(file);
    if (type === "avatar") {
      form.value.owner_avatar_url = result.url;
    } else {
      form.value.hero_image_url = result.url;
    }
    ElMessage.success("图片上传成功，请保存配置");
  } catch {
    ElMessage.error("图片上传失败，请稍后重试");
  } finally {
    uploadingImage.value = "";
  }
}

async function handleVisualAssetImageSelected(index: number, event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) {
    return;
  }
  if (!file.type.startsWith("image/")) {
    ElMessage.error("请选择图片文件");
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error("图片大小不能超过 10 MB");
    return;
  }

  uploadingImage.value = `asset-${index}`;
  try {
    const result = await uploadImage(file);
    form.value.visual_assets[index].image_url = result.url;
    if (!form.value.visual_assets[index].name || form.value.visual_assets[index].name === "新的视觉资产") {
      form.value.visual_assets[index].name = "已上传视觉资产";
    }
    ElMessage.success("图片上传成功，请保存配置");
  } catch {
    ElMessage.error("图片上传失败，请稍后重试");
  } finally {
    uploadingImage.value = "";
  }
}

async function loadSettings() {
  try {
    const payload = await fetchSiteSettings();
    form.value = {
      ...payload,
      visual_assets: normalizeVisualAssets(payload.visual_assets),
    };
    formatQuotes(payload.quotes);
    statusText.value = "站点设置已加载，可直接修改文章列表页视觉层。";
  } catch {
    statusText.value = "读取失败，请确认后端服务已启动。";
  }
}

async function saveSettings() {
  saving.value = true;
  statusText.value = "正在保存站点设置...";

  try {
    const payload: SiteSettings = {
      ...form.value,
      quotes: parseQuotes(),
      visual_assets: normalizeVisualAssets(form.value.visual_assets),
    };

    const nextValue = await updateSiteSettings(payload);
    form.value = nextValue;
    formatQuotes(nextValue.quotes);
    statusText.value = "保存成功，前台刷新后即可看到新的文章列表页视觉层。";
    ElMessage.success("站点设置已保存");
  } catch {
    statusText.value = "保存失败，请检查建站日期、经纬度和语录格式。";
    ElMessage.error("保存失败，请检查站点配置");
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  void loadSettings();
});
</script>

<template>
  <div class="page-stack">
    <PageHeader
      eyebrow="SITE SETTINGS"
      title="站点设置"
      description="这里管理站点基础信息，并维护文章列表页可复用的视觉层资源。"
    />

    <div class="status-panel">
      <el-icon><Check /></el-icon>
      {{ statusText }}
    </div>

    <div class="settings-grid">
      <el-card shadow="never" class="form-card">
        <template #header>
          <div class="panel-header">
            <span>站点基础内容</span>
            <el-tag type="warning">可运营配置</el-tag>
          </div>
        </template>

        <el-form label-position="top" class="settings-form" @submit.prevent="saveSettings">
          <el-form-item label="站点副标题">
            <el-input
              v-model="form.site_subtitle"
              placeholder="自由、梦想、伙伴，这里记录我向前航行的每一步。"
            />
          </el-form-item>

          <el-form-item label="导航品牌名">
            <el-input v-model="form.nav_brand" placeholder="某某某的个人空间" />
          </el-form-item>

          <el-form-item label="建站日期">
            <div class="site-date-field">
              <el-date-picker
                v-model="form.site_launched_on"
                type="date"
                format="YYYY年MM月DD日"
                value-format="YYYY-MM-DD"
                placeholder="选择建站日期"
                :disabled-date="disableFutureDate"
              />
              <span>首页 TODAY 卡片会从该日期起按自然日计算运行天数。</span>
            </div>
          </el-form-item>

          <el-form-item label="站长头像">
            <div class="image-picker image-picker-avatar">
              <img :src="form.owner_avatar_url" alt="站长头像" />
              <div class="image-picker-content">
                <strong>{{ form.owner_avatar_url ? "已选择头像" : "暂未选择头像" }}</strong>
                <span>支持 JPG、PNG、WEBP，单张不超过 10 MB</span>
                <input
                  ref="avatarInput"
                  class="image-picker-input"
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/gif"
                  @change="handleImageSelected('avatar', $event)"
                />
                <el-button
                  type="primary"
                  plain
                  :loading="uploadingImage === 'avatar'"
                  @click="openImagePicker('avatar')"
                >
                  <el-icon><Upload /></el-icon>
                  更换头像
                </el-button>
              </div>
            </div>
          </el-form-item>

          <el-form-item label="站长地址名称">
            <el-input v-model="form.owner_location_name" placeholder="例如：上海市浦东新区" />
          </el-form-item>

          <div class="coordinate-fields">
            <el-form-item label="站长纬度">
              <el-input-number
                v-model="form.owner_latitude"
                :min="-90"
                :max="90"
                :step="0.000001"
                :precision="6"
                controls-position="right"
                placeholder="例如：31.230416"
              />
            </el-form-item>
            <el-form-item label="站长经度">
              <el-input-number
                v-model="form.owner_longitude"
                :min="-180"
                :max="180"
                :step="0.000001"
                :precision="6"
                controls-position="right"
                placeholder="例如：121.473701"
              />
            </el-form-item>
          </div>
          <p class="coordinate-hint">经纬度会在后端用于计算访客与站长的直线距离，前台不会展示坐标原值。</p>

          <el-form-item label="站点封面图">
            <div class="image-picker image-picker-hero">
              <img :src="form.hero_image_url" alt="站点封面图" />
              <div class="image-picker-overlay">
                <input
                  ref="heroInput"
                  class="image-picker-input"
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/gif"
                  @change="handleImageSelected('hero', $event)"
                />
                <el-button
                  type="primary"
                  :loading="uploadingImage === 'hero'"
                  @click="openImagePicker('hero')"
                >
                  <el-icon><Picture /></el-icon>
                  更换封面图
                </el-button>
              </div>
            </div>
            <span class="image-picker-hint">建议使用横向图片，上传后点击底部按钮保存。</span>
          </el-form-item>

          <el-form-item label="文章列表页视觉资产">
            <div class="visual-assets-panel">
              <div class="visual-assets-header">
                <div>
                  <strong>文章列表页背景图</strong>
                  <span>只维护背景图；多张启用图片会在前台文章列表页每 6 秒平滑切换。</span>
                </div>
                <el-button type="primary" plain @click="addVisualAsset">添加资产</el-button>
              </div>

              <div v-for="(asset, index) in form.visual_assets" :key="asset.key" class="visual-asset-card">
                <div class="visual-asset-preview" :style="{ backgroundImage: asset.image_url ? `url(${asset.image_url})` : 'none' }">
                  <span :class="['visual-asset-state', { muted: !asset.enabled }]">
                    {{ asset.enabled ? "启用" : "停用" }}
                  </span>
                </div>
                <div class="visual-asset-form">
                  <div class="visual-asset-grid">
                    <el-input v-model="asset.key" placeholder="key，例如 article_list_background" />
                    <el-input v-model="asset.name" placeholder="名称，例如 文章列表页背景" />
                    <el-input model-value="背景图" disabled />
                  </div>
                  <div class="visual-asset-grid visual-asset-grid-secondary">
                    <el-input v-model="asset.image_url" placeholder="图片地址或上传后自动回填" />
                    <el-input-number
                      v-model="asset.opacity"
                      :min="0"
                      :max="1"
                      :step="0.05"
                      :precision="2"
                      controls-position="right"
                      placeholder="透明度"
                    />
                    <el-switch v-model="asset.enabled" active-text="启用" inactive-text="停用" />
                  </div>
                  <el-input
                    v-model="asset.note"
                    type="textarea"
                    :rows="2"
                    placeholder="备注，例如：用于文章列表页的清晰背景图"
                  />
                  <div class="visual-asset-actions">
                    <input
                      :ref="(el) => setVisualAssetInputRef(index, el as HTMLInputElement | null)"
                      class="image-picker-input"
                      type="file"
                      accept="image/jpeg,image/png,image/webp,image/gif"
                      @change="handleVisualAssetImageSelected(index, $event)"
                    />
                    <el-button
                      type="primary"
                      plain
                      :loading="uploadingImage === `asset-${index}`"
                      @click="openVisualAssetPicker(index)"
                    >
                      <el-icon><Upload /></el-icon>
                      上传图片
                    </el-button>
                    <el-button type="danger" plain @click="removeVisualAsset(index)">
                      删除
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </el-form-item>

          <el-form-item label="经典语句">
            <el-input
              v-model="quoteDraft"
              type="textarea"
              :rows="8"
              placeholder="每行一个：角色|台词"
            />
          </el-form-item>

          <el-button type="primary" size="large" :loading="saving" @click="saveSettings">
            保存设置
          </el-button>
        </el-form>
      </el-card>

      <el-card shadow="never" class="preview-card">
        <template #header>
          <div class="panel-header">
            <span>实时预览</span>
            <el-tag effect="plain">Hero</el-tag>
          </div>
        </template>

        <div class="preview-hero" :style="{ backgroundImage: `url(${form.hero_image_url})` }">
          <div class="preview-mask">
            <p>{{ form.site_subtitle }}</p>
            <img class="preview-avatar" :src="form.owner_avatar_url" alt="站长头像预览" />
            <small>站长地址：{{ form.owner_location_name }}</small>
            <ul>
              <li v-for="line in previewQuotes" :key="line">{{ line }}</li>
            </ul>
          </div>
        </div>

        <div class="preview-asset-strip">
          <div class="panel-header">
            <span>文章列表页背景图预览</span>
            <el-tag effect="plain">{{ previewVisualAssets.length }} 项已配置</el-tag>
          </div>
          <div class="preview-asset-grid">
            <article
              v-for="asset in previewVisualAssets"
              :key="asset.key"
              class="preview-asset-card"
              :style="{ backgroundImage: `url(${asset.image_url})` }"
            >
              <div class="preview-asset-shade">
                <strong>{{ asset.name }}</strong>
                <span>{{ asset.key }}</span>
              </div>
            </article>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>
