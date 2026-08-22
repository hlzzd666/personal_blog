import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { fetchCurrentAdmin, loginAdmin, logoutAdmin, type AdminLoginPayload } from "../api/auth";

type AuthSession = {
  username: string;
  loggedInAt: string;
  expiresAt: string;
};

export const useAuthStore = defineStore("auth", () => {
  const session = ref<AuthSession | null>(null);
  const initialized = ref(false);

  const isAuthenticated = computed(() => Boolean(session.value));
  const username = computed(() => session.value?.username ?? "");

  function setSession(payload: { username: string; logged_in_at: string; expires_at: string }) {
    session.value = {
      username: payload.username,
      loggedInAt: payload.logged_in_at,
      expiresAt: payload.expires_at,
    };
    initialized.value = true;
  }

  function clearSession() {
    session.value = null;
    initialized.value = true;
  }

  async function refreshSession() {
    try {
      setSession(await fetchCurrentAdmin());
      return true;
    } catch {
      clearSession();
      return false;
    }
  }

  async function login(payload: AdminLoginPayload) {
    setSession(await loginAdmin(payload));
  }

  async function logout() {
    try {
      await logoutAdmin();
    } finally {
      clearSession();
    }
  }

  return {
    session,
    initialized,
    username,
    isAuthenticated,
    clearSession,
    refreshSession,
    login,
    logout,
  };
});

export async function hasAuthSession() {
  const authStore = useAuthStore();
  if (authStore.isAuthenticated) {
    return true;
  }
  return authStore.refreshSession();
}
