<script setup lang="ts">
import { computed } from "vue";

type AtmosphereVariant = "detail" | "series" | "notes";

const props = withDefaults(defineProps<{ variant?: AtmosphereVariant }>(), {
  variant: "detail",
});

const assetByVariant: Record<AtmosphereVariant, string> = {
  detail: "/atmosphere/deep-current.svg",
  series: "/atmosphere/clouded-route.svg",
  notes: "/atmosphere/sunset-wake.svg",
};

const assetUrl = computed(() => assetByVariant[props.variant]);
</script>

<template>
  <div class="ocean-atmosphere" :class="`ocean-atmosphere--${variant}`" aria-hidden="true">
    <img class="ocean-atmosphere-image" :src="assetUrl" alt="" fetchpriority="low" />
    <span class="ocean-atmosphere-wash ocean-atmosphere-wash-one"></span>
    <span class="ocean-atmosphere-wash ocean-atmosphere-wash-two"></span>
    <span class="ocean-atmosphere-current ocean-atmosphere-current-one"></span>
    <span class="ocean-atmosphere-current ocean-atmosphere-current-two"></span>
    <span class="ocean-atmosphere-beacon ocean-atmosphere-beacon-one"></span>
    <span class="ocean-atmosphere-beacon ocean-atmosphere-beacon-two"></span>
  </div>
</template>

<style scoped>
.ocean-atmosphere {
  position: fixed;
  z-index: 0;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  background: #061b25;
  isolation: isolate;
}

.ocean-atmosphere-image,
.ocean-atmosphere-wash,
.ocean-atmosphere-current,
.ocean-atmosphere-beacon {
  position: absolute;
  pointer-events: none;
}

.ocean-atmosphere-image {
  inset: -4%;
  z-index: -4;
  width: 108%;
  height: 108%;
  object-fit: cover;
  opacity: 0.58;
  filter: saturate(0.92) contrast(1.02);
  transform: scale(1.04);
  animation: atmosphere-image-drift 28s ease-in-out infinite alternate;
}

.ocean-atmosphere::before,
.ocean-atmosphere::after {
  content: "";
  position: absolute;
  z-index: -3;
  inset: 0;
  pointer-events: none;
}

.ocean-atmosphere::before {
  background: linear-gradient(115deg, rgba(4, 20, 29, 0.55), transparent 42%, rgba(4, 18, 26, 0.58));
}

.ocean-atmosphere::after {
  background: linear-gradient(180deg, rgba(3, 17, 25, 0.12), rgba(3, 17, 25, 0.36) 55%, rgba(3, 17, 25, 0.78));
}

.ocean-atmosphere-wash {
  z-index: -2;
  width: 45rem;
  height: 24rem;
  border-radius: 50%;
  opacity: 0.22;
  filter: blur(36px);
  mix-blend-mode: screen;
}

.ocean-atmosphere-wash-one {
  top: 10%;
  right: -12rem;
  background: #e8b85e;
  transform: rotate(-12deg);
  animation: atmosphere-wash-one 18s ease-in-out infinite alternate;
}

.ocean-atmosphere-wash-two {
  bottom: 2%;
  left: -16rem;
  background: #4cbab2;
  transform: rotate(18deg);
  animation: atmosphere-wash-two 23s ease-in-out infinite alternate;
}

.ocean-atmosphere-current {
  z-index: -1;
  width: 120%;
  height: 5rem;
  left: -10%;
  border-top: 1px solid rgba(239, 205, 112, 0.24);
  border-bottom: 1px solid rgba(117, 201, 189, 0.12);
  opacity: 0.64;
  transform: rotate(-7deg);
}

.ocean-atmosphere-current-one {
  top: 33%;
  animation: atmosphere-current-one 17s ease-in-out infinite alternate;
}

.ocean-atmosphere-current-two {
  top: 76%;
  opacity: 0.4;
  transform: rotate(5deg);
  animation: atmosphere-current-two 21s ease-in-out infinite alternate;
}

.ocean-atmosphere-beacon {
  z-index: -1;
  width: 0.35rem;
  height: 0.35rem;
  border: 1px solid rgba(244, 202, 88, 0.8);
  border-radius: 50%;
  background: rgba(244, 202, 88, 0.3);
  box-shadow: 0 0 0 0.25rem rgba(244, 202, 88, 0.08), 0 0 1rem rgba(244, 202, 88, 0.35);
  animation: atmosphere-beacon 4.8s ease-out infinite;
}

.ocean-atmosphere-beacon-one { top: 26%; left: 18%; }
.ocean-atmosphere-beacon-two { right: 22%; bottom: 20%; animation-delay: -2.3s; }

.ocean-atmosphere--series .ocean-atmosphere-wash-one { background: #e4a16f; }
.ocean-atmosphere--notes .ocean-atmosphere-wash-two { background: #e37c5e; }

@keyframes atmosphere-image-drift {
  from { transform: scale(1.04) translate3d(-0.7%, -0.5%, 0); }
  to { transform: scale(1.08) translate3d(0.7%, 0.5%, 0); }
}

@keyframes atmosphere-wash-one {
  from { transform: translate3d(0, -1rem, 0) rotate(-12deg) scale(0.96); opacity: 0.16; }
  to { transform: translate3d(-4rem, 2rem, 0) rotate(-4deg) scale(1.08); opacity: 0.27; }
}

@keyframes atmosphere-wash-two {
  from { transform: translate3d(-1rem, 1rem, 0) rotate(18deg) scale(0.94); opacity: 0.14; }
  to { transform: translate3d(3rem, -2rem, 0) rotate(9deg) scale(1.08); opacity: 0.24; }
}

@keyframes atmosphere-current-one {
  from { transform: translateX(-3%) rotate(-7deg); }
  to { transform: translateX(3%) rotate(-4deg); }
}

@keyframes atmosphere-current-two {
  from { transform: translateX(4%) rotate(5deg); }
  to { transform: translateX(-3%) rotate(8deg); }
}

@keyframes atmosphere-beacon {
  0%, 100% { opacity: 0.35; transform: scale(0.7); }
  48% { opacity: 0.9; transform: scale(1.15); box-shadow: 0 0 0 0.9rem rgba(244, 202, 88, 0), 0 0 1.4rem rgba(244, 202, 88, 0.55); }
}

@media (max-width: 700px) {
  .ocean-atmosphere-image { opacity: 0.48; }
  .ocean-atmosphere-wash { width: 28rem; height: 16rem; filter: blur(28px); }
  .ocean-atmosphere-current-two { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  .ocean-atmosphere-image,
  .ocean-atmosphere-wash,
  .ocean-atmosphere-current,
  .ocean-atmosphere-beacon {
    animation: none;
  }
}
</style>
