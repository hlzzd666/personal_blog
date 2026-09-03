<script setup lang="ts">
import { Delete, Edit, Plus, Search, Upload } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";
import { MdEditor } from "md-editor-v3";
import "md-editor-v3/lib/style.css";

import { createArticle, deleteArticle, fetchManageArticles, updateArticle } from "../api/articles";
import { fetchArticleTaxonomy, fetchSeries } from "../api/content";
import { resolveErrorMessage } from "../api/http";
import { uploadImage } from "../api/site-settings";
import PageHeader from "../components/PageHeader.vue";
import type { Article, ArticlePayload } from "../types/article";
import type { Series, TaxonomyItem } from "../types/content";

const emptyArticle = (): ArticlePayload => ({
  slug: "",
  title: "",
  summary: "",
  content_markdown: "# 新的航行记录\n\n在这里写下今天的发现。",
  cover_image_url: null,
  is_repost: false,
  author: "站长",
  source_url: null,
  published_at: new Date().toISOString().slice(0, 19),
  updated_at: new Date().toISOString().slice(0, 19),
  views: 0,
  likes: 0,
  tags: [],
  category: "随笔",
  category_id: null,
  tag_ids: [],
  series_id: null,
  series_order: null,
});

const articles = ref<Article[]>([]);
const total = ref(0);
const loading = ref(false);
const saving = ref(false);
const drawerVisible = ref(false);
const editingId = ref<number | null>(null);
const searchText = ref("");
const categoryFilter = ref("");
const tagFilter = ref("");
const attributeFilter = ref<"" | "true" | "false">("");
const publishedRange = ref<string[]>([]);
const updatedRange = ref<string[]>([]);
const page = ref(1);
const form = reactive<ArticlePayload>(emptyArticle());
const drawerTitle = computed(() => (editingId.value === null ? "写一篇新文章" : "编辑文章"));
const markdownInput = ref<HTMLInputElement | null>(null);
const importingMarkdown = ref(false);
const seriesOptions = ref<Series[]>([]);
const categoryOptions = ref<TaxonomyItem[]>([]);
const tagOptions = ref<TaxonomyItem[]>([]);
const route = useRoute();
const seriesNameById = computed(() => new Map(seriesOptions.value.map((item) => [item.id, item.title])));

function formatDate(value: string | null) {
  if (!value) return "未设置";
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function getSeriesName(seriesId: number | null) {
  return seriesId === null ? "-" : seriesNameById.value.get(seriesId) ?? "专题已移除";
}

function resetForm() {
  Object.assign(form, emptyArticle());
}

async function loadArticles() {
  loading.value = true;
  try {
    const result = await fetchManageArticles({
      page: page.value,
      page_size: 20,
      search: searchText.value || undefined,
      category: categoryFilter.value || undefined,
      tag: tagFilter.value || undefined,
      is_repost: attributeFilter.value || undefined,
      published_from: publishedRange.value[0],
      published_to: publishedRange.value[1],
      updated_from: updatedRange.value[0],
      updated_to: updatedRange.value[1],
    });
    articles.value = result.items;
    total.value = result.total;
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "文章列表读取失败"));
  } finally {
    loading.value = false;
  }
}

async function loadSeriesOptions() {
  try {
    seriesOptions.value = (await fetchSeries()).items;
  } catch {
    seriesOptions.value = [];
  }
}

async function loadTaxonomyOptions() {
  try {
    const taxonomy = await fetchArticleTaxonomy();
    categoryOptions.value = taxonomy.categories;
    tagOptions.value = taxonomy.tags;
  } catch {
    categoryOptions.value = [];
    tagOptions.value = [];
  }
}

function openCreate() {
  editingId.value = null;
  resetForm();
  const defaultCategory = categoryOptions.value[0];
  if (defaultCategory) {
    form.category_id = defaultCategory.id;
    form.category = defaultCategory.name;
  }
  drawerVisible.value = true;
}

