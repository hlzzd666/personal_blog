<script setup lang="ts">
import {
  DataBoard,
  Document,
  Picture,
  Setting,
  User,
} from "@element-plus/icons-vue";
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { adminNavigation, adminNavigationGroups } from "../constants/navigation";

const route = useRoute();
const router = useRouter();

const iconMap = {
  DataBoard,
  Document,
  Picture,
  Setting,
  User,
};

const activePath = computed(() => (route.path === "/" ? "/" : route.path));

function handleSelect(index: string) {
  void router.push(index);
}
</script>

<template>
  <aside class="app-sidebar">
    <div class="sidebar-brand">
      <span class="sidebar-logo" aria-hidden="true">B</span>
      <div>
        <p class="sidebar-mark">CAPTAIN'S DESK</p>
        <h1>博客后台</h1>
      </div>
    </div>

    <nav class="sidebar-nav" aria-label="后台目录">
      <section v-for="group in adminNavigationGroups" :key="group.key" class="sidebar-group">
        <p class="sidebar-group-label">{{ group.label }}</p>
        <el-menu
          :default-active="activePath"
          class="sidebar-menu"
          background-color="transparent"
          text-color="#9aabba"
          active-text-color="#f5c66f"
          @select="handleSelect"
        >
          <el-menu-item
            v-for="item in adminNavigation.filter((entry) => entry.group === group.key)"
            :key="item.to"
            :index="item.to"
          >
            <el-icon>
              <component :is="iconMap[item.icon]" />
            </el-icon>
            <span>{{ item.label }}</span>
          </el-menu-item>
        </el-menu>
      </section>
    </nav>

    <p class="sidebar-footer">内容管理工作台</p>
  </aside>
</template>
