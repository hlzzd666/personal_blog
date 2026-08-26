<script setup lang="ts">
import { Delete, Edit, Plus, Search } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, onMounted, reactive, ref } from "vue";
import { MdEditor } from "md-editor-v3";
import "md-editor-v3/lib/style.css";

import { createNote, deleteNote, fetchNotes, updateNote } from "../api/content";
import { uploadImage } from "../api/site-settings";
import PageHeader from "../components/PageHeader.vue";
import type { Note, NotePayload } from "../types/content";

const emptyNote = (): NotePayload => ({
  slug: "",
  content_markdown: "今天记录一个简短想法。",
  tags: [],
  external_url: null,
  published_at: new Date().toISOString().slice(0, 19),
});

const notes = ref<Note[]>([]);
const total = ref(0);
const page = ref(1);
const tagFilter = ref("");
const loading = ref(false);
const saving = ref(false);
const drawerVisible = ref(false);
const editingId = ref<number | null>(null);
const form = reactive<NotePayload>(emptyNote());
const drawerTitle = computed(() => (editingId.value === null ? "发布短动态" : "编辑短动态"));

function formatDate(value: string | null) {
  if (!value) return "未设置";
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function excerpt(markdown: string) {
  return markdown.replace(/[#>*_`[\]()!-]/g, " ").replace(/\s+/g, " ").trim().slice(0, 90);
}

async function loadNotes() {
  loading.value = true;
  try {
    const result = await fetchNotes({ page: page.value, page_size: 20, tag: tagFilter.value || undefined });
    notes.value = result.items;
    total.value = result.total;
  } catch {
    ElMessage.error("短动态读取失败");
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editingId.value = null;
  Object.assign(form, emptyNote());
  drawerVisible.value = true;
}

function openEdit(note: Note) {
  editingId.value = note.id;
  Object.assign(form, {
    slug: note.slug,
    content_markdown: note.content_markdown,
    tags: [...note.tags],
    external_url: note.external_url,
    published_at: note.published_at?.slice(0, 19) ?? null,
  });
  drawerVisible.value = true;
}

async function saveNote() {
  if (!form.slug.trim() || !form.content_markdown.trim()) {
    ElMessage.warning("请填写动态别名和内容");
    return;
  }
  saving.value = true;
  try {
    const payload = {
      ...form,
      tags: form.tags.map((tag) => tag.trim()).filter(Boolean),
      external_url: form.external_url || null,
    };
    if (editingId.value === null) await createNote(payload);
    else await updateNote(editingId.value, payload);
    ElMessage.success(editingId.value === null ? "短动态已发布" : "短动态已更新");
    drawerVisible.value = false;
    await loadNotes();
  } catch {
    ElMessage.error("保存失败，请检查别名或外部链接");
  } finally {
    saving.value = false;
  }
}

async function removeNote(note: Note) {
  try {
    await ElMessageBox.confirm(`确定删除动态“${excerpt(note.content_markdown)}”吗？`, "删除短动态", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });
    await deleteNote(note.id);
    ElMessage.success("短动态已删除");
    await loadNotes();
  } catch (error) {
    if (error !== "cancel" && error !== "close") ElMessage.error("删除失败");
  }
}

async function handleImageUpload(files: File[], insertImages: (urls: string[]) => void) {
  try {
    const validFiles = files.filter((file) => file.type.startsWith("image/") && file.size <= 10 * 1024 * 1024);
    const results = await Promise.all(validFiles.map(uploadImage));
    insertImages(results.map((item) => item.url));
  } catch {
    ElMessage.error("图片上传失败");
  }
}

function changePage(next: number) {
  page.value = next;
  void loadNotes();
}

onMounted(loadNotes);
</script>

<template>
  <div class="page-stack content-admin-page">
    <PageHeader eyebrow="SHORT SIGNALS" title="短动态" description="发布简短 Markdown 记录，通过发布时间控制列表顺序。" />
    <div class="content-admin-toolbar">
      <div class="note-filter">
        <el-input v-model="tagFilter" clearable placeholder="按标签筛选" @keyup.enter="page = 1; loadNotes()">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button :loading="loading" @click="page = 1; loadNotes()">查询</el-button>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreate">发布动态</el-button>
    </div>
    <el-card shadow="never" class="content-table-card">
      <el-table v-loading="loading" :data="notes" row-key="id" empty-text="还没有短动态。">
        <el-table-column label="内容" min-width="340">
          <template #default="{ row }"><div class="note-table-content"><strong>{{ excerpt(row.content_markdown) }}</strong><span>/notes/{{ row.slug }}</span></div></template>
        </el-table-column>
        <el-table-column label="标签" min-width="180">
          <template #default="{ row }"><el-tag v-for="tag in row.tags" :key="tag" size="small" effect="plain">{{ tag }}</el-tag></template>
        </el-table-column>
        <el-table-column label="发布时间" width="190"><template #default="{ row }">{{ formatDate(row.published_at ?? row.created_at) }}</template></el-table-column>
        <el-table-column label="操作" fixed="right" width="142">
          <template #default="{ row }">
            <el-button link type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="removeNote(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-if="total > 20" v-model:current-page="page" layout="prev, pager, next" :page-size="20" :total="total" @current-change="changePage" />
    </el-card>
    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="min(1000px, 100vw)" destroy-on-close>
      <el-form label-position="top" @submit.prevent="saveNote">
        <div class="editor-form-grid">
          <el-form-item label="动态别名" required><el-input v-model="form.slug" placeholder="lowercase-slug" /></el-form-item>
          <el-form-item label="发布时间"><el-date-picker v-model="form.published_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" format="YYYY年MM月DD日 HH:mm" /></el-form-item>
        </div>
        <el-form-item label="标签"><el-select v-model="form.tags" multiple filterable allow-create default-first-option><el-option v-for="tag in form.tags" :key="tag" :label="tag" :value="tag" /></el-select></el-form-item>
        <el-form-item label="外部链接"><el-input v-model="form.external_url" clearable placeholder="可选，https://..." /></el-form-item>
        <el-form-item label="Markdown 内容" required>
          <MdEditor v-model="form.content_markdown" language="zh-CN" preview-theme="github" :on-upload-img="handleImageUpload" />
        </el-form-item>
        <div class="drawer-actions"><el-button @click="drawerVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveNote">保存动态</el-button></div>
      </el-form>
    </el-drawer>
  </div>
</template>
