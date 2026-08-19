<script setup lang="ts">
defineProps<{
  eyebrow: string;
  title: string;
  description: string;
}>();
</script>

<template>
  <header class="page-header">
    <div>
      <p class="page-kicker">{{ eyebrow }}</p>
      <h2>{{ title }}</h2>
    </div>
    <p class="page-description">{{ description }}</p>
  </header>
</template>
