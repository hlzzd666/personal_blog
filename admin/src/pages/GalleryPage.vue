<script setup lang="ts">
import {
  ArrowDown,
  ArrowUp,
  Delete,
  Edit,
  Picture,
  Plus,
  Refresh,
  Upload,
} from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, onMounted, reactive, ref } from "vue";

import {
  createGalleryCharacter,
  createGalleryChapter,
  deleteGalleryChapter,
  deleteGalleryCharacter,
  fetchManageGallery,
  reorderGalleryCharacters,
  reorderGalleryChapters,
  uploadGalleryImage,
  updateGalleryCharacter,
  updateGalleryChapter,
  updateGallerySettings,
} from "../api/gallery";
import { resolveErrorMessage } from "../api/http";
import PageHeader from "../components/PageHeader.vue";
import type {
  GalleryCharacter,
  GalleryCharacterPayload,
  GalleryChapter,
  GalleryChapterPayload,
  GallerySettingsPayload,
} from "../types/gallery";

const MAX_CHARACTERS = 40;
const emptySettings = (): GallerySettingsPayload => ({
  hall_name: "伟大航路人物档案馆",
  entry_title: "踏入伟大航路，查阅传奇人物档案",
  show_entry: true,
  show_logo: false,
  logo_url: null,
});
const emptyCharacter = (): GalleryCharacterPayload => ({
  name: "",
  epithet: "",
  faction: "",
  bounty: "",
  ability: "",
  description: "",
  quote: "",
  poster_url: null,
  chapter_id: null,
  is_visible: false,
});
const emptyChapter = (): GalleryChapterPayload => ({
  title: "",
  subtitle: "",
  heading: "",
  description: "",
  note: "",
  label: "",
  story: "",
  artwork_index: 0,
  is_visible: true,
});

const loading = ref(false);
const savingSettings = ref(false);
const savingCharacter = ref(false);
const savingOrder = ref(false);
const savingChapter = ref(false);
const savingChapterOrder = ref(false);
const changingChapterId = ref<number | null>(null);
const uploading = ref<"logo" | "poster" | "">("");
const orderDirty = ref(false);
const drawerOpen = ref(false);
const chapterDialogOpen = ref(false);
const editingId = ref<number | null>(null);
const editingChapterId = ref<number | null>(null);
const logoInput = ref<HTMLInputElement | null>(null);
const posterInput = ref<HTMLInputElement | null>(null);
const settingsForm = reactive<GallerySettingsPayload>(emptySettings());
const characterForm = reactive<GalleryCharacterPayload>(emptyCharacter());
const chapterForm = reactive<GalleryChapterPayload>(emptyChapter());
const characters = ref<GalleryCharacter[]>([]);
const chapters = ref<GalleryChapter[]>([]);
const chapterOrderDirty = ref(false);

const drawerTitle = computed(() => (editingId.value === null ? "新增展厅人物" : "编辑展厅人物"));
const chapterDialogTitle = computed(() => (editingChapterId.value === null ? "新增展厅分类" : "编辑展厅分类"));
const countStatus = computed(() => `${characters.value.length} / ${MAX_CHARACTERS}`);
const contentReady = computed(() => characters.value.filter((item) => item.is_visible).length >= 6);

function toPayload(item: GalleryCharacter): GalleryCharacterPayload {
  return {
    name: item.name,
    epithet: item.epithet,
    faction: item.faction,
    bounty: item.bounty,
    ability: item.ability,
    description: item.description,
    quote: item.quote,
    poster_url: item.poster_url,
    chapter_id: item.chapter_id,
    is_visible: item.is_visible,
  };
}

async function loadGallery() {
  loading.value = true;
  try {
    const result = await fetchManageGallery();
    Object.assign(settingsForm, {
      hall_name: result.settings.hall_name,
      entry_title: result.settings.entry_title,
      show_entry: result.settings.show_entry,
      show_logo: result.settings.show_logo,
      logo_url: result.settings.logo_url,
    });
    characters.value = result.characters;
    chapters.value = result.chapters;
    chapterOrderDirty.value = false;
    orderDirty.value = false;
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "展厅内容读取失败"));
  } finally {
    loading.value = false;
  }
}

