<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { CopyDocument, Delete, Refresh, Upload } from "@element-plus/icons-vue";

import { cleanupUnreferencedMediaFiles, fetchMediaFiles, uploadMediaImage } from "../api/media";
import PageHeader from "../components/PageHeader.vue";
import type { MediaFileItem, MediaListResponse } from "../types/media";

type MediaFilter = "all" | "used" | "unused";

const mediaData = ref<MediaListResponse | null>(null);
const loading = ref(false);
const cleanupLoading = ref(false);
const uploading = ref(false);
const searchKeyword = ref("");
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
    return matchesKeyword && matchesStatus;
  });
});

const stats = computed(() => [
  { label: "全部文件", value: mediaData.value?.total ?? 0, helper: "上传目录文件数" },
  { label: "已引用", value: mediaData.value?.used_count ?? 0, helper: "正在被内容使用" },
  { label: "未引用", value: mediaData.value?.unused_count ?? 0, helper: "可执行清理" },
  { label: "占用空间", value: formatBytes(mediaData.value?.total_size ?? 0), helper: "当前上传目录" },
]);

onMounted(() => {
  void loadMediaFiles();
});

async function loadMediaFiles() {
  loading.value = true;
  try {
    mediaData.value = await fetchMediaFiles();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "媒体资源加载失败"));
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
    await uploadMediaImage(file);
    ElMessage.success("图片上传成功");
    await loadMediaFiles();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "图片上传失败"));
  } finally {
    uploading.value = false;
    input.value = "";
  }
}

async function handleCleanup() {
  if ((mediaData.value?.unused_count ?? 0) === 0) {
    ElMessage.info("当前没有未引用文件");
    return;
  }

  try {
    await ElMessageBox.confirm(
      `将清理 ${mediaData.value?.unused_count ?? 0} 个未引用文件，预计释放 ${formatBytes(
        mediaData.value?.unused_size ?? 0,
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
    const result = await cleanupUnreferencedMediaFiles();
    ElMessage.success(`已清理 ${result.deleted_count} 个文件，释放 ${formatBytes(result.deleted_size)}`);
    await loadMediaFiles();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "未引用文件清理失败"));
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

function formatBytes(size: number) {
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

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}
</script>

<template>
  <div class="page-stack media-admin-page">
    <PageHeader eyebrow="MEDIA" title="媒体资源管理" description="统一查看上传文件、引用状态与未引用文件清理。" />

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
            :disabled="(mediaData?.unused_count ?? 0) === 0"
            @click="handleCleanup"
          >
            清理未引用
          </el-button>
        </div>
      </div>

      <el-table
        v-loading="loading"
        :data="filteredItems"
        row-key="relative_path"
        class="media-table"
        max-height="620"
        empty-text="暂无媒体文件"
      >
        <el-table-column label="文件" min-width="320">
          <template #default="{ row }">
            <div class="media-file-cell">
              <div class="media-file-preview">
                <img v-if="isImage(row)" :src="row.url" :alt="row.filename" />
                <span v-else>{{ getMediaTypeLabel(row).slice(0, 1) }}</span>
              </div>
              <div class="media-file-meta">
                <strong>{{ row.filename }}</strong>
                <span>{{ row.relative_path }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
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
