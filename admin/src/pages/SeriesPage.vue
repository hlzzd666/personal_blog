<script setup lang="ts">
import { Delete, Edit, Picture, Plus, Refresh } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, onMounted, reactive, ref } from "vue";

import { createSeries, deleteSeries, fetchSeries, updateSeries } from "../api/content";
import { resolveErrorMessage } from "../api/http";
import { uploadImage } from "../api/site-settings";
import PageHeader from "../components/PageHeader.vue";
import type { Series, SeriesPayload } from "../types/content";

const emptySeries = (): SeriesPayload => ({
  slug: "",
  title: "",
  description: "",
  cover_image_url: null,
  sort_order: 0,
});

const items = ref<Series[]>([]);
const loading = ref(false);
const saving = ref(false);
const uploading = ref(false);
const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const coverInput = ref<HTMLInputElement | null>(null);
const form = reactive<SeriesPayload>(emptySeries());
const dialogTitle = computed(() => (editingId.value === null ? "创建专题" : "编辑专题"));

async function loadSeries() {
  loading.value = true;
  try {
    items.value = (await fetchSeries()).items;
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "专题列表读取失败"));
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editingId.value = null;
  Object.assign(form, emptySeries());
  dialogVisible.value = true;
}

function openEdit(item: Series) {
  editingId.value = item.id;
  Object.assign(form, {
    slug: item.slug,
    title: item.title,
    description: item.description,
    cover_image_url: item.cover_image_url,
    sort_order: item.sort_order,
  });
  dialogVisible.value = true;
}

async function saveSeries() {
  if (!form.title.trim() || !form.slug.trim()) {
    ElMessage.warning("请填写专题名称和别名");
    return;
  }
  saving.value = true;
  try {
    const payload = { ...form, cover_image_url: form.cover_image_url || null };
    if (editingId.value === null) await createSeries(payload);
    else await updateSeries(editingId.value, payload);
    ElMessage.success(editingId.value === null ? "专题已创建" : "专题已更新");
    dialogVisible.value = false;
    await loadSeries();
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "专题保存失败，请检查表单内容"));
  } finally {
    saving.value = false;
  }
}

async function removeSeries(item: Series) {
  try {
    await ElMessageBox.confirm(
      `删除“${item.title}”后，${item.article_count} 篇文章会解除专题关联，但不会被删除。`,
      "删除专题",
      { type: "warning", confirmButtonText: "删除专题", cancelButtonText: "取消" },
    );
    await deleteSeries(item.id);
    ElMessage.success("专题已删除，文章关联已解除");
    await loadSeries();
  } catch (error) {
    if (error !== "cancel" && error !== "close") {
      ElMessage.error(resolveErrorMessage(error, "专题删除失败"));
    }
  }
}

async function uploadCover(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  uploading.value = true;
  try {
    form.cover_image_url = (await uploadImage(file)).url;
    ElMessage.success("专题封面已上传");
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "封面上传失败"));
  } finally {
    uploading.value = false;
  }
}

onMounted(loadSeries);
</script>

<template>
  <div class="page-stack content-admin-page">
    <PageHeader
      eyebrow="CURATED ROUTES"
      title="专题管理"
      description="组织连续阅读路线。排序值越高，专题在前台列表中越靠前。"
    />

    <div class="content-admin-toolbar">
      <span>共 {{ items.length }} 个专题</span>
      <div>
        <el-button :icon="Refresh" :loading="loading" @click="loadSeries">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">创建专题</el-button>
      </div>
    </div>

    <el-card shadow="never" class="content-table-card">
      <el-table v-loading="loading" :data="items" row-key="id" empty-text="还没有专题。">
        <el-table-column label="专题" min-width="320">
          <template #default="{ row }">
            <div class="series-table-title">
              <div class="series-cover-mini">
                <img v-if="row.cover_image_url" :src="row.cover_image_url" :alt="row.title" />
                <el-icon v-else><Picture /></el-icon>
              </div>
              <div><strong>{{ row.title }}</strong><span>/series/{{ row.slug }}</span></div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="简介" min-width="260" show-overflow-tooltip />
        <el-table-column prop="article_count" label="文章" width="82" />
        <el-table-column prop="sort_order" label="排序" width="82" />
        <el-table-column label="操作" fixed="right" width="142">
          <template #default="{ row }">
            <el-button link type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="removeSeries(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="min(680px, calc(100vw - 32px))" destroy-on-close>
      <el-form label-position="top" @submit.prevent="saveSeries">
        <div class="editor-form-grid">
          <el-form-item label="专题名称" required><el-input v-model="form.title" /></el-form-item>
          <el-form-item label="专题别名" required><el-input v-model="form.slug" placeholder="lowercase-slug" /></el-form-item>
        </div>
        <el-form-item label="专题简介"><el-input v-model="form.description" type="textarea" :rows="4" maxlength="2000" show-word-limit /></el-form-item>
        <div class="editor-form-grid">
          <el-form-item label="封面图 URL"><el-input v-model="form.cover_image_url" clearable /></el-form-item>
          <el-form-item label="前台排序"><el-input-number v-model="form.sort_order" :min="0" :max="100000" controls-position="right" /></el-form-item>
        </div>
        <div class="cover-upload-row">
          <input ref="coverInput" class="media-upload-input" type="file" accept="image/*" @change="uploadCover" />
          <el-button :icon="Picture" :loading="uploading" @click="coverInput?.click()">从媒体上传封面</el-button>
          <img v-if="form.cover_image_url" :src="form.cover_image_url" alt="专题封面预览" />
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveSeries">保存专题</el-button>
      </template>
    </el-dialog>
  </div>
</template>
