<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import SiteFooter from "./components/SiteFooter.vue";
import SiteNavigation from "./components/SiteNavigation.vue";

const route = useRoute();
const isStandalone = computed(() => route.path === "/gallery" || route.path === "/dashboard");
</script>

<template>
  <SiteNavigation v-if="!isStandalone" />
  <router-view v-slot="{ Component }">
    <KeepAlive include="ArticlesPage,NotesPage">
      <component :is="Component" />
    </KeepAlive>
  </router-view>
  <SiteFooter v-if="!isStandalone" />
</template>
