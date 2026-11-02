<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { CopyDocument, Delete, Refresh, Upload } from "@element-plus/icons-vue";

import { cleanupUnreferencedMediaFiles, fetchMediaFiles, uploadMediaImage } from "../api/media";
import { resolveErrorMessage } from "../api/http";
import PageHeader from "../components/PageHeader.vue";
import ImagePreview from "../components/ImagePreview.vue";
import type { MediaFileItem, MediaListResponse } from "../types/media";

type MediaFilter = "all" | "used" | "unused";

const mediaData = ref<MediaListResponse | null>(null);
const loading = ref(false);
const cleanupLoading = ref(false);
const uploading = ref(false);
const searchKeyword = ref("");
const storageFilter = ref<"all" | "local" | "oss">("all");
const referenceFilter = ref<MediaFilter>("all");
const uploadInput = ref<HTMLInputElement | null>(null);

const mediaItems = computed(() => mediaData.value?.items ?? []);
const filteredItems = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  return mediaItems.value.filter((item) => {
    const matchesKeyword =
      keyword.length === 0 ||
      item.filename.toLowerCase().includes(keyword) ||
      item.relative_path.toLowerCase().includes(keyword) ||
      item.content_type.toLowerCase().includes(keyword);
    const matchesStatus =
      referenceFilter.value === "all" ||
      (referenceFilter.value === "used" && item.referenced) ||
      (referenceFilter.value === "unused" && !item.referenced);
    return matchesKeyword && matchesStatus && (storageFilter.value === "all" || item.storage === storageFilter.value);
  });
});

const cleanupItems = computed(() => mediaItems.value.filter(item => item.storage === storageFilter.value && !item.referenced && item.cleanup_eligible));
const canCleanup = computed(() => storageFilter.value !== "all" && !searchKeyword.value.trim() && referenceFilter.value !== "used" && cleanupItems.value.length > 0 && !loading.value && (storageFilter.value !== "oss" || mediaData.value?.oss_complete));
const stats = computed(() => {
  const items = filteredItems.value;
  const partial = items.some(item => item.size === null) || (storageFilter.value !== "local" && mediaData.value?.oss_complete === false);
  return [
    { label: "全部文件", value: items.length, helper: "当前筛选结果" },
    { label: "已引用", value: items.filter(item => item.referenced).length, helper: "正在被内容使用" },
    { label: "未引用", value: items.filter(item => !item.referenced).length, helper: "所选存储内可清理" },
    { label: "占用空间", value: formatBytes(items.reduce((sum, item) => sum + (item.size ?? 0), 0)), helper: partial ? "仅统计已知大小，数据不完整" : "当前筛选结果" },
  ];
});

onMounted(() => {
  void loadMediaFiles();
});

async function loadMediaFiles() {
  loading.value = true;
  try {
    mediaData.value = await fetchMediaFiles();
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "媒体资源加载失败"));
  } finally {
    loading.value = false;
  }
}

function triggerUpload() {
  uploadInput.value?.click();
}

async function handleImageSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) {
    return;
  }

  uploading.value = true;
  try {
    const result = await uploadMediaImage(file);
    storageFilter.value = mediaData.value?.upload_storage ?? "all";
    searchKeyword.value = "";
    referenceFilter.value = "all";
    if (!mediaData.value?.oss_complete) {
      ElMessage.info(`上传地址：${result.url}；OSS 列举权限恢复后可在完整列表查看`);
    }
    ElMessage.success("图片上传成功");
    await loadMediaFiles();
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "图片上传失败"));
  } finally {
    uploading.value = false;
    input.value = "";
  }
}

async function handleCleanup() {
  if (!canCleanup.value || storageFilter.value === "all") {
    ElMessage.info("当前没有未引用文件");
    return;
  }

  const storage = storageFilter.value;
  try {
    await ElMessageBox.confirm(
      `将清理${storage === "oss" ? " OSS" : "服务器本地"}的 ${cleanupItems.value.length} 个未引用文件，预计释放 ${formatBytes(
        cleanupItems.value.reduce((sum, item) => sum + (item.size ?? 0), 0),
      )}。清理后无法恢复，是否继续？`,
      "清理未引用文件",
      {
        confirmButtonText: "确认清理",
        cancelButtonText: "取消",
        type: "warning",
      },
    );
  } catch {
    return;
  }

  cleanupLoading.value = true;
  try {
    const result = await cleanupUnreferencedMediaFiles(storage);
    ElMessage.success(`已清理 ${result.deleted_count} 个文件，释放 ${formatBytes(result.deleted_size)}`);
    await loadMediaFiles();
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "未引用文件清理失败"));
    await loadMediaFiles();
  } finally {
    cleanupLoading.value = false;
  }
}

async function copyUrl(url: string) {
  try {
    await navigator.clipboard.writeText(url);
    ElMessage.success("文件链接已复制");
  } catch {
    ElMessage.error("复制失败，请手动打开后复制");
  }
}

function openFile(url: string) {
  window.open(url, "_blank", "noopener,noreferrer");
}

function isImage(item: MediaFileItem) {
  return item.media_type === "image" || item.content_type.startsWith("image/");
}