async function saveSettings() {
  if (!settingsForm.hall_name.trim() || !settingsForm.entry_title.trim()) {
    ElMessage.warning("请填写展厅名称和入口标题");
    return;
  }
  savingSettings.value = true;
  try {
    const result = await updateGallerySettings({
      ...settingsForm,
      logo_url: settingsForm.logo_url || null,
    });
    Object.assign(settingsForm, result);
    ElMessage.success("展厅设置已保存");
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "展厅设置保存失败"));
  } finally {
    savingSettings.value = false;
  }
}

function toChapterPayload(item: GalleryChapter): GalleryChapterPayload {
  return {
    title: item.title,
    subtitle: item.subtitle,
    heading: item.heading,
    description: item.description,
    note: item.note,
    label: item.label,
    story: item.story,
    artwork_index: item.artwork_index,
    is_visible: item.is_visible,
  };
}

function openCreateChapter() {
  editingChapterId.value = null;
  Object.assign(chapterForm, emptyChapter());
  chapterDialogOpen.value = true;
}

function openEditChapter(item: GalleryChapter) {
  editingChapterId.value = item.id;
  Object.assign(chapterForm, toChapterPayload(item));
  chapterDialogOpen.value = true;
}

async function saveChapter() {
  if (savingChapter.value) return;
  if (!chapterForm.title.trim()) {
    ElMessage.warning("请填写分类名称");
    return;
  }
  savingChapter.value = true;
  try {
    if (editingChapterId.value === null) await createGalleryChapter({ ...chapterForm });
    else await updateGalleryChapter(editingChapterId.value, { ...chapterForm });
    ElMessage.success(editingChapterId.value === null ? "展厅分类已创建" : "展厅分类已更新");
    chapterDialogOpen.value = false;
    await loadGallery();
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "展厅分类保存失败"));
  } finally {
    savingChapter.value = false;
  }
}

function moveChapter(index: number, offset: -1 | 1) {
  const target = index + offset;
  if (target < 0 || target >= chapters.value.length) return;
  const next = [...chapters.value];
  [next[index], next[target]] = [next[target], next[index]];
  chapters.value = next;
  chapterOrderDirty.value = true;
}

async function saveChapterOrder() {
  savingChapterOrder.value = true;
  try {
    chapters.value = await reorderGalleryChapters(chapters.value.map((item) => item.id));
    chapterOrderDirty.value = false;
    ElMessage.success("展厅分类顺序已保存");
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "分类顺序保存失败"));
  } finally {
    savingChapterOrder.value = false;
  }
}

async function toggleChapterVisibility(item: GalleryChapter) {
  changingChapterId.value = item.id;
  try {
    const updated = await updateGalleryChapter(item.id, toChapterPayload(item));
    Object.assign(item, updated);
    ElMessage.success(item.is_visible ? "分类已公开" : "分类已隐藏，人物仍在全部馆藏展示");
  } catch (error) {
    item.is_visible = !item.is_visible;
    ElMessage.error(resolveErrorMessage(error, "分类状态更新失败"));
  } finally {
    changingChapterId.value = null;
  }
}

async function removeChapter(item: GalleryChapter) {
  if (characters.value.some((character) => character.chapter_id === item.id)) {
    ElMessage.warning("该分类仍有人物使用，请在人物编辑中调整所属分类后再删除");
    return;
  }
  try {
    await ElMessageBox.confirm(
      `确认删除分类“${item.title}”及其章节文案？`,
      "删除展厅分类",
      { type: "warning", confirmButtonText: "删除分类", cancelButtonText: "取消" },
    );
    await deleteGalleryChapter(item.id);
    ElMessage.success("展厅分类已删除");
    await loadGallery();
  } catch (error) {
    if (error !== "cancel" && error !== "close") ElMessage.error(resolveErrorMessage(error, "分类删除失败"));
  }
}

function openCreate() {
  if (characters.value.length >= MAX_CHARACTERS) {
    ElMessage.warning("展厅最多维护 40 位人物");
    return;
  }
  editingId.value = null;
  Object.assign(characterForm, emptyCharacter());
  drawerOpen.value = true;
}

function openEdit(item: GalleryCharacter) {
  editingId.value = item.id;
  Object.assign(characterForm, toPayload(item));
  drawerOpen.value = true;
}

