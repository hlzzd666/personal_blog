<script setup lang="ts">
import { Delete, Edit, Plus, Refresh } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, onMounted, reactive, ref } from "vue";

import {
  createArticleCategory,
  createArticleTag,
  deleteArticleCategory,
  deleteArticleTag,
  fetchArticleTaxonomy,
  updateArticleCategory,
  updateArticleTag,
} from "../api/content";
import { resolveErrorMessage } from "../api/http";
import PageHeader from "../components/PageHeader.vue";
import type { ArticleTaxonomy, TaxonomyItem, TaxonomyPayload } from "../types/content";

type TaxonomyKind = "category" | "tag";

const data = ref<ArticleTaxonomy>({ categories: [], tags: [] });
const loading = ref(false);
const saving = ref(false);
const dialogVisible = ref(false);
const editing = ref<TaxonomyItem | null>(null);
const kind = ref<TaxonomyKind>("category");
const form = reactive<TaxonomyPayload>({ name: "", sort_order: 0 });
const currentItems = computed(() => (kind.value === "category" ? data.value.categories : data.value.tags));
const dialogTitle = computed(() => `${editing.value ? "编辑" : "新增"}${kind.value === "category" ? "分类" : "标签"}`);

async function loadTaxonomy() {
  loading.value = true;
  try {
    data.value = await fetchArticleTaxonomy();
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "分类和标签读取失败"));
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editing.value = null;
  Object.assign(form, { name: "", sort_order: 0 });
  dialogVisible.value = true;
}

function openEdit(item: TaxonomyItem) {
  editing.value = item;
  Object.assign(form, { name: item.name, sort_order: item.sort_order });
  dialogVisible.value = true;
}

function changeKind(nextKind: TaxonomyKind) {
  kind.value = nextKind;
  editing.value = null;
}

async function saveItem() {
  if (!form.name.trim()) {
    ElMessage.warning("请输入名称");
    return;
  }
  saving.value = true;
  try {
    const payload = { name: form.name.trim(), sort_order: form.sort_order };
    if (kind.value === "category") {
      if (editing.value) await updateArticleCategory(editing.value.id, payload);
      else await createArticleCategory(payload);
    } else if (editing.value) await updateArticleTag(editing.value.id, payload);
    else await createArticleTag(payload);
    ElMessage.success(`${kind.value === "category" ? "分类" : "标签"}${editing.value ? "已更新" : "已创建"}`);
    dialogVisible.value = false;
    await loadTaxonomy();
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "保存失败，请检查名称是否重复"));
  } finally {
    saving.value = false;
  }
}

async function removeItem(item: TaxonomyItem) {
  const label = kind.value === "category" ? "分类" : "标签";
  try {
    await ElMessageBox.confirm(
      item.article_count ? `${label}“${item.name}”正在被 ${item.article_count} 篇文章使用，不能删除。` : `确定删除${label}“${item.name}”吗？`,
      `删除${label}`,
      { type: item.article_count ? "warning" : "info", confirmButtonText: item.article_count ? "知道了" : "删除", cancelButtonText: "取消" },
    );
  } catch {
    return;
  }
  if (item.article_count) return;
  try {
    if (kind.value === "category") await deleteArticleCategory(item.id);
    else await deleteArticleTag(item.id);
    ElMessage.success(`${label}已删除`);
    await loadTaxonomy();
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, `${label}删除失败`));
  }
}

onMounted(loadTaxonomy);
</script>

<template>
  <div class="page-stack content-admin-page taxonomy-admin-page">
    <PageHeader eyebrow="ARTICLE TAXONOMY" title="分类与标签" description="统一维护文章分类和标签，文章编辑时只选择已登记的内容。" />

    <el-card shadow="never" class="form-card taxonomy-card">
      <div class="taxonomy-toolbar">
        <el-tabs :model-value="kind" @update:model-value="changeKind">
          <el-tab-pane label="分类" name="category" />
          <el-tab-pane label="标签" name="tag" />
        </el-tabs>
        <div class="taxonomy-actions">
          <el-button :icon="Refresh" :loading="loading" @click="loadTaxonomy">刷新</el-button>
          <el-button type="primary" :icon="Plus" @click="openCreate">新增{{ kind === "category" ? "分类" : "标签" }}</el-button>
        </div>
      </div>

      <el-table v-loading="loading" :data="currentItems" row-key="id" empty-text="还没有维护项。">
        <el-table-column prop="name" :label="kind === 'category' ? '分类名称' : '标签名称'" min-width="260" />
        <el-table-column prop="sort_order" label="排序" width="120" />
        <el-table-column prop="article_count" label="引用文章" width="130" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="removeItem(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="min(520px, calc(100vw - 32px))" destroy-on-close>
      <el-form label-position="top" @submit.prevent="saveItem">
        <el-form-item :label="kind === 'category' ? '分类名称' : '标签名称'" required>
          <el-input v-model="form.name" maxlength="80" show-word-limit />
        </el-form-item>
        <el-form-item label="排序值">
          <el-input-number v-model="form.sort_order" :min="0" :max="100000" controls-position="right" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveItem">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
