<script setup lang="ts">
import { Connection, MagicStick, Refresh, Select } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, onMounted, reactive, ref } from "vue";

import {
  fetchDailyLearningRuns,
  fetchDailyLearningSettings,
  runDailyLearningNow,
  testDailyLearningAI,
  updateDailyLearningSettings,
} from "../api/daily-learning";
import { fetchArticleTaxonomy, fetchSeries } from "../api/content";
import { resolveErrorMessage } from "../api/http";
import PageHeader from "../components/PageHeader.vue";
import type {
  DailyLearningRun,
  DailyLearningRunStatus,
  DailyLearningSettingsPayload,
} from "../types/daily-learning";
import type { Series, TaxonomyItem } from "../types/content";

const form = reactive<DailyLearningSettingsPayload>({
  enabled: false,
  publish_time: "09:00",
  schedule_type: "daily",
  schedule_weekday: null,
  schedule_day: null,
  ai_base_url: "",
  ai_model: "",
  generation_topic: "",
  system_prompt: "",
  api_key: "",
  generation_instructions: "",
  generation_count: 10,
  question_label: "",
  answer_label: "",
  article_title_template: "",
  article_slug_template: "",
  article_summary_template: "",
  author: "",
  series_id: null,
  category_id: null,
  tag_ids: [],
  tags: [],
  max_attempts: 3,
  retry_delays_minutes: [],
});
const apiKeyConfigured = ref(false);
const updatedAt = ref("");
const runs = ref<DailyLearningRun[]>([]);
const seriesOptions = ref<Series[]>([]);
const categoryOptions = ref<TaxonomyItem[]>([]);
const tagOptions = ref<TaxonomyItem[]>([]);
const retryDelaysText = ref("");
const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const queueing = ref(false);

const weekdays = [
  { label: "周一", value: 1 },
  { label: "周二", value: 2 },
  { label: "周三", value: 3 },
  { label: "周四", value: 4 },
  { label: "周五", value: 5 },
  { label: "周六", value: 6 },
  { label: "周日", value: 7 },
];

const selectedCategoryName = computed(() => {
  const category = categoryOptions.value.find((item) => item.id === form.category_id);
  return category?.name ?? (form.category_id ? "配置已失效" : "未配置");
});
const selectedSeriesName = computed(
  () => seriesOptions.value.find((item) => item.id === form.series_id)?.title ?? (form.series_id ? "配置已失效" : "不加入专题"),
);
const selectedTagNames = computed(() =>
  tagOptions.value.filter((item) => form.tag_ids.includes(item.id)).map((item) => item.name),
);
const scheduleSummary = computed(() => {
  if (form.schedule_type === "weekly") {
    return `每周${weekdays.find((item) => item.value === form.schedule_weekday)?.label ?? "待配置"} ${form.publish_time}`;
  }
  if (form.schedule_type === "monthly") {
    return `每月 ${form.schedule_day ?? "待配置"} 日 ${form.publish_time}`;
  }
  return `每日 ${form.publish_time}`;
});

const statusMeta: Record<DailyLearningRunStatus, { label: string; type: "info" | "warning" | "success" | "danger" }> = {
  pending: { label: "等待执行", type: "info" },
  running: { label: "生成中", type: "warning" },
  succeeded: { label: "已发布", type: "success" },
  failed: { label: "失败", type: "danger" },
};

function formatDateTime(value: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
    hour12: false,
  }).format(new Date(value));
}

async function loadSettings() {
  const settings = await fetchDailyLearningSettings();
  Object.assign(form, {
    enabled: settings.enabled,
    publish_time: settings.publish_time.slice(0, 5),
    schedule_type: settings.schedule_type,
    schedule_weekday: settings.schedule_weekday,
    schedule_day: settings.schedule_day,
    ai_base_url: settings.ai_base_url,
    ai_model: settings.ai_model,
    api_key: "",
    generation_topic: settings.generation_topic,
    system_prompt: settings.system_prompt,
    generation_instructions: settings.generation_instructions,
    generation_count: settings.generation_count,
    question_label: settings.question_label,
    answer_label: settings.answer_label,
    article_title_template: settings.article_title_template,
    article_slug_template: settings.article_slug_template,
    article_summary_template: settings.article_summary_template,
    author: settings.author,
    series_id: settings.series_id,
    category_id: settings.category_id,
    tag_ids: [...settings.tag_ids],
    tags: [...settings.tags],
    max_attempts: settings.max_attempts,
    retry_delays_minutes: [...settings.retry_delays_minutes],
  });
  retryDelaysText.value = settings.retry_delays_minutes.join(", ");
  apiKeyConfigured.value = settings.api_key_configured;
  updatedAt.value = settings.updated_at;
}

