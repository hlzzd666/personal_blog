<script setup lang="ts">
defineProps<{ src?: string | null; alt: string }>();
</script>

<template>
  <span class="image-preview" :title="src || '未设置图片'">
    <el-image :key="src" :src="src || ''" :alt="alt" fit="cover">
      <template #error>
        <span class="image-preview-error" role="status">{{ src ? '图片加载失败' : '未设置图片' }}</span>
      </template>
    </el-image>
  </span>
</template>

<style scoped>
.image-preview { display: block; width: 100%; height: 100%; overflow: hidden; }
.image-preview :deep(.el-image) { display: block; width: 100%; height: 100%; }
.image-preview-error { display: grid; place-items: center; width: 100%; height: 100%; padding: 8px; box-sizing: border-box; background: #edf2f6; color: #526375; font-size: 12px; line-height: 1.5; text-align: center; }
</style>
