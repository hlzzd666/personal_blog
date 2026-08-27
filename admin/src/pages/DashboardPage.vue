<script setup lang="ts">
import { Collection, DataLine, Document, Star, View } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { computed, onMounted, ref } from "vue";

import { fetchDashboardStats } from "../api/content";
import { resolveErrorMessage } from "../api/http";
import PageHeader from "../components/PageHeader.vue";
import type { DashboardStats } from "../types/content";

const stats = ref<DashboardStats | null>(null);
const loading = ref(false);

const summaryCards = computed(() => [
  { title: "文章", value: stats.value?.article_count ?? 0, description: "当前公开文章总数", icon: Document },
  { title: "总浏览", value: stats.value?.total_views ?? 0, description: "包含后台手动调整值", icon: View },
  { title: "总点赞", value: stats.value?.total_likes ?? 0, description: "包含后台手动调整值", icon: Star },
  { title: "专题 / 动态", value: `${stats.value?.series_count ?? 0} / ${stats.value?.note_count ?? 0}`, description: "专题与短动态内容量", icon: Collection },
]);

function formatDate(value: string | null) {
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium" }).format(new Date(value ?? Date.now()));
}

async function loadStats() {
  loading.value = true;
  try {
    stats.value = await fetchDashboardStats();
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "控制台统计读取失败"));
  } finally {
    loading.value = false;
  }
}

onMounted(loadStats);
</script>

<template>
  <div v-loading="loading" class="page-stack dashboard-page">
    <PageHeader eyebrow="DASHBOARD" title="控制台" description="查看内容规模、累计互动和当前热门文章。" />

    <el-row :gutter="16">
      <el-col v-for="card in summaryCards" :key="card.title" :xs="24" :sm="12" :xl="6">
        <el-card shadow="hover" class="dashboard-stat-card">
          <div class="dashboard-stat-top">
            <div><p class="dashboard-stat-title">{{ card.title }}</p><strong>{{ card.value }}</strong></div>
            <el-icon class="dashboard-stat-icon"><component :is="card.icon" /></el-icon>
          </div>
          <p class="dashboard-stat-text">{{ card.description }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="15">
        <el-card shadow="never" class="dashboard-panel">
          <template #header><div class="panel-header"><span>热门文章</span><el-icon><DataLine /></el-icon></div></template>
          <el-table :data="stats?.top_articles ?? []" empty-text="暂无文章">
            <el-table-column prop="title" label="文章" min-width="260" show-overflow-tooltip />
            <el-table-column prop="category" label="分类" width="100" />
            <el-table-column prop="views" label="浏览" width="82" />
            <el-table-column prop="likes" label="点赞" width="82" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :xl="9">
        <el-card shadow="never" class="dashboard-panel">
          <template #header><div class="panel-header"><span>最近文章</span></div></template>
          <div class="dashboard-recent-list">
            <RouterLink v-for="article in stats?.recent_articles ?? []" :key="article.id" to="/articles">
              <span>{{ article.title }}</span><time>{{ formatDate(article.published_at ?? article.created_at) }}</time>
            </RouterLink>
            <p v-if="!stats?.recent_articles.length" class="dashboard-empty">暂无文章</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
