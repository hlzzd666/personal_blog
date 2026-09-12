<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import SiteFooter from "./components/SiteFooter.vue";
import SiteNavigation from "./components/SiteNavigation.vue";

const route = useRoute();
const router = useRouter();
const appReady = ref(false);
const isStandalone = computed(() => route.path === "/gallery" || route.path === "/dashboard");

void router.isReady().finally(() => {
  appReady.value = true;
});
</script>

<template>
  <div v-if="!appReady" class="app-boot" role="status" aria-live="polite">
    <div class="app-boot-mark" aria-hidden="true"></div>
    <p>正在展开航海日志</p>
  </div>
  <router-view v-else v-slot="{ Component }">
    <div v-if="Component" class="app-shell">
      <SiteNavigation v-if="!isStandalone" />
      <div class="app-content">
        <KeepAlive include="ArticlesPage,NotesPage">
          <component :is="Component" />
        </KeepAlive>
      </div>
      <SiteFooter v-if="!isStandalone" />
    </div>
    <div v-else class="app-boot" role="status" aria-live="polite">
      <div class="app-boot-mark" aria-hidden="true"></div>
      <p>正在展开航海日志</p>
    </div>
  </router-view>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #07131f;
}

.app-content {
  flex: 1 0 auto;
  min-width: 0;
}

.app-boot {
  display: grid;
  min-height: 100vh;
  place-content: center;
  gap: 1rem;
  color: #f6ebd4;
  background:
    radial-gradient(circle at 50% 42%, rgba(240, 193, 98, 0.14), transparent 22rem),
    linear-gradient(152deg, #07131f 0%, #071c29 48%, #07131f 100%);
  font-family: "Noto Sans SC", sans-serif;
  text-align: center;
}

.app-boot p {
  margin: 0;
  color: rgba(246, 235, 212, 0.78);
  font-size: 0.82rem;
  font-weight: 700;
}

.app-boot-mark {
  width: 3rem;
  height: 3rem;
  margin: 0 auto;
  border: 1px solid rgba(240, 193, 98, 0.48);
  border-radius: 50%;
  background:
    linear-gradient(90deg, transparent 48%, rgba(135, 210, 199, 0.9) 49% 51%, transparent 52%),
    linear-gradient(0deg, transparent 48%, rgba(135, 210, 199, 0.9) 49% 51%, transparent 52%);
  box-shadow: 0 1rem 2.4rem rgba(7, 19, 31, 0.42);
  animation: app-boot-spin 1.2s linear infinite;
}

@keyframes app-boot-spin {
  to {
    transform: rotate(1turn);
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-boot-mark {
    animation: none;
  }
}
</style>