async function loadOptions() {
  const [taxonomy, series] = await Promise.all([fetchArticleTaxonomy(), fetchSeries()]);
  categoryOptions.value = taxonomy.categories;
  tagOptions.value = taxonomy.tags;
  seriesOptions.value = series.items;
}

async function loadRuns(showError = false) {
  try {
    runs.value = (await fetchDailyLearningRuns()).items;
  } catch (error) {
    if (showError) ElMessage.error(resolveErrorMessage(error, "运行记录读取失败"));
  }
}

async function loadPage() {
  loading.value = true;
  try {
    await Promise.all([loadSettings(), loadOptions(), loadRuns()]);
    if (form.category_id && !categoryOptions.value.some((item) => item.id === form.category_id)) {
      ElMessage.error("当前配置的文章分类不存在，请重新选择分类");
      form.category_id = null;
    }
    const missingTags = form.tag_ids.filter((id) => !tagOptions.value.some((item) => item.id === id));
    if (missingTags.length) {
      ElMessage.error("当前配置中有不存在的文章标签，请重新选择标签");
      form.tag_ids = form.tag_ids.filter((id) => !missingTags.includes(id));
    }
    if (form.series_id && !seriesOptions.value.some((item) => item.id === form.series_id)) {
      ElMessage.error("当前配置的专题不存在，请重新选择专题");
      form.series_id = null;
    }
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "每日问答配置读取失败"));
  } finally {
    loading.value = false;
  }
}

async function saveSettings() {
  if (form.enabled && (!form.ai_base_url || !form.ai_model)) {
    ElMessage.warning("启用自动发布前，请填写 AI 接口地址和模型");
    return;
  }
  if (form.enabled && !apiKeyConfigured.value && !form.api_key?.trim()) {
    ElMessage.warning("请填写 AI API Key");
    return;
  }
  if (!form.category_id) {
    ElMessage.warning("请选择文章分类");
    return;
  }
  if (form.schedule_type === "weekly" && !form.schedule_weekday) {
    ElMessage.warning("每周发布请选择星期几");
    return;
  }
  if (form.schedule_type === "monthly" && !form.schedule_day) {
    ElMessage.warning("每月发布请选择日期");
    return;
  }
  const retryTokens = retryDelaysText.value.trim() ? retryDelaysText.value.split(/[,，\s]+/) : [];
  if (retryTokens.some((value) => !/^\d+$/.test(value))) {
    ElMessage.warning("重试间隔必须填写为整数，例如：10, 30");
    return;
  }
  const retryDelays = retryTokens.map(Number);
  if (retryDelays.some((value) => value < 1 || value > 1440)) {
    ElMessage.warning("重试间隔必须是 1 至 1440 分钟的整数");
    return;
  }
  if (retryDelays.length > form.max_attempts - 1) {
    ElMessage.warning("重试间隔数量不能超过最大尝试次数减一");
    return;
  }
  saving.value = true;
  try {
    const selectedTags = tagOptions.value.filter((item) => form.tag_ids.includes(item.id));
    const result = await updateDailyLearningSettings({
      ...form,
      tags: selectedTags.map((tag) => tag.name),
      retry_delays_minutes: retryDelays,
      api_key: form.api_key?.trim() || null,
    });
    form.api_key = "";
    apiKeyConfigured.value = result.api_key_configured;
    updatedAt.value = result.updated_at;
    ElMessage.success("每日问答配置已保存");
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "配置保存失败"));
  } finally {
    saving.value = false;
  }
}

async function testConnection() {
  testing.value = true;
  try {
    const result = await testDailyLearningAI();
    ElMessage.success(`验证通过：生成 ${result.question_count} 题，耗时 ${result.latency_ms} ms`);
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "AI 测试失败"));
  } finally {
    testing.value = false;
  }
}

