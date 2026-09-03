<script setup lang="ts">
import { RouterView } from "vue-router";

import AppHeader from "../components/AppHeader.vue";
import AppSidebar from "../components/AppSidebar.vue";
import AdminTabs from "../components/AdminTabs.vue";
</script>

<template>
  <main class="admin-shell">
    <AppSidebar />
    <section class="workspace-shell">
      <AppHeader />
      <AdminTabs />
      <div class="workspace-body">
        <RouterView v-slot="{ Component, route }">
          <KeepAlive>
            <component :is="Component" :key="route.fullPath" />
          </KeepAlive>
        </RouterView>
      </div>
    </section>
  </main>
</template>
