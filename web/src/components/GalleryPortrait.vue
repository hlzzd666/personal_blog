<script setup lang="ts">
import { ref, watch } from "vue";
import type { GalleryCharacter } from "../api/gallery";
import { portraitStyle } from "../gallery/curation";

const props = defineProps<{ character: GalleryCharacter; recordNumber: number }>();
const failed = ref(false);
watch(() => props.character.poster_url, () => { failed.value = false; });
function imageUrl(url: string) {
  try {
    const source = new URL(url, window.location.href);
    return source.pathname.startsWith('/uploads/') ? `${source.pathname}${source.search}` : url;
  } catch { return url; }
}
</script>

<template>
  <div class="portrait-art">
    <div v-if="portraitStyle(character.name)" class="portrait-painting" :style="portraitStyle(character.name)" role="img" :aria-label="`${character.name}馆藏插画`"></div>
    <div v-else class="portrait-typeset">
      <small>GRAND LINE ARCHIVE</small><span>{{ String(recordNumber).padStart(2, '0') }}</span><strong>{{ character.name }}</strong><small>{{ character.epithet }}</small>
    </div>
    <img v-if="character.poster_url && !failed" :key="character.poster_url" :src="imageUrl(character.poster_url)" :alt="`${character.name}海报`" loading="lazy" decoding="async" @error="failed = true" />
  </div>
</template>

<style scoped>
.portrait-art { position: relative; width: 100%; height: 100%; min-height: 0; aspect-ratio: 2/3; background: #241c13; }
.portrait-painting,.portrait-art img,.portrait-typeset { position: absolute; inset: 0; width: 100%; height: 100%; }
.portrait-painting { background-repeat: no-repeat; }
.portrait-art img { object-fit: contain; background: #241c13; }
.portrait-typeset { display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 22px; padding: 18px; color: #e8d7b1; text-align: center; border: 10px double #8d7042; }
.portrait-typeset span { font: 64px Georgia,serif; color: #b69657; }
.portrait-typeset strong { font: 24px/1.5 var(--serif); overflow-wrap: anywhere; }
.portrait-typeset small { font-size: 10px; letter-spacing: .08em; }
</style>