function validateCharacter() {
  const required = [
    characterForm.name,
    characterForm.epithet,
    characterForm.faction,
    characterForm.bounty,
    characterForm.ability,
    characterForm.description,
    characterForm.quote,
  ];
  if (required.some((value) => !value.trim())) {
    ElMessage.warning("请完整填写人物姓名、档案资料和代表台词");
    return false;
  }
  return true;
}

async function saveCharacter() {
  if (!validateCharacter()) return;
  savingCharacter.value = true;
  try {
    const payload = {
      ...characterForm,
      chapter_id: characterForm.chapter_id || null,
      poster_url: characterForm.poster_url || null,
    };
    if (editingId.value === null) await createGalleryCharacter(payload);
    else await updateGalleryCharacter(editingId.value, payload);
    ElMessage.success(editingId.value === null ? "展厅人物已创建" : "展厅人物已更新");
    drawerOpen.value = false;
    await loadGallery();
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "人物保存失败，请检查表单内容"));
  } finally {
    savingCharacter.value = false;
  }
}

async function toggleVisibility(item: GalleryCharacter) {
  try {
    const updated = await updateGalleryCharacter(item.id, toPayload(item));
    Object.assign(item, updated);
    ElMessage.success(item.is_visible ? "人物已加入公开展厅" : "人物已从公开展厅隐藏");
  } catch (error) {
    item.is_visible = !item.is_visible;
    ElMessage.error(resolveErrorMessage(error, "展示状态更新失败"));
  }
}

function moveCharacter(index: number, offset: -1 | 1) {
  const target = index + offset;
  if (target < 0 || target >= characters.value.length) return;
  const next = [...characters.value];
  [next[index], next[target]] = [next[target], next[index]];
  characters.value = next;
  orderDirty.value = true;
}

async function saveOrder() {
  savingOrder.value = true;
  try {
    characters.value = await reorderGalleryCharacters(characters.value.map((item) => item.id));
    orderDirty.value = false;
    ElMessage.success("人物展示顺序已保存");
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "人物顺序保存失败，请刷新后重试"));
  } finally {
    savingOrder.value = false;
  }
}

async function removeCharacter(item: GalleryCharacter) {
  try {
    await ElMessageBox.confirm(
      `确认删除“${item.name}”？人物资料会从展厅中永久移除。`,
      "删除展厅人物",
      { type: "warning", confirmButtonText: "删除人物", cancelButtonText: "取消" },
    );
    await deleteGalleryCharacter(item.id);
    ElMessage.success("展厅人物已删除");
    await loadGallery();
  } catch (error) {
    if (error !== "cancel" && error !== "close") {
      ElMessage.error(resolveErrorMessage(error, "人物删除失败"));
    }
  }
}

async function inspectPosterDimensions(file: File) {
  const objectUrl = URL.createObjectURL(file);
  try {
    const image = new Image();
    image.src = objectUrl;
    await image.decode();
    const ratio = image.naturalWidth / image.naturalHeight;
    const warnings: string[] = [];
    if (Math.abs(ratio - 2 / 3) > 0.04) {
      warnings.push("海报不是推荐的 2:3 竖版比例，前台会居中裁切");
    }
    if (image.naturalWidth < 1200 || image.naturalHeight < 1800) {
      warnings.push("海报低于建议的 1200 × 1800，近距离观看可能不够清晰");
    }
    if (warnings.length) ElMessage.warning(warnings.join("；"));
  } catch {
    // 上传接口会继续执行自身的文件校验。
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

async function uploadSelected(kind: "logo" | "poster", event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  if (kind === "poster") await inspectPosterDimensions(file);
  uploading.value = kind;
  try {
    const result = await uploadGalleryImage(kind, file);
    if (kind === "logo") {
      settingsForm.logo_url = result.url;
    } else {
      characterForm.poster_url = result.url;
    }
    ElMessage.success(kind === "logo" ? "Logo 已上传，请保存设置" : "人物海报已上传");
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "图片上传失败"));
  } finally {
    uploading.value = "";
  }
}

onMounted(loadGallery);
</script>

