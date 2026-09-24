<script setup lang="ts">
withDefaults(defineProps<{ heading?: number }>(), { heading: 0 });
</script>
<template>
  <svg class="museum-compass" viewBox="0 0 180 180" aria-hidden="true">
    <circle cx="90" cy="90" r="68" fill="#08141ce6" stroke="currentColor" stroke-width=".7" />
    <circle cx="90" cy="90" r="61" fill="none" stroke="currentColor" stroke-width=".35" />
    <circle cx="90" cy="90" r="45" fill="none" stroke="currentColor" stroke-dasharray="1 4" stroke-width=".7" />
    <g v-for="index in 36" :key="index" :transform="`rotate(${index * 10} 90 90)`">
      <path :d="index % 3 === 0 ? 'M90 24V33' : 'M90 24V28'" stroke="currentColor" stroke-width=".6" />
    </g>
    <g :transform="`rotate(${heading} 90 90)`">
      <g v-for="index in 8" :key="index" :transform="`rotate(${index * 45} 90 90)`">
        <path d="M90 90L84 83L90 42Z" fill="currentColor" :opacity="index % 2 ? .45 : .9" />
        <path d="M90 90L96 83L90 42Z" fill="none" stroke="currentColor" stroke-width=".5" />
      </g>
    </g>
    <circle cx="90" cy="90" r="6" fill="#09141a" stroke="currentColor" />
    <g fill="currentColor" text-anchor="middle" font-family="Georgia,serif" font-size="13">
      <text x="90" y="14">N</text><text x="90" y="176">S</text><text x="10" y="95">W</text><text x="170" y="95">E</text>
    </g>
  </svg>
</template>
<style scoped>
.museum-compass { display: block; width: 100%; color: #bb9b5d; }
</style>
