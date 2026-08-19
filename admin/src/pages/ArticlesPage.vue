<script setup lang="ts">
import PageHeader from "../components/PageHeader.vue";
</script>

<template>
  <div class="page-stack">
    <PageHeader
      eyebrow="ARTICLES"
      title="文章管理"
      description="这个模块后续承接文章列表、分类标签、发布流程、草稿箱和编辑器。"
    />
    <el-card shadow="never" class="empty-module-card">
      <el-empty description="文章模块已预留，下一步可以继续接入文章列表和编辑器。">
        <el-button type="primary" disabled>稍后继续开发</el-button>
      </el-empty>
    </el-card>
  </div>
</template>
