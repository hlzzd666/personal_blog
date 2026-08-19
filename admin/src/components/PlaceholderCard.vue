<script setup lang="ts">
defineProps<{
  title: string;
  description: string;
}>();
</script>

<template>
  <section class="placeholder-card">
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
  </section>
</template>
