<script setup lang="ts">
import { Delete, Edit, Refresh, Search } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, onMounted, ref } from "vue";

import { fetchManageGuestbook, updateGuestbookReply, updateGuestbookStatus, type GuestbookItem, type GuestbookStatus } from "../api/guestbook";
import { resolveErrorMessage } from "../api/http";
import PageHeader from "../components/PageHeader.vue";

const data = ref<{ items: GuestbookItem[]; total: number; pending_count: number } | null>(null);
const loading = ref(false);
const page = ref(1);
const status = ref<GuestbookStatus | "">("pending");
const keyword = ref("");
const replyVisible = ref(false);
const replyTarget = ref<GuestbookItem | null>(null);
const reply = ref("");
const savingReply = ref(false);
const items = computed(() => data.value?.items ?? []);

const statusLabels: Record<GuestbookStatus, string> = { pending: "待审核", approved: "已通过", rejected: "已拒绝", spam: "垃圾", deleted: "已删除" };
const statusTypes: Record<GuestbookStatus, "warning" | "success" | "danger" | "info"> = { pending: "warning", approved: "success", rejected: "info", spam: "danger", deleted: "danger" };
function statusLabel(value: string) { return statusLabels[value as GuestbookStatus] ?? value; }
function statusType(value: string) { return statusTypes[value as GuestbookStatus] ?? "info"; }

function formatDate(value: string) { return new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)); }
function excerpt(value: string) { return value.length > 100 ? `${value.slice(0, 100)}…` : value; }
async function load() {
  loading.value = true;
  try { data.value = await fetchManageGuestbook({ page: page.value, page_size: 20, status: status.value || undefined, keyword: keyword.value.trim() || undefined }); }
  catch (error) { ElMessage.error(resolveErrorMessage(error, "留言读取失败")); }
  finally { loading.value = false; }
}
function search() { page.value = 1; void load(); }
async function changeStatus(item: GuestbookItem, next: GuestbookStatus) {
  try {
    await updateGuestbookStatus(item.id, next);
    ElMessage.success(`留言已${statusLabels[next]}`);
    await load();
  } catch (error) { ElMessage.error(resolveErrorMessage(error, "留言状态更新失败")); }
}
async function remove(item: GuestbookItem) {
  try { await ElMessageBox.confirm(`确定删除“${excerpt(item.content)}”吗？`, "删除留言", { type: "warning", confirmButtonText: "删除", cancelButtonText: "取消" }); }
  catch { return; }
  await changeStatus(item, "deleted");
}
function openReply(item: GuestbookItem) { replyTarget.value = item; reply.value = item.admin_reply; replyVisible.value = true; }
async function saveReply() {
  if (!replyTarget.value) return;
  savingReply.value = true;
  try { await updateGuestbookReply(replyTarget.value.id, reply.value); ElMessage.success("回复已保存"); replyVisible.value = false; await load(); }
  catch (error) { ElMessage.error(resolveErrorMessage(error, "回复保存失败")); }
  finally { savingReply.value = false; }
}
onMounted(load);
</script>

<template>
  <div class="page-stack content-admin-page">
    <PageHeader eyebrow="MESSAGE BOARD" title="留言板" description="审核访客留言，只有通过审核的内容会显示在前台。" />
    <div class="content-admin-toolbar guestbook-admin-toolbar">
      <div class="guestbook-admin-filters"><el-input v-model="keyword" clearable placeholder="搜索昵称或内容" @keyup.enter="search"><template #prefix><el-icon><Search /></el-icon></template></el-input><el-select v-model="status" aria-label="留言状态" @change="search"><el-option label="待审核" value="pending" /><el-option label="已通过" value="approved" /><el-option label="已拒绝" value="rejected" /><el-option label="垃圾留言" value="spam" /><el-option label="全部状态" value="" /></el-select><el-button :icon="Search" @click="search">查询</el-button></div>
      <el-button :icon="Refresh" :loading="loading" @click="load">刷新（待审 {{ data?.pending_count ?? 0 }}）</el-button>
    </div>
    <el-card shadow="never" class="content-table-card">
      <el-table v-loading="loading" :data="items" row-key="id" empty-text="暂无留言">
        <el-table-column label="留言" min-width="360"><template #default="{ row }"><div class="guestbook-admin-content"><strong>{{ row.nickname }}</strong><span>{{ row.content }}</span></div></template></el-table-column>
        <el-table-column label="状态" width="110"><template #default="{ row }"><el-tag :type="statusType(row.status)" effect="light">{{ statusLabel(row.status) }}</el-tag></template></el-table-column>
        <el-table-column label="提交时间" width="180"><template #default="{ row }">{{ formatDate(row.created_at) }}</template></el-table-column>
        <el-table-column label="操作" fixed="right" width="250"><template #default="{ row }"><el-button v-if="row.status === 'pending' || row.status === 'rejected' || row.status === 'spam'" link type="success" @click="changeStatus(row, 'approved')">通过</el-button><el-button v-if="row.status === 'pending'" link type="warning" @click="changeStatus(row, 'rejected')">拒绝</el-button><el-button v-if="row.status === 'pending'" link type="danger" @click="changeStatus(row, 'spam')">标垃圾</el-button><el-button v-if="row.status === 'approved'" link type="primary" :icon="Edit" @click="openReply(row)">回复</el-button><el-button v-if="row.status !== 'deleted'" link type="danger" :icon="Delete" @click="remove(row)">删除</el-button></template></el-table-column>
      </el-table>
      <el-pagination v-if="(data?.total ?? 0) > 20" v-model:current-page="page" layout="prev, pager, next" :page-size="20" :total="data?.total ?? 0" @current-change="load" />
    </el-card>
    <el-dialog v-model="replyVisible" title="回复留言" width="min(560px, calc(100vw - 32px))"><p class="guestbook-reply-source">{{ replyTarget?.content }}</p><el-input v-model="reply" type="textarea" :rows="5" maxlength="2000" show-word-limit placeholder="写给访客的回复" /><template #footer><el-button @click="replyVisible = false">取消</el-button><el-button type="primary" :loading="savingReply" @click="saveReply">保存回复</el-button></template></el-dialog>
  </div>
</template>

<style scoped>
.guestbook-admin-toolbar { align-items: center; }
.guestbook-admin-filters { display: flex; flex-wrap: wrap; gap: .75rem; }
.guestbook-admin-filters .el-input { width: 240px; }
.guestbook-admin-filters .el-select { width: 140px; }
.guestbook-admin-content { display: grid; gap: .35rem; }
.guestbook-admin-content span { color: var(--admin-muted, #62737b); white-space: pre-wrap; overflow: hidden; text-overflow: ellipsis; }
.guestbook-reply-source { padding: .8rem; margin: 0 0 1rem; white-space: pre-wrap; color: #536b72; background: #f3f0e7; }
@media (max-width: 700px) { .guestbook-admin-filters { width: 100%; } .guestbook-admin-filters .el-input, .guestbook-admin-filters .el-select { width: 100%; } }
</style>