function openEdit(article: Article) {
  editingId.value = article.id;
  Object.assign(form, {
    ...article,
    published_at: article.published_at?.slice(0, 19) ?? null,
    updated_at: article.updated_at?.slice(0, 19) ?? null,
    category_id: article.category_id ?? categoryOptions.value.find((item) => item.name === article.category)?.id ?? null,
    tag_ids: article.tag_ids?.length
      ? [...article.tag_ids]
      : article.tags
          .map((tag) => tagOptions.value.find((item) => item.name === tag)?.id)
          .filter((id): id is number => id !== undefined),
  });
  drawerVisible.value = true;
}

async function saveArticle() {
  const category = categoryOptions.value.find((item) => item.id === form.category_id);
  const selectedTags = tagOptions.value.filter((item) => form.tag_ids.includes(item.id));
  if (!category) {
    ElMessage.warning("请先在分类与标签中维护并选择文章分类");
    return;
  }
  const payload: ArticlePayload = {
    ...form,
    category: category.name,
    category_id: category.id,
    tags: selectedTags.map((tag) => tag.name),
    tag_ids: [...form.tag_ids],
    cover_image_url: form.cover_image_url || null,
    source_url: form.source_url || null,
    series_order: form.series_id === null ? null : form.series_order,
  };
  saving.value = true;

  try {
    if (editingId.value === null) {
      await createArticle(payload);
      ElMessage.success("文章已加入归档");
    } else {
      await updateArticle(editingId.value, payload);
      ElMessage.success("文章已更新");
    }
    drawerVisible.value = false;
    await loadArticles();
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "文章保存失败，请检查表单内容"));
  } finally {
    saving.value = false;
  }
}

async function removeArticle(article: Article) {
  try {
    await ElMessageBox.confirm(`确定删除《${article.title}》吗？此操作不可撤销。`, "删除文章", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });
    await deleteArticle(article.id);
    ElMessage.success("文章已删除");
    await loadArticles();
  } catch (error) {
    if (error !== "cancel" && error !== "close") {
      ElMessage.error(resolveErrorMessage(error, "文章删除失败"));
    }
  }
}

function handlePageChange(nextPage: number) {
  page.value = nextPage;
  void loadArticles();
}

async function handleMarkdownImageUpload(files: File[], insertImages: (urls: string[]) => void) {
  const validFiles = files.filter((file) => {
    if (!file.type.startsWith("image/")) {
      ElMessage.warning(`已跳过非图片文件：${file.name}`);
      return false;
    }
    if (file.size > 10 * 1024 * 1024) {
      ElMessage.warning(`图片不能超过 10 MB：${file.name}`);
      return false;
    }
    return true;
  });

  if (!validFiles.length) {
    return;
  }

  try {
    const results = await Promise.all(validFiles.map((file) => uploadImage(file)));
    insertImages(results.map((result) => result.url));
    ElMessage.success(`已插入 ${results.length} 张图片`);
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "图片上传失败，请稍后重试"));
  }
}

function openMarkdownPicker() {
  markdownInput.value?.click();
}

async function importMarkdown(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) {
    return;
  }

  const filename = file.name.toLowerCase();
  if (!filename.endsWith(".md") && !filename.endsWith(".markdown")) {
    ElMessage.error("请选择 .md 或 .markdown 文件");
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error("Markdown 文件不能超过 5 MB");
    return;
  }

  importingMarkdown.value = true;
  try {
    form.content_markdown = await file.text();
    ElMessage.success("Markdown 内容已导入");
  } catch {
    ElMessage.error("Markdown 文件读取失败");
  } finally {
    importingMarkdown.value = false;
  }
}

onMounted(async () => {
  const querySearch = typeof route.query.search === "string" ? route.query.search : "";
  const queryEdit = typeof route.query.edit === "string" ? Number(route.query.edit) : null;
  searchText.value = querySearch;
  await Promise.all([loadArticles(), loadSeriesOptions()]);
  await loadTaxonomyOptions();
  if (queryEdit !== null && Number.isInteger(queryEdit)) {
    const article = articles.value.find((item) => item.id === queryEdit);
    if (article) openEdit(article);
  }
});
</script>

