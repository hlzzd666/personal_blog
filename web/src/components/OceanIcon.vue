<script setup lang="ts">
import { computed } from "vue";

import { iconCatalog, iconUrl, type IconName } from "../icons";

const props = withDefaults(
  defineProps<{
    name: IconName;
    size?: number;
    decorative?: boolean;
    label?: string;
  }>(),
  { size: 24, decorative: true, label: "" },
);

const metadata = computed(() => iconCatalog.find((icon) => icon.name === props.name));
const alternativeText = computed(() =>
  props.decorative ? "" : props.label || metadata.value?.label || props.name,
);
</script>

<template>
  <img
    class="ocean-icon"
    :src="iconUrl(name)"
    :alt="alternativeText"
    :aria-hidden="decorative ? 'true' : undefined"
    :width="size"
    :height="size"
    :style="{ width: `${size}px`, height: `${size}px` }"
  />
</template>

<style scoped>
.ocean-icon {
  display: block;
  flex: 0 0 auto;
  aspect-ratio: 1;
  object-fit: contain;
  filter: drop-shadow(0 0.12rem 0.18rem rgba(4, 19, 29, 0.2));
  transition: filter 180ms ease, transform 240ms cubic-bezier(0.2, 0.76, 0.26, 1);
}

@media (prefers-color-scheme: dark) {
  .ocean-icon {
    filter: drop-shadow(0 0.16rem 0.24rem rgba(0, 0, 0, 0.42)) saturate(1.06);
  }
}

@media (prefers-reduced-motion: reduce) {
  .ocean-icon {
    transition: none;
  }
}
</style>
