<script setup lang="ts">
import { Connection, MagicStick, Refresh, Select } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { onMounted, reactive, ref } from "vue";

import {
  fetchDailyLearningRuns,
  fetchDailyLearningSettings,
  runDailyLearningNow,
  testDailyLearningAI,
  updateDailyLearningSettings,
} from "../api/daily-learning";
import { ApiError } from "../api/http";
import PageHeader from "../components/PageHeader.vue";
import type {
  DailyLearningRun,
  DailyLearningRunStatus,
  DailyLearningSettingsPayload,
} from "../types/daily-learning";

const form = reactive<DailyLearningSettingsPayload>({
  enabled: false,
  publish_time: "09:00",
  ai_base_url: "",
  ai_model: "",
  api_key: "",
  generation_instructions:
    "题目覆盖 JavaScript、TypeScript、Vue、React、浏览器、CSS、网络、性能和工程化，兼顾基础、中级和高级难度。答案准确、清晰，必要时给出简短代码示例。",
  tags: ["前端面试", "每日问答"],
});
const apiKeyConfigured = ref(false);
const updatedAt = ref("");
const runs = ref<DailyLearningRun[]>([]);
const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const queueing = ref(false);

const statusMeta: Record<DailyLearningRunStatus, { label: string; type: "info" | "warning" | "success" | "danger" }> = {
  pending: { label: "等待执行", type: "info" },
  running: { label: "生成中", type: "warning" },
  succeeded: { label: "已发布", type: "success" },
  failed: { label: "失败", type: "danger" },
};

function errorMessage(error: unknown, fallback: string) {
  return error instanceof ApiError ? error.message : fallback;
}

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
    ai_base_url: settings.ai_base_url,
    ai_model: settings.ai_model,
    api_key: "",
    generation_instructions: settings.generation_instructions,
    tags: [...settings.tags],
  });
  apiKeyConfigured.value = settings.api_key_configured;
  updatedAt.value = settings.updated_at;
}

async function loadRuns(showError = false) {
  try {
    runs.value = (await fetchDailyLearningRuns()).items;
  } catch (error) {
    if (showError) ElMessage.error(errorMessage(error, "运行记录读取失败"));
  }
}

async function loadPage() {
  loading.value = true;
  try {
    await Promise.all([loadSettings(), loadRuns()]);
  } catch (error) {
    ElMessage.error(errorMessage(error, "每日问答配置读取失败"));
  } finally {
    loading.value = false;
  }
}

async function saveSettings() {
  if (!form.ai_base_url || !form.ai_model) {
    ElMessage.warning("请填写 AI 接口地址和模型");
    return;
  }
  if (!apiKeyConfigured.value && !form.api_key?.trim()) {
    ElMessage.warning("请填写 AI API Key");
    return;
  }
  const normalizedTags = [...new Set(form.tags.map((tag) => tag.trim()).filter(Boolean))];
  if (!normalizedTags.length) {
    ElMessage.warning("请至少添加一个文章标签");
    return;
  }
  if (normalizedTags.some((tag) => tag.length > 30)) {
    ElMessage.warning("单个文章标签不能超过 30 个字符");
    return;
  }
  saving.value = true;
  try {
    const result = await updateDailyLearningSettings({
      ...form,
      tags: normalizedTags,
      api_key: form.api_key?.trim() || null,
    });
    form.api_key = "";
    apiKeyConfigured.value = result.api_key_configured;
    updatedAt.value = result.updated_at;
    ElMessage.success("每日问答配置已保存");
  } catch (error) {
    ElMessage.error(errorMessage(error, "配置保存失败"));
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
    ElMessage.error(errorMessage(error, "AI 测试失败"));
  } finally {
    testing.value = false;
  }
}

async function queueNow() {
  try {
    await ElMessageBox.confirm(
      "任务会在约一分钟内生成并直接公开今天的 10 道问答。当天已发布时不会重复创建。",
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
    ElMessage.error(errorMessage(error, "任务加入队列失败"));
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
      description="每天按北京时间自动生成 10 道前端面试题，校验完整后直接发布到“今日份学习”专题。"
    />

    <section class="daily-learning-summary">
      <div>
        <span>任务状态</span>
        <strong>{{ form.enabled ? "自动发布已启用" : "自动发布已停用" }}</strong>
      </div>
      <div>
        <span>每日时间</span>
        <strong>{{ form.publish_time }} · Asia/Shanghai</strong>
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
            <el-form-item label="每日发布时间" required>
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

          <el-form-item label="文章标签" required>
            <el-select
              v-model="form.tags"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="输入后按回车添加标签"
            >
              <el-option v-for="tag in form.tags" :key="tag" :label="tag" :value="tag" />
            </el-select>
            <span class="field-help">每天生成的文章都会使用这些标签，最多 20 个。</span>
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
        <template #header><strong>固定发布规则</strong></template>
        <dl>
          <div><dt>文章标题</dt><dd>YYYY-MM-DD-学习问答</dd></div>
          <div><dt>文章别名</dt><dd>YYYY-MM-DD-学习记录</dd></div>
          <div><dt>文章分类</dt><dd>每日问答</dd></div>
          <div><dt>所属专题</dt><dd>今日份学习</dd></div>
          <div><dt>文章作者</dt><dd>AI自动生成</dd></div>
          <div><dt>文章标签</dt><dd>{{ form.tags.join("、") || "尚未配置" }}</dd></div>
          <div><dt>内容数量</dt><dd>10 道题目与参考答案</dd></div>
          <div><dt>失败策略</dt><dd>最多 3 次，不发布残缺内容</dd></div>
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
.daily-learning-actions { justify-content: flex-start; flex-wrap: wrap; }
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