<template>
  <div class="page-stack articles-admin-page">
    <PageHeader
      eyebrow="LOGBOOK ARCHIVE"
      title="文章归档"
      description="用归档、标签和分类组织每一次靠岸，不再区分草稿与发布状态。"
    />

    <div class="article-toolbar">
      <div class="article-filters">
        <div class="article-filter-primary">
          <el-input v-model="searchText" clearable placeholder="搜索标题、别名或摘要" @keyup.enter="page = 1; loadArticles()">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-button type="primary" :loading="loading" @click="page = 1; loadArticles()">查询</el-button>
        </div>
        <div class="article-filter-options">
          <el-select v-model="categoryFilter" class="article-filter-select" clearable placeholder="按分类筛选" @change="page = 1; loadArticles()">
            <el-option v-for="item in categoryOptions" :key="item.id" :label="item.name" :value="item.name" />
          </el-select>
          <el-select v-model="tagFilter" class="article-filter-select" clearable placeholder="按标签筛选" @change="page = 1; loadArticles()">
            <el-option v-for="item in tagOptions" :key="item.id" :label="item.name" :value="item.name" />
          </el-select>
          <el-select v-model="attributeFilter" class="article-filter-select" clearable placeholder="按属性筛选" @change="page = 1; loadArticles()">
            <el-option label="原创" value="false" />
            <el-option label="转载" value="true" />
          </el-select>
          <el-date-picker
            v-model="publishedRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="发表开始时间"
            end-placeholder="发表结束时间"
            value-format="YYYY-MM-DDTHH:mm:ss"
            format="YYYY年MM月DD日 HH:mm"
            @change="page = 1; loadArticles()"
          />
          <el-date-picker
            v-model="updatedRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="更新开始时间"
            end-placeholder="更新结束时间"
            value-format="YYYY-MM-DDTHH:mm:ss"
            format="YYYY年MM月DD日 HH:mm"
            @change="page = 1; loadArticles()"
          />
        </div>
      </div>
      <el-button class="article-create-button" type="primary" :icon="Plus" @click="openCreate">写入航行记录</el-button>
    </div>

    <el-card shadow="never" class="articles-table-card">
      <el-table v-loading="loading" :data="articles" row-key="id" empty-text="还没有文章，先写下第一段航行记录。">
        <el-table-column label="文章" min-width="300">
          <template #default="{ row }">
            <div class="article-table-title">
              <img v-if="row.cover_image_url" :src="row.cover_image_url" :alt="row.title" />
              <div><strong>{{ row.title }}</strong><span>{{ row.slug }}</span></div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="author" label="作者" width="110" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="110" />
        <el-table-column label="所属专题" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ getSeriesName(row.series_id) }}</template>
        </el-table-column>
        <el-table-column label="标签" min-width="180">
          <template #default="{ row }"><el-tag v-for="tag in row.tags" :key="tag" size="small" effect="plain">{{ tag }}</el-tag></template>
        </el-table-column>
        <el-table-column label="属性" width="90">
          <template #default="{ row }"><el-tag :type="row.is_repost ? 'warning' : 'success'" size="small">{{ row.is_repost ? "转载" : "原创" }}</el-tag></template>
        </el-table-column>
        <el-table-column label="发表时间" width="180"><template #default="{ row }">{{ formatDate(row.published_at) }}</template></el-table-column>
        <el-table-column label="最后更新" width="180"><template #default="{ row }">{{ formatDate(row.updated_at) }}</template></el-table-column>
        <el-table-column label="阅读 / 喜欢" width="120"><template #default="{ row }">{{ row.views }} / {{ row.likes }}</template></el-table-column>
        <el-table-column label="操作" fixed="right" width="130">
          <template #default="{ row }">
            <el-button link type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="removeArticle(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-if="total > 20" v-model:current-page="page" class="article-pagination" layout="prev, pager, next" :page-size="20" :total="total" @current-change="handlePageChange" />
    </el-card>

    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="min(1180px, 100vw)" destroy-on-close>
      <el-form label-position="top" class="article-editor-form" @submit.prevent="saveArticle">
        <div class="editor-form-grid">
          <el-form-item label="文章标题" required><el-input v-model="form.title" placeholder="例如：在潮汐里学习 TypeScript" /></el-form-item>
          <el-form-item label="文章别名" required><el-input v-model="form.slug" placeholder="例如：typescript-学习记录" /></el-form-item>
        </div>
        <el-form-item label="文章摘要"><el-input v-model="form.summary" type="textarea" :rows="2" maxlength="500" show-word-limit /></el-form-item>
        <div class="editor-form-grid">
          <el-form-item label="文章作者"><el-input v-model="form.author" /></el-form-item>
          <el-form-item label="文章分类" required>
            <el-select v-model="form.category_id" placeholder="选择分类">
              <el-option v-for="item in categoryOptions" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </el-form-item>
        </div>
        <div class="editor-form-grid">
          <el-form-item label="所属专题">
            <el-select v-model="form.series_id" clearable placeholder="不加入专题">
              <el-option v-for="item in seriesOptions" :key="item.id" :label="item.title" :value="item.id" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="标签">
          <el-select v-model="form.tag_ids" multiple filterable placeholder="选择标签">
            <el-option v-for="tag in tagOptions" :key="tag.id" :label="tag.name" :value="tag.id" />
          </el-select>
        </el-form-item>
        <el-form-item required>
          <template #label>
            <div class="markdown-field-label">
              <span>Markdown 内容</span>
              <input
                ref="markdownInput"
                class="markdown-import-input"
                type="file"
                accept=".md,.markdown,text/markdown"
                @change="importMarkdown"
              />
              <el-button
                link
                type="primary"
                :loading="importingMarkdown"
                @click="openMarkdownPicker"
              >
                <el-icon><Upload /></el-icon>
                导入 Markdown
              </el-button>
            </div>
          </template>
          <MdEditor
            v-model="form.content_markdown"
            language="zh-CN"
            preview-theme="github"
            :on-upload-img="handleMarkdownImageUpload"
          />
        </el-form-item>
        <div class="editor-form-grid">
          <el-form-item label="发表时间"><el-date-picker v-model="form.published_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" format="YYYY年MM月DD日 HH:mm" placeholder="选择发表时间" :teleported="false" popper-class="article-date-picker-popper" /></el-form-item>
          <el-form-item label="更新时间"><el-date-picker v-model="form.updated_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" format="YYYY年MM月DD日 HH:mm" placeholder="选择更新时间" :teleported="false" popper-class="article-date-picker-popper" /></el-form-item>
        </div>
        <div class="editor-form-grid">
          <el-form-item label="封面图 URL"><el-input v-model="form.cover_image_url" placeholder="可选" /></el-form-item>
          <el-form-item label="转载来源链接"><el-input v-model="form.source_url" :disabled="!form.is_repost" placeholder="开启转载后填写" /></el-form-item>
        </div>
        <el-form-item label="内容属性"><el-checkbox v-model="form.is_repost">这是一篇转载文章</el-checkbox></el-form-item>
        <div class="editor-form-grid">
          <el-form-item label="浏览量"><el-input-number v-model="form.views" :min="0" controls-position="right" /></el-form-item>
          <el-form-item label="点赞数"><el-input-number v-model="form.likes" :min="0" controls-position="right" /></el-form-item>
        </div>
        <div class="drawer-actions"><el-button @click="drawerVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveArticle">保存文章</el-button></div>
      </el-form>
    </el-drawer>
  </div>
</template>
