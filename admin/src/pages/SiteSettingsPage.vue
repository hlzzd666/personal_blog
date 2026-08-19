<script setup lang="ts">
import { Check, Picture, Upload } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { computed, onMounted, ref } from "vue";

import { fetchSiteSettings, updateSiteSettings, uploadImage } from "../api/site-settings";
import PageHeader from "../components/PageHeader.vue";
import type { QuoteItem, SiteSettings } from "../types/site";

const form = ref<SiteSettings>({
  site_subtitle: "自由、梦想、伙伴，这里记录我向前航行的每一步。",
  hero_image_url: "https://images.hdqwalls.com/download/one-piece-anime-artwork-i6-2560x1440.jpg",
  nav_brand: "某某某的个人空间",
  owner_avatar_url: "/owner-avatar.jpg",
  owner_location_name: "未设置站长地址",
  owner_latitude: null,
  owner_longitude: null,
  quotes: [],
});
const statusText = ref("正在读取首页配置...");
const saving = ref(false);
const quoteDraft = ref("");
const avatarInput = ref<HTMLInputElement | null>(null);
const heroInput = ref<HTMLInputElement | null>(null);
const uploadingImage = ref<"avatar" | "hero" | "">("");

const previewQuotes = computed(() => quoteDraft.value.split("\n").filter(Boolean).slice(0, 3));

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

async function loadSettings() {
  try {
    const payload = await fetchSiteSettings();
    form.value = payload;
    formatQuotes(payload.quotes);
    statusText.value = "首页配置已加载，可直接修改。";
  } catch {
    statusText.value = "读取失败，请确认后端服务已启动。";
  }
}

async function saveSettings() {
  saving.value = true;
  statusText.value = "正在保存首页配置...";

  try {
    const payload: SiteSettings = {
      ...form.value,
      quotes: parseQuotes(),
    };

    const nextValue = await updateSiteSettings(payload);
    form.value = nextValue;
    formatQuotes(nextValue.quotes);
    statusText.value = "保存成功，前台刷新后即可看到新的封面图和语录。";
    ElMessage.success("首页配置已保存");
  } catch {
    statusText.value = "保存失败，请检查语录格式是否为：角色|台词";
    ElMessage.error("保存失败，请检查语录格式");
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
      title="首页欢迎页配置"
      description="这里管理首屏大图、副标题、导航品牌和经典语句轮播。"
    />

    <div class="status-panel">
      <el-icon><Check /></el-icon>
      {{ statusText }}
    </div>

    <div class="settings-grid">
      <el-card shadow="never" class="form-card">
        <template #header>
          <div class="panel-header">
            <span>欢迎页内容</span>
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

          <el-form-item label="首页封面图">
            <div class="image-picker image-picker-hero">
              <img :src="form.hero_image_url" alt="首页封面图" />
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

          <el-form-item label="经典语句">
            <el-input
              v-model="quoteDraft"
              type="textarea"
              :rows="8"
              placeholder="每行一个：角色|台词"
            />
          </el-form-item>

          <el-button type="primary" size="large" :loading="saving" @click="saveSettings">
            保存首页配置
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
      </el-card>
    </div>
  </div>
</template>
