<script setup lang="ts">
import { ArrowRight, SwitchButton } from "@element-plus/icons-vue";
import { ElMessageBox } from "element-plus";
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { adminNavigation } from "../constants/navigation";
import { useAuthStore } from "../stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const activeLabel = computed(() => {
  const current = adminNavigation.find((item) => item.to === route.path);
  return current?.label ?? "控制台";
});

async function handleLogout() {
  await ElMessageBox.confirm("确认退出当前后台登录状态吗？", "退出登录", {
    type: "warning",
    confirmButtonText: "退出",
    cancelButtonText: "取消",
  });

  await authStore.logout();
  await router.push("/login");
}
</script>

<template>
  <header class="app-header">
    <div>
      <el-breadcrumb :separator-icon="ArrowRight">
        <el-breadcrumb-item>工作台</el-breadcrumb-item>
        <el-breadcrumb-item>{{ activeLabel }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <div class="app-header-actions">
      <span class="header-status"><i></i>系统正常</span>
      <el-dropdown trigger="click">
        <span class="header-user">
          {{ authStore.username }}
          <el-icon><SwitchButton /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>
