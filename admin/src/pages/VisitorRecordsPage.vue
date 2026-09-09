<script setup lang="ts">
import { Delete, Refresh, Search } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, onMounted, reactive, ref } from "vue";

import {
  deleteVisitorRecord,
  deleteVisitorRecords,
  fetchVisitorRecords,
} from "../api/visitor-records";
import { resolveErrorMessage } from "../api/http";
import PageHeader from "../components/PageHeader.vue";
import type { VisitorRecord, VisitorRecordListResponse } from "../types/visitor-record";

type DateRange = [string, string] | [];

const data = ref<VisitorRecordListResponse | null>(null);
const records = computed(() => data.value?.items ?? []);
const loading = ref(false);
const page = ref(1);
const filters = reactive({
  ip: "",
  city: "",
  page_path: "",
  date_range: [] as DateRange,
});

const stats = computed(() => [
  { label: "总访问量", value: data.value?.total_visits ?? 0, helper: "永久保存的访问记录" },
  { label: "今日访问", value: data.value?.today_visits ?? 0, helper: "按服务器日期统计" },
  { label: "独立 IP", value: data.value?.unique_ips ?? 0, helper: "原始 IP 去重数量" },
]);

const hasDateRange = computed(() => filters.date_range.length === 2);

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function locationText(record: VisitorRecord) {
  return [record.city, record.region, record.country].filter(Boolean).join(" · ") || "未知";
}

function deviceText(deviceType: string) {
  return {
    desktop: "桌面端",
    mobile: "移动端",
    tablet: "平板",
    bot: "爬虫",
  }[deviceType] ?? deviceType;
}

function queryParams() {
  return {
    page: page.value,
    page_size: 20,
    ip: filters.ip.trim() || undefined,
    city: filters.city.trim() || undefined,
    page_path: filters.page_path.trim() || undefined,
    visited_from: filters.date_range[0] || undefined,
    visited_to: filters.date_range[1] || undefined,
  };
}

async function loadRecords() {
  loading.value = true;
  try {
    data.value = await fetchVisitorRecords(queryParams());
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "访客记录读取失败"));
  } finally {
    loading.value = false;
  }
}

function search() {
  page.value = 1;
  void loadRecords();
}

function resetFilters() {
  filters.ip = "";
  filters.city = "";
  filters.page_path = "";
  filters.date_range = [];
  search();
}

async function removeRecord(record: VisitorRecord) {
  try {
    await ElMessageBox.confirm(
      `确定删除 ${record.ip} 在 ${formatDate(record.visited_at)} 的访问记录吗？`,
      "删除访客记录",
      {
        type: "warning",
        confirmButtonText: "删除",
        cancelButtonText: "取消",
      },
    );
    await deleteVisitorRecord(record.id);
    ElMessage.success("访客记录已删除");
    await loadRecords();
  } catch (error) {
    if (error !== "cancel" && error !== "close") {
      ElMessage.error(resolveErrorMessage(error, "访客记录删除失败"));
    }
  }
}

async function removeByDate() {
  if (!hasDateRange.value) {
    ElMessage.warning("请先选择批量删除的日期范围");
    return;
  }
  try {
    await ElMessageBox.confirm(
      `确定删除 ${filters.date_range[0]} 至 ${filters.date_range[1]} 的全部访客记录吗？此操作无法恢复。`,
      "按日期删除访客记录",
      {
        type: "warning",
        confirmButtonText: "确认删除",
        cancelButtonText: "取消",
      },
    );
    const result = await deleteVisitorRecords(filters.date_range[0], filters.date_range[1]);
    ElMessage.success(`已删除 ${result.deleted_count} 条访客记录`);
    page.value = 1;
    await loadRecords();
  } catch (error) {
    if (error !== "cancel" && error !== "close") {
      ElMessage.error(resolveErrorMessage(error, "批量删除访客记录失败"));
    }
  }
}

onMounted(loadRecords);
</script>

<template>
  <div class="page-stack visitor-records-page">
    <PageHeader eyebrow="VISITOR LOG" title="访客记录" description="查看公开前台访问来源、位置和设备信息。" />

    <section class="media-stat-grid visitor-stat-grid" aria-label="访客记录统计">
      <article v-for="item in stats" :key="item.label" class="media-stat-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.helper }}</small>
      </article>
    </section>

    <el-card shadow="never" class="form-card visitor-records-card">
      <div class="visitor-records-toolbar">
        <div class="visitor-records-filters">
          <el-input v-model="filters.ip" clearable placeholder="搜索 IP" @keyup.enter="search" />
          <el-input v-model="filters.city" clearable placeholder="搜索城市" @keyup.enter="search" />
          <el-input v-model="filters.page_path" clearable placeholder="搜索访问页面" @keyup.enter="search" />
          <el-date-picker
            v-model="filters.date_range"
            type="daterange"
            value-format="YYYY-MM-DD"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            range-separator="至"
            clearable
          />
        </div>
        <div class="visitor-records-actions">
          <el-button :icon="Search" @click="search">查询</el-button>
          <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
          <el-button
            type="danger"
            plain
            :icon="Delete"
            :disabled="!hasDateRange"
            @click="removeByDate"
          >
            按日期删除
          </el-button>
        </div>
      </div>

      <el-table v-loading="loading" :data="records" row-key="id" empty-text="暂无访客记录">
        <el-table-column prop="ip" label="IP 地址" width="150" />
        <el-table-column label="位置" min-width="150">
          <template #default="{ row }">{{ locationText(row) }}</template>
        </el-table-column>
        <el-table-column label="访问页面" min-width="250" show-overflow-tooltip>
          <template #default="{ row }">{{ row.page_path }}</template>
        </el-table-column>
        <el-table-column label="设备" width="100">
          <template #default="{ row }">{{ deviceText(row.device_type) }}</template>
        </el-table-column>
        <el-table-column label="User-Agent" min-width="260" show-overflow-tooltip>
          <template #default="{ row }">{{ row.user_agent || "未知" }}</template>
        </el-table-column>
        <el-table-column label="访问时间" width="175">
          <template #default="{ row }">{{ formatDate(row.visited_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="92">
          <template #default="{ row }">
            <el-button link type="danger" :icon="Delete" @click="removeRecord(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="(data?.total ?? 0) > 20"
        v-model:current-page="page"
        layout="prev, pager, next"
        :page-size="20"
        :total="data?.total ?? 0"
        @current-change="loadRecords"
      />
    </el-card>
  </div>
</template>