async function queueNow() {
  try {
    await ElMessageBox.confirm(
      `任务会在约一分钟内按当前配置生成 ${form.generation_count} 道问答并直接公开。当天已发布时不会重复创建。`,
      "立即生成今日问答",
      { type: "warning", confirmButtonText: "加入队列", cancelButtonText: "取消" },
    );
  } catch {
    return;
  }
  queueing.value = true;
  try {
    const run = await runDailyLearningNow();
    ElMessage.success(run.status === "succeeded" ? "今天的文章已经发布" : "任务已加入队列");
    await loadRuns();
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "任务加入队列失败"));
  } finally {
    queueing.value = false;
  }
}

onMounted(() => {
  void loadPage();
});
</script>

<template>
  <div v-loading="loading" class="page-stack daily-learning-page">
    <PageHeader
      eyebrow="AUTOMATED STUDY LOG"
      title="每日问答"
      description="按当前配置自动生成问答内容，校验完整后直接发布。历史文章不会受配置修改影响。"
    />

    <section class="daily-learning-summary">
      <div>
        <span>任务状态</span>
        <strong>{{ form.enabled ? "自动发布已启用" : "自动发布已停用" }}</strong>
      </div>
      <div>
        <span>发布计划</span>
        <strong>{{ scheduleSummary }} · Asia/Shanghai</strong>
      </div>
      <div>
        <span>API Key</span>
        <strong>{{ apiKeyConfigured ? "已加密配置" : "尚未配置" }}</strong>
      </div>
      <div>
        <span>最近保存</span>
        <strong>{{ formatDateTime(updatedAt || null) }}</strong>
      </div>
    </section>

    <div class="daily-learning-layout">
      <el-card shadow="never" class="daily-learning-config">
        <template #header>
          <div class="panel-header">
            <span>生成与调度配置</span>
            <el-switch v-model="form.enabled" active-text="启用" inactive-text="停用" />
          </div>
        </template>

        <el-form label-position="top" @submit.prevent="saveSettings">
          <div class="daily-learning-fields">
            <el-form-item label="发布周期" required>
              <el-radio-group v-model="form.schedule_type">
                <el-radio-button label="daily">每日</el-radio-button>
                <el-radio-button label="weekly">每周</el-radio-button>
                <el-radio-button label="monthly">每月</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item v-if="form.schedule_type === 'weekly'" label="每周发布日" required>
              <el-select v-model="form.schedule_weekday" placeholder="选择星期">
                <el-option v-for="item in weekdays" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="form.schedule_type === 'monthly'" label="每月发布日" required>
              <el-input-number v-model="form.schedule_day" :min="1" :max="31" controls-position="right" />
              <span class="field-help">当月没有该日期时按当月最后一天执行。</span>
            </el-form-item>
            <el-form-item label="发布时间" required>
              <el-time-select
                v-model="form.publish_time"
                start="00:00"
                step="00:05"
                end="23:55"
                placeholder="选择时间"
              />
            </el-form-item>
            <el-form-item label="AI 模型" required>
              <el-input v-model="form.ai_model" placeholder="例如：deepseek-chat" />
            </el-form-item>
          </div>

          <el-form-item label="OpenAI 兼容接口地址" required>
            <el-input v-model="form.ai_base_url" placeholder="https://api.example.com/v1" />
          </el-form-item>

          <el-form-item label="AI API Key" :required="!apiKeyConfigured">
            <el-input
              v-model="form.api_key"
              type="password"
              show-password
              autocomplete="new-password"
              :placeholder="apiKeyConfigured ? '已配置，留空表示不修改' : '输入 API Key'"
            />
            <span class="field-help">保存后不会再次显示明文；留空会保留当前 Key。</span>
          </el-form-item>

          <div class="daily-learning-fields">
            <el-form-item label="生成主题" required>
              <el-input v-model="form.generation_topic" maxlength="200" />
            </el-form-item>
            <el-form-item label="生成数量" required>
              <el-input-number v-model="form.generation_count" :min="1" :max="20" controls-position="right" />
            </el-form-item>
          </div>

          <el-form-item label="AI 角色设定" required>
            <el-input v-model="form.system_prompt" type="textarea" :rows="3" maxlength="5000" show-word-limit />
          </el-form-item>
          <el-form-item label="生成要求">
            <el-input
              v-model="form.generation_instructions"
              type="textarea"
              :rows="6"
              maxlength="5000"
              show-word-limit
            />
          </el-form-item>

          <div class="daily-learning-fields">
            <el-form-item label="问题标题" required><el-input v-model="form.question_label" maxlength="50" /></el-form-item>
            <el-form-item label="答案标题" required><el-input v-model="form.answer_label" maxlength="50" /></el-form-item>
          </div>

          <div class="daily-learning-fields">
            <el-form-item label="文章标题模板" required><el-input v-model="form.article_title_template" maxlength="200" /></el-form-item>
            <el-form-item label="文章别名模板" required><el-input v-model="form.article_slug_template" maxlength="160" /></el-form-item>
          </div>
          <el-form-item label="文章摘要模板">
            <el-input v-model="form.article_summary_template" type="textarea" :rows="2" maxlength="5000" show-word-limit />
          </el-form-item>

          <div class="daily-learning-fields">
            <el-form-item label="文章作者"><el-input v-model="form.author" maxlength="100" /></el-form-item>
            <el-form-item label="文章分类" required>
              <el-select v-model="form.category_id" placeholder="选择分类" :disabled="!categoryOptions.length">
                <el-option v-for="item in categoryOptions" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
              <span v-if="!categoryOptions.length" class="field-help field-error">暂无分类，请先在“分类与标签”中创建。</span>
            </el-form-item>
          </div>
          <div class="daily-learning-fields">
            <el-form-item label="所属专题">
              <el-select v-model="form.series_id" clearable placeholder="不加入专题">
                <el-option v-for="item in seriesOptions" :key="item.id" :label="item.title" :value="item.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="文章标签">
              <el-select v-model="form.tag_ids" multiple filterable placeholder="选择标签">
                <el-option v-for="item in tagOptions" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
              <span class="field-help">可不选；只能选择“分类与标签”中已维护的标签。</span>
            </el-form-item>
          </div>

          <div class="daily-learning-fields">
            <el-form-item label="最大尝试次数" required>
              <el-input-number v-model="form.max_attempts" :min="1" :max="10" controls-position="right" />
            </el-form-item>
            <el-form-item label="重试间隔（分钟）">
              <el-input v-model="retryDelaysText" placeholder="例如：10, 30" />
              <span class="field-help">按顺序填写，最多为最大尝试次数减一项；每项 1-1440 分钟。</span>
            </el-form-item>
          </div>

          <div class="daily-learning-actions">
            <el-button type="primary" :icon="Select" :loading="saving" @click="saveSettings">
              保存配置
            </el-button>
            <el-button :icon="Connection" :loading="testing" @click="testConnection">
              测试 AI
            </el-button>
            <el-button type="warning" plain :icon="MagicStick" :loading="queueing" @click="queueNow">
              立即生成
            </el-button>
          </div>
        </el-form>
      </el-card>

      <el-card shadow="never" class="daily-learning-rules">
        <template #header><strong>当前生效配置</strong></template>
        <dl>
          <div><dt>发布计划</dt><dd>{{ scheduleSummary }}</dd></div>
          <div><dt>生成主题</dt><dd>{{ form.generation_topic || "未配置" }}</dd></div>
          <div><dt>内容数量</dt><dd>{{ form.generation_count }} 道问答</dd></div>
          <div><dt>文章标题模板</dt><dd>{{ form.article_title_template || "未配置" }}</dd></div>
          <div><dt>文章别名模板</dt><dd>{{ form.article_slug_template || "未配置" }}</dd></div>
          <div><dt>文章分类</dt><dd>{{ selectedCategoryName }}</dd></div>
          <div><dt>所属专题</dt><dd>{{ selectedSeriesName }}</dd></div>
          <div><dt>文章标签</dt><dd>{{ selectedTagNames.join("、") || "未配置" }}</dd></div>
          <div><dt>失败策略</dt><dd>最多 {{ form.max_attempts }} 次，间隔 {{ retryDelaysText || "无" }} 分钟</dd></div>
        </dl>
      </el-card>
    </div>

    <section class="daily-learning-runs">
      <div class="content-admin-toolbar">
        <div>
          <strong>最近运行记录</strong>
        </div>
        <el-button :icon="Refresh" @click="loadRuns(true)">刷新</el-button>
      </div>

      <el-table :data="runs" row-key="id" empty-text="还没有运行记录。">
        <el-table-column prop="run_date" label="日期" width="120" />
        <el-table-column label="状态" width="112">
          <template #default="{ row }">
            <el-tag :type="statusMeta[row.status as DailyLearningRunStatus].type">
              {{ statusMeta[row.status as DailyLearningRunStatus].label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="attempt_count" label="尝试" width="78" />
        <el-table-column label="任务时间" min-width="175">
          <template #default="{ row }">{{ formatDateTime(row.started_at || row.scheduled_for) }}</template>
        </el-table-column>
        <el-table-column label="结果" min-width="280">
          <template #default="{ row }">
            <RouterLink
              v-if="row.article_id && row.article_slug"
              :to="{ path: '/articles', query: { search: row.article_slug, edit: row.article_id } }"
              class="article-result-link"
            >
              {{ row.article_title }}
            </RouterLink>
            <span v-else :class="{ 'run-error': row.last_error }">
              {{ row.last_error || (row.status === 'pending' ? '等待定时器执行' : '正在生成内容') }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="下次重试" min-width="175">
          <template #default="{ row }">{{ formatDateTime(row.next_retry_at) }}</template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<style scoped>
.daily-learning-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border: 1px solid var(--admin-border, #d9e0e6);
  border-radius: 6px;
  background: #fff;
}

.daily-learning-summary > div {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
  padding: 1rem 1.15rem;
  border-right: 1px solid var(--admin-border, #d9e0e6);
}

.daily-learning-summary > div:last-child { border-right: 0; }
.daily-learning-summary span,
.field-help { color: #7a8793; font-size: 0.78rem; }
.daily-learning-summary strong { overflow-wrap: anywhere; color: #263746; font-size: 0.94rem; }

.daily-learning-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(18rem, 0.72fr);
  gap: 1rem;
}

.panel-header,
.content-admin-toolbar,
.daily-learning-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  justify-content: space-between;
}

.daily-learning-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
.daily-learning-fields .el-select,
.daily-learning-fields .el-input-number,
.daily-learning-fields .el-input { width: 100%; }
.daily-learning-actions { justify-content: flex-start; flex-wrap: wrap; }
.field-error { color: #c45656; }
.daily-learning-rules dl { display: grid; gap: 0; margin: 0; }
.daily-learning-rules dl > div { display: grid; gap: 0.25rem; padding: 0.8rem 0; border-bottom: 1px solid #e7ebef; }
.daily-learning-rules dl > div:last-child { border-bottom: 0; }
.daily-learning-rules dt { color: #7a8793; font-size: 0.76rem; }
.daily-learning-rules dd { margin: 0; color: #263746; font-weight: 700; overflow-wrap: anywhere; }
.daily-learning-runs { overflow: hidden; border: 1px solid #d9e0e6; border-radius: 6px; background: #fff; }
.daily-learning-runs .content-admin-toolbar { padding: 0.9rem 1rem; border-bottom: 1px solid #e7ebef; }
.daily-learning-runs .content-admin-toolbar > div { display: grid; gap: 0.2rem; }
.daily-learning-runs .content-admin-toolbar span { color: #7a8793; font-size: 0.76rem; }
.article-result-link { color: #2f6d73; font-weight: 700; text-decoration: none; }
.run-error { color: #c45656; }

@media (max-width: 980px) {
  .daily-learning-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .daily-learning-summary > div:nth-child(2) { border-right: 0; }
  .daily-learning-summary > div:nth-child(-n + 2) { border-bottom: 1px solid #d9e0e6; }
  .daily-learning-layout { grid-template-columns: minmax(0, 1fr); }
}

@media (max-width: 620px) {
  .daily-learning-summary,
  .daily-learning-fields { grid-template-columns: minmax(0, 1fr); }
  .daily-learning-summary > div { border-right: 0; border-bottom: 1px solid #d9e0e6; }
  .daily-learning-summary > div:nth-child(-n + 2) { border-bottom: 1px solid #d9e0e6; }
  .daily-learning-summary > div:last-child { border-bottom: 0; }
  .daily-learning-actions .el-button { width: 100%; margin-left: 0; }
}
</style>