function getMediaTypeLabel(item: MediaFileItem) {
  if (item.media_type === "image") {
    return "图片";
  }
  if (item.media_type === "resume") {
    return "简历";
  }
  return "文件";
}

function formatBytes(size: number | null) {
  if (size === null) return "未知";
  if (size < 1024) {
    return `${size} B`;
  }
  const units = ["KB", "MB", "GB", "TB"];
  let value = size / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(value >= 10 ? 1 : 2)} ${units[unitIndex]}`;
}

function formatDate(value: string | null) {
  if (!value) return "未知";
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}


</script>

<template>
  <div class="page-stack media-admin-page">
    <PageHeader eyebrow="MEDIA" title="媒体资源管理" description="统一查看上传文件、引用状态与未引用文件清理。" />

    <el-alert v-for="warning in mediaData?.warnings ?? []" :key="warning" :title="warning" type="warning" :closable="false" show-icon />

    <section class="media-stat-grid" aria-label="媒体资源统计">
      <article v-for="item in stats" :key="item.label" class="media-stat-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.helper }}</small>
      </article>
    </section>

    <el-card shadow="never" class="form-card media-manager-card">
      <div class="media-toolbar">
        <div class="media-toolbar-filters">
          <el-input
            v-model="searchKeyword"
            clearable
            placeholder="搜索文件名 / 路径 / 类型"
            class="media-search-input"
          />
          <el-select v-model="storageFilter" class="media-status-select" aria-label="存储来源筛选">
            <el-option label="全部存储" value="all" />
            <el-option label="服务器本地" value="local" />
            <el-option label="OSS" value="oss" />
          </el-select>
          <el-select v-model="referenceFilter" class="media-status-select" aria-label="引用状态筛选">
            <el-option label="全部资源" value="all" />
            <el-option label="已引用" value="used" />
            <el-option label="未引用" value="unused" />
          </el-select>
        </div>
        <div class="media-toolbar-actions">
          <input
            ref="uploadInput"
            class="media-upload-input"
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            @change="handleImageSelected"
          />
          <el-button :icon="Upload" :loading="uploading" @click="triggerUpload">上传图片</el-button>
          <el-button :icon="Refresh" :loading="loading" @click="loadMediaFiles">刷新</el-button>
          <el-button
            type="danger"
            plain
            :icon="Delete"
            :loading="cleanupLoading"
            :disabled="!canCleanup"
            @click="handleCleanup"
          >
            清理{{ storageFilter === "oss" ? " OSS" : storageFilter === "local" ? "本地" : "" }}未引用
          </el-button>
        </div>
      </div>

      <p class="media-muted">上传位置：{{ mediaData?.upload_storage === "oss" ? "OSS" : "服务器本地" }}。清理前请选择一个存储来源并清空搜索，已引用文件不会被清理。</p>
      <el-table
        v-loading="loading"
        :data="filteredItems"
        :row-key="(item: MediaFileItem) => `${item.storage}:${item.relative_path}`"
        class="media-table"
        max-height="620"
        empty-text="暂无媒体文件"
      >
        <el-table-column label="文件" min-width="320">
          <template #default="{ row }">
            <div class="media-file-cell">
              <div class="media-file-preview">
                <ImagePreview v-if="isImage(row)" :src="row.url" :alt="row.filename" />
                <span v-else>{{ getMediaTypeLabel(row).slice(0, 1) }}</span>
              </div>
              <div class="media-file-meta">
                <strong>{{ row.filename }}</strong>
                <span>{{ row.relative_path }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="存储来源" width="120"><template #default="{ row }"><el-tag :type="row.storage === 'oss' ? 'warning' : 'info'">{{ row.storage === "oss" ? "OSS" : "服务器本地" }}</el-tag></template></el-table-column>
        <el-table-column label="类型" width="110">
          <template #default="{ row }">
            <el-tag effect="plain">{{ getMediaTypeLabel(row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="110">
          <template #default="{ row }">{{ formatBytes(row.size) }}</template>
        </el-table-column>
        <el-table-column label="引用状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.referenced ? 'success' : 'danger'" effect="light">
              {{ row.referenced ? "已引用" : "未引用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="引用位置" min-width="260">
          <template #default="{ row }">
            <div v-if="row.references.length > 0" class="media-reference-list">
              <el-tag v-for="reference in row.references.slice(0, 3)" :key="reference.label" effect="plain">
                {{ reference.source }}：{{ reference.label }}
              </el-tag>
              <span v-if="row.references.length > 3" class="media-muted">+{{ row.references.length - 3 }}</span>
            </div>
            <span v-else class="media-muted">未被内容使用</span>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="170">
          <template #default="{ row }">{{ formatDate(row.modified_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="{ row }">
            <el-button text size="small" @click="openFile(row.url)">查看</el-button>
            <el-button text size="small" :icon="CopyDocument" @click="copyUrl(row.url)">复制</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.media-toolbar { flex-wrap: wrap; }
.media-toolbar-filters { flex-wrap: wrap; }
.media-status-select { flex-shrink: 0; }
</style>
