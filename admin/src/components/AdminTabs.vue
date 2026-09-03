<script setup lang="ts">
import { Close } from "@element-plus/icons-vue";
import { computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAdminTabsStore } from "../stores/admin-tabs";

const route = useRoute();
const router = useRouter();
const tabsStore = useAdminTabsStore();

const activeKey = computed(() => route.fullPath);

function ensureCurrentTab() {
  const title = typeof route.meta.title === "string" ? route.meta.title : "后台页面";
  tabsStore.ensureTab({ key: route.fullPath, path: route.fullPath, title });
}

function selectTab(path: string) {
  if (path !== route.fullPath) {
    void router.push(path);
  }
}

function closeTab(tabKey: string) {
  const index = tabsStore.tabs.findIndex((tab) => tab.key === tabKey);
  const isActive = tabKey === route.fullPath;
  tabsStore.removeTab(tabKey);

  if (!isActive) {
    return;
  }

  const nextTab = tabsStore.tabs[index] ?? tabsStore.tabs[index - 1] ?? tabsStore.tabs[0];
  if (nextTab && nextTab.key !== route.fullPath) {
    void router.push(nextTab.path);
  }
}

function closeOtherTabs() {
  tabsStore.removeOtherTabs(route.fullPath);
}

watch(() => route.fullPath, ensureCurrentTab, { immediate: true });
</script>

<template>
  <nav class="admin-tabs" aria-label="已打开页面">
    <div class="admin-tabs-scroll">
      <button
        v-for="tab in tabsStore.tabs"
        :key="tab.key"
        class="admin-tab"
        :class="{ 'is-active': activeKey === tab.key }"
        type="button"
        :aria-current="activeKey === tab.key ? 'page' : undefined"
        @click="selectTab(tab.path)"
      >
        <span>{{ tab.title }}</span>
        <el-icon
          v-if="tab.closable"
          class="admin-tab-close"
          title="关闭标签"
          aria-label="关闭标签"
          @click.stop="closeTab(tab.key)"
        >
          <Close />
        </el-icon>
      </button>
    </div>
    <el-button
      v-if="tabsStore.tabs.some((tab) => tab.closable)"
      class="admin-tabs-clear"
      link
      type="info"
      @click="closeOtherTabs"
    >
      关闭其他
    </el-button>
  </nav>
</template>
