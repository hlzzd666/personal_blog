import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { ADMIN_CREDENTIALS, AUTH_STORAGE_KEY } from "../constants/auth";
function readSession() {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) {
        return null;
    }
    try {
        return JSON.parse(raw);
    }
    catch {
        localStorage.removeItem(AUTH_STORAGE_KEY);
        return null;
    }
}
export function hasAuthSession() {
    return Boolean(readSession());
}
export const useAuthStore = defineStore("auth", () => {
    const session = ref(readSession());
    const isAuthenticated = computed(() => Boolean(session.value));
    const username = computed(() => session.value?.username ?? "");
    function login(payload) {
        if (payload.username !== ADMIN_CREDENTIALS.username ||
            payload.password !== ADMIN_CREDENTIALS.password) {
            throw new Error("账号或密码错误");
        }
        session.value = {
            username: payload.username,
            loggedInAt: new Date().toISOString(),
        };
        localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session.value));
    }
    function logout() {
        session.value = null;
        localStorage.removeItem(AUTH_STORAGE_KEY);
    }
    return {
        session,
        username,
        isAuthenticated,
        login,
        logout,
    };
});