<template>
  <div class="page-stack gallery-admin-page">
    <PageHeader
      eyebrow="GRAND LINE ARCHIVE"
      title="3D 展厅"
      description="维护展厅入口与人物档案。启用的人物会按当前顺序进入公开展厅。"
    />

    <section class="gallery-settings-panel" aria-labelledby="gallery-settings-title">
      <div class="gallery-panel-heading">
        <div>
          <h3 id="gallery-settings-title">展厅入口</h3>
          <p>名称和入口标题会显示在访客进入 3D 场景前。</p>
        </div>
        <div class="gallery-panel-actions">
          <el-button type="primary" :loading="savingSettings" @click="saveSettings">保存入口设置</el-button>
        </div>
      </div>
      <el-form label-position="top" @submit.prevent="saveSettings">
        <div class="gallery-settings-grid">
          <el-form-item label="展厅名称" required>
            <el-input v-model="settingsForm.hall_name" maxlength="120" show-word-limit />
          </el-form-item>
          <el-form-item label="入口标题" required>
            <el-input v-model="settingsForm.entry_title" maxlength="200" show-word-limit />
          </el-form-item>
        </div>
        <div class="gallery-logo-row">
          <div class="gallery-logo-preview">
            <img v-if="settingsForm.logo_url" :src="settingsForm.logo_url" alt="展厅 Logo 预览" />
            <el-icon v-else><Picture /></el-icon>
          </div>
          <div class="gallery-logo-actions">
            <el-switch v-model="settingsForm.show_logo" active-text="在入口显示 Logo" />
            <input ref="logoInput" class="media-upload-input" type="file" accept="image/jpeg,image/png,image/webp" @change="uploadSelected('logo', $event)" />
            <el-button :icon="Upload" :loading="uploading === 'logo'" @click="logoInput?.click()">上传 Logo</el-button>
            <el-button v-if="settingsForm.logo_url" @click="settingsForm.logo_url = null">移除 Logo</el-button>
          </div>
        </div>
        <div class="gallery-entry-visibility-row">
          <el-switch
            v-model="settingsForm.show_entry"
            active-text="在前台显示展厅入口"
            inactive-text="隐藏展厅入口"
          />
          <small>关闭后仅隐藏前台导航和首页快捷入口，不会删除展厅内容。</small>
        </div>
      </el-form>
    </section>

    <section class="gallery-settings-panel gallery-chapters-panel" aria-labelledby="gallery-chapters-title">
      <div class="gallery-panel-heading">
        <div>
          <h3 id="gallery-chapters-title">人物分类标签</h3>
          <p>在人物编辑中选择所属分类。隐藏标签后，人物仍出现在“全部馆藏”；分类被引用时不能删除。</p>
        </div>
        <div class="gallery-panel-actions">
          <el-button :disabled="!chapterOrderDirty" :loading="savingChapterOrder" @click="saveChapterOrder">保存分类顺序</el-button>
          <el-button type="primary" :icon="Plus" :disabled="loading || chapters.length >= 20" @click="openCreateChapter">新增分类</el-button>
        </div>
      </div>
      <el-table v-loading="loading" :data="chapters" row-key="id" empty-text="还没有分类标签，点击“新增分类”开始维护。">
        <el-table-column label="顺序" width="78"><template #default="{ $index }"><span class="gallery-slot-number">{{ String($index + 1).padStart(2, "0") }}</span></template></el-table-column>
        <el-table-column prop="title" label="标签名称" min-width="150" />
        <el-table-column prop="subtitle" label="副标题" min-width="250" show-overflow-tooltip />
        <el-table-column label="人物数" width="90"><template #default="{ row }">{{ characters.filter(character => character.chapter_id === row.id).length }}</template></el-table-column>
        <el-table-column label="公开" width="90"><template #default="{ row }"><el-switch v-model="row.is_visible" :aria-label="'公开分类' + row.title" :disabled="changingChapterId !== null" :loading="changingChapterId === row.id" @change="toggleChapterVisibility(row)" /></template></el-table-column>
        <el-table-column label="排序" width="106"><template #default="{ row, $index }"><div class="gallery-order-actions"><el-button circle size="small" :icon="ArrowUp" :aria-label="'上移分类' + row.title" :disabled="$index === 0 || savingChapterOrder" @click="moveChapter($index, -1)" /><el-button circle size="small" :icon="ArrowDown" :aria-label="'下移分类' + row.title" :disabled="$index === chapters.length - 1 || savingChapterOrder" @click="moveChapter($index, 1)" /></div></template></el-table-column>
        <el-table-column label="操作" width="142" fixed="right"><template #default="{ row }"><el-button link type="primary" :icon="Edit" @click="openEditChapter(row)">编辑</el-button><el-button link type="danger" :icon="Delete" @click="removeChapter(row)">删除</el-button></template></el-table-column>
      </el-table>
    </section>

    <div class="gallery-admin-toolbar">
      <div>
        <strong>{{ countStatus }}</strong>
        <span :class="{ warning: !contentReady }">
          {{ contentReady ? "公开展厅内容充足" : "建议至少启用 6 位人物" }}
        </span>
      </div>
      <div class="gallery-toolbar-actions">
        <el-button :icon="Refresh" :loading="loading" @click="loadGallery">刷新</el-button>
        <el-button :disabled="!orderDirty" :loading="savingOrder" @click="saveOrder">保存顺序</el-button>
        <el-button type="primary" :icon="Plus" :disabled="characters.length >= MAX_CHARACTERS" @click="openCreate">新增人物</el-button>
      </div>
    </div>

    <el-card shadow="never" class="content-table-card gallery-table-card">
      <el-table v-loading="loading" :data="characters" row-key="id" empty-text="还没有人物，创建后即可开始布展。">
        <el-table-column label="展位" width="78">
          <template #default="{ $index }"><span class="gallery-slot-number">{{ String($index + 1).padStart(2, "0") }}</span></template>
        </el-table-column>
        <el-table-column label="人物" min-width="250">
          <template #default="{ row }">
            <div class="gallery-character-cell">
              <div class="gallery-poster-mini">
                <img v-if="row.poster_url" :src="row.poster_url" :alt="`${row.name}海报`" />
                <span v-else>{{ row.name.slice(0, 1) }}</span>
              </div>
              <div><strong>{{ row.name }}</strong><span>{{ row.epithet }}</span></div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="faction" label="势力" min-width="140" show-overflow-tooltip />
        <el-table-column label="所属分类" min-width="140"><template #default="{ row }">{{ chapters.find(chapter => chapter.id === row.chapter_id)?.title || '未分类' }}</template></el-table-column>
        <el-table-column prop="bounty" label="悬赏" min-width="150" show-overflow-tooltip />
        <el-table-column label="公开展示" width="112">
          <template #default="{ row }"><el-switch v-model="row.is_visible" @change="toggleVisibility(row)" /></template>
        </el-table-column>
        <el-table-column label="顺序" width="106">
          <template #default="{ $index }">
            <div class="gallery-order-actions">
              <el-tooltip content="上移" placement="top"><el-button circle size="small" :icon="ArrowUp" :disabled="$index === 0" @click="moveCharacter($index, -1)" /></el-tooltip>
              <el-tooltip content="下移" placement="top"><el-button circle size="small" :icon="ArrowDown" :disabled="$index === characters.length - 1" @click="moveCharacter($index, 1)" /></el-tooltip>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="142">
          <template #default="{ row }">
            <el-button link type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="removeCharacter(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer v-model="drawerOpen" :title="drawerTitle" size="min(720px, 94vw)" destroy-on-close>
      <el-form class="gallery-character-form" label-position="top" @submit.prevent="saveCharacter">
        <div class="gallery-character-editor">
          <div class="gallery-poster-editor">
            <div class="gallery-poster-preview">
              <img v-if="characterForm.poster_url" :src="characterForm.poster_url" alt="人物海报预览" />
              <div v-else><span>WANTED</span><strong>{{ characterForm.name || "人物海报" }}</strong></div>
            </div>
            <input ref="posterInput" class="media-upload-input" type="file" accept="image/jpeg,image/png,image/webp" @change="uploadSelected('poster', $event)" />
            <el-button :icon="Upload" :loading="uploading === 'poster'" @click="posterInput?.click()">上传 2:3 海报</el-button>
            <el-button v-if="characterForm.poster_url" @click="characterForm.poster_url = null">使用占位海报</el-button>
            <small>建议至少 1200 × 1800，单张不超过 10 MB。</small>
          </div>
          <div class="gallery-character-fields">
            <div class="editor-form-grid">
              <el-form-item label="姓名" required><el-input v-model="characterForm.name" maxlength="80" /></el-form-item>
              <el-form-item label="称号" required><el-input v-model="characterForm.epithet" maxlength="120" /></el-form-item>
            </div>
            <div class="editor-form-grid">
              <el-form-item label="所属势力" required><el-input v-model="characterForm.faction" maxlength="120" /></el-form-item>
              <el-form-item label="悬赏" required><el-input v-model="characterForm.bounty" maxlength="120" placeholder="例如：30亿贝里或未知" /></el-form-item>
            </div>
            <el-form-item label="人物分类标签">
              <el-select v-model="characterForm.chapter_id" clearable placeholder="未分类" style="width: 100%">
                <el-option v-for="chapter in chapters" :key="chapter.id" :label="chapter.title + (chapter.is_visible ? '' : '（已隐藏）')" :value="chapter.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="能力" required><el-input v-model="characterForm.ability" maxlength="500" show-word-limit /></el-form-item>
            <el-form-item label="人物简介" required><el-input v-model="characterForm.description" type="textarea" :rows="5" maxlength="5000" show-word-limit /></el-form-item>
            <el-form-item label="代表台词" required><el-input v-model="characterForm.quote" type="textarea" :rows="3" maxlength="500" show-word-limit /></el-form-item>
            <el-form-item label="公开状态">
              <el-switch v-model="characterForm.is_visible" active-text="保存后在展厅展示" inactive-text="保存后保持隐藏" />
            </el-form-item>
          </div>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="drawerOpen = false">取消</el-button>
        <el-button type="primary" :loading="savingCharacter" @click="saveCharacter">保存人物</el-button>
      </template>
    </el-drawer>

    <el-dialog v-model="chapterDialogOpen" :title="chapterDialogTitle" width="min(720px, calc(100vw - 32px))" destroy-on-close>
      <el-form label-position="top" @submit.prevent="saveChapter">
        <div class="editor-form-grid">
          <el-form-item label="标签名称" required><el-input v-model="chapterForm.title" maxlength="80" /></el-form-item>
          <el-form-item label="章节短标识（选填）"><el-input v-model="chapterForm.label" maxlength="120" placeholder="例如：梦想起点" /></el-form-item>
        </div>
        <el-form-item label="章节插画"><el-select v-model="chapterForm.artwork_index"><el-option label="航海总览" :value="0" /><el-option label="东海启航" :value="1" /><el-option label="伟大航路" :value="2" /><el-option label="新世界" :value="3" /></el-select></el-form-item>
        <el-form-item label="副标题（选填）"><el-input v-model="chapterForm.subtitle" maxlength="200" /></el-form-item>
        <el-form-item label="章节标题（选填）"><el-input v-model="chapterForm.heading" type="textarea" :rows="2" maxlength="200" placeholder="留空使用分类名称，可按回车换行" /></el-form-item>
        <el-form-item label="序厅说明（选填）"><el-input v-model="chapterForm.description" type="textarea" :rows="3" maxlength="500" /></el-form-item>
        <el-form-item label="入口提示（选填）"><el-input v-model="chapterForm.note" maxlength="300" /></el-form-item>
        <el-form-item label="章节故事（选填）"><el-input v-model="chapterForm.story" type="textarea" :rows="5" maxlength="5000" show-word-limit /></el-form-item>
        <el-form-item label="公开状态"><el-switch v-model="chapterForm.is_visible" active-text="在前台显示此标签" inactive-text="暂时隐藏此标签" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="chapterDialogOpen = false">取消</el-button><el-button type="primary" :loading="savingChapter" @click="saveChapter">保存分类</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.gallery-admin-page {
  min-width: 0;
}

