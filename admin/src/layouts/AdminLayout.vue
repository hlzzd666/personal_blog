<script setup lang="ts">
import { RouterView } from "vue-router";

import AppHeader from "../components/AppHeader.vue";
import AppSidebar from "../components/AppSidebar.vue";
</script>

<template>
  <main class="admin-shell">
    <AppSidebar />
    <section class="workspace-shell">
      <AppHeader />
      <div class="workspace-body">
        <RouterView />
      </div>
    </section>
  </main>
</template>
