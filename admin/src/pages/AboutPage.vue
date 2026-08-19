<script setup lang="ts">
import PageHeader from "../components/PageHeader.vue";
</script>

<template>
  <div class="page-stack">
    <PageHeader
      eyebrow="ABOUT"
      title="关于自己"
      description="这个模块后续用来管理简介、头像、经历、技能标签和联系方式。"
    />
    <el-card shadow="never" class="empty-module-card">
      <el-empty description="建议继续拆成基础信息、时间线、社交链接和公开展示设置四部分。">
        <el-button type="primary" disabled>等待下一步细化</el-button>
      </el-empty>
    </el-card>
  </div>
</template>