.gallery-settings-panel {
  padding: 1.25rem;
  border: 1px solid var(--admin-border);
  border-radius: 8px;
  background: var(--admin-surface);
  box-shadow: var(--admin-shadow);
}

.gallery-panel-heading,
.gallery-admin-toolbar,
.gallery-logo-row,
.gallery-logo-actions,
.gallery-panel-actions,
.gallery-toolbar-actions,
.gallery-character-cell,
.gallery-order-actions {
  display: flex;
  align-items: center;
}

.gallery-panel-heading,
.gallery-admin-toolbar {
  justify-content: space-between;
  gap: 1rem;
}

.gallery-panel-actions {
  justify-content: flex-end;
  gap: 0.65rem;
}

.gallery-panel-heading {
  margin-bottom: 1rem;
  padding-bottom: 0.9rem;
  border-bottom: 1px solid var(--admin-border);
}

.gallery-panel-heading h3,
.gallery-panel-heading p {
  margin: 0;
}

.gallery-panel-heading h3 {
  color: var(--admin-ink);
  font-size: 1rem;
}

.gallery-panel-heading p,
.gallery-logo-actions small,
.gallery-poster-editor small {
  color: var(--admin-muted);
  font-size: 0.78rem;
}

.gallery-panel-heading p {
  margin-top: 0.3rem;
}

