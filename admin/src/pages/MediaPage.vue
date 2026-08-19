<script setup lang="ts">
import PageHeader from "../components/PageHeader.vue";
</script>

<template>
  <div class="page-stack">
    <PageHeader
      eyebrow="MEDIA"
      title="媒体资源"
      description="这个模块后续用来管理首页大图、文章封面、正文插图和静态资源。"
    />
    <el-card shadow="never" class="empty-module-card">
      <el-empty description="建议优先补图片上传、本地资源列表和资源引用关系。">
        <el-button type="primary" disabled>等待接入上传功能</el-button>
      </el-empty>
    </el-card>
  </div>
</template>
