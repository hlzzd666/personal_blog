<script setup lang="ts">
import { Check, Link } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { computed, onMounted, ref } from "vue";

import { fetchSiteSettings, updateSiteSettings } from "../api/site-settings";
import PageHeader from "../components/PageHeader.vue";
import type { QuoteItem, SiteSettings } from "../types/site";

const form = ref<SiteSettings>({
  site_subtitle: "自由、梦想、伙伴，这里记录我向前航行的每一步。",
  hero_image_url: "https://images.hdqwalls.com/download/one-piece-anime-artwork-i6-2560x1440.jpg",
  nav_brand: "某某某的个人空间",
  quotes: [],
});
const statusText = ref("正在读取首页配置...");
const saving = ref(false);
const quoteDraft = ref("");

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

          <el-form-item label="封面图 URL">
            <el-input
              v-model="form.hero_image_url"
              type="textarea"
              :rows="3"
              placeholder="填写可访问的海贼王风格封面图地址"
            >
              <template #prefix>
                <el-icon><Link /></el-icon>
              </template>
            </el-input>
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
            <ul>
              <li v-for="line in previewQuotes" :key="line">{{ line }}</li>
            </ul>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>