.gallery-settings-grid {
  display: grid;
  grid-template-columns: 0.8fr 1.2fr;
  gap: 1rem;
}

.gallery-logo-row {
  gap: 1rem;
}

.gallery-entry-visibility-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--admin-border);
}

.gallery-entry-visibility-row small {
  color: var(--admin-muted);
  font-size: 0.78rem;
}

.gallery-logo-preview {
  display: grid;
  flex: 0 0 150px;
  place-items: center;
  width: 150px;
  height: 76px;
  overflow: hidden;
  border: 1px solid var(--admin-border);
  border-radius: 7px;
  background: #f6f8fa;
  color: var(--admin-muted);
}

.gallery-logo-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.gallery-logo-actions,
.gallery-toolbar-actions,
.gallery-order-actions {
  flex-wrap: wrap;
  gap: 0.55rem;
}

.gallery-admin-toolbar > div:first-child {
  display: grid;
  gap: 0.25rem;
}

.gallery-admin-toolbar strong {
  color: var(--admin-ink);
  font: 700 1.15rem "IBM Plex Mono", monospace;
}

.gallery-admin-toolbar span {
  color: #3d9266;
  font-size: 0.78rem;
}

.gallery-admin-toolbar span.warning {
  color: #a96623;
}

.gallery-table-card {
  overflow: hidden;
}

