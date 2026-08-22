import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { fetchCurrentAdmin, loginAdmin, logoutAdmin } from "../api/auth";
export const useAuthStore = defineStore("auth", () => {
    const session = ref(null);
    const initialized = ref(false);
    const isAuthenticated = computed(() => Boolean(session.value));
    const username = computed(() => session.value?.username ?? "");
    function setSession(payload) {
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
        }
        catch {
            clearSession();
            return false;
        }
    }
    async function login(payload) {
        setSession(await loginAdmin(payload));
    }
    async function logout() {
        try {
            await logoutAdmin();
        }
        finally {
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
