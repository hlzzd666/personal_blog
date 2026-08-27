<script setup lang="ts">
import { Lock, User } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { resolveErrorMessage } from "../api/http";
import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();

const loading = ref(false);
const form = reactive({
  username: "admin",
  password: "",
});

async function handleLogin() {
  loading.value = true;

  try {
    await authStore.login(form);
    ElMessage.success("登录成功，欢迎进入后台。");
    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/";
    await router.push(redirect);
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, "登录失败，请稍后重试"));
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="login-shell">
    <div class="login-panel-wrap">
      <el-card shadow="never" class="login-panel">
        <h2>进入后台</h2>

        <el-form label-position="top" class="login-form" @submit.prevent="handleLogin">
          <el-form-item label="账号">
            <el-input v-model="form.username" placeholder="请输入账号">
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="密码">
            <el-input v-model="form.password" type="password" show-password placeholder="请输入密码">
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-button
            class="login-submit"
            type="primary"
            :loading="loading"
            size="large"
            @click="handleLogin"
          >
            登录后台
          </el-button>
        </el-form>
      </el-card>
    </div>
  </section>
</template>