.gallery-slot-number {
  color: #a96623;
  font: 700 0.82rem "IBM Plex Mono", monospace;
}

.gallery-character-cell {
  gap: 0.75rem;
  min-width: 0;
}

.gallery-character-cell > div:last-child {
  min-width: 0;
}

.gallery-character-cell strong,
.gallery-character-cell span {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.gallery-character-cell span {
  margin-top: 0.2rem;
  color: var(--admin-muted);
  font-size: 0.75rem;
}

.gallery-poster-mini {
  display: grid;
  flex: 0 0 42px;
  place-items: center;
  width: 42px;
  aspect-ratio: 2 / 3;
  overflow: hidden;
  border: 1px solid #d9e1e7;
  border-radius: 4px;
  background: #173959;
  color: #e0b668;
  font-weight: 800;
}

.gallery-poster-mini img,
.gallery-poster-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.gallery-character-editor {
  display: grid;
  grid-template-columns: 210px minmax(0, 1fr);
  gap: 1.5rem;
  align-items: start;
}

.gallery-poster-editor {
  display: grid;
  gap: 0.65rem;
}

.gallery-poster-preview {
  aspect-ratio: 2 / 3;
  overflow: hidden;
  border: 1px solid #d7c398;
  border-radius: 6px;
  background: #e9ddbd;
}

.gallery-poster-preview > div {
  display: grid;
  height: 100%;
  place-content: center;
  padding: 1rem;
  color: #654828;
  text-align: center;
}

.gallery-poster-preview span {
  font: 700 0.75rem "IBM Plex Mono", monospace;
}

.gallery-poster-preview strong {
  margin-top: 0.6rem;
  font-size: 1.3rem;
}

@media (max-width: 860px) {
  .gallery-panel-heading,
  .gallery-admin-toolbar,
  .gallery-logo-row,
  .gallery-entry-visibility-row,
  .gallery-panel-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .gallery-settings-grid,
  .gallery-character-editor {
    grid-template-columns: 1fr;
  }

  .gallery-logo-preview,
  .gallery-poster-editor {
    width: 100%;
  }

  .gallery-poster-preview {
    width: min(210px, 100%);
  }
}
</style>
