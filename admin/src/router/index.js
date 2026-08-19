import { createRouter, createWebHistory } from "vue-router";
import AdminLayout from "../layouts/AdminLayout.vue";
import AboutPage from "../pages/AboutPage.vue";
import ArticlesPage from "../pages/ArticlesPage.vue";
import DashboardPage from "../pages/DashboardPage.vue";
import LoginPage from "../pages/LoginPage.vue";
import MediaPage from "../pages/MediaPage.vue";
import SiteSettingsPage from "../pages/SiteSettingsPage.vue";
import { hasAuthSession } from "../stores/auth";
export const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: "/login",
            name: "login",
            component: LoginPage,
            meta: { guestOnly: true },
        },
        {
            path: "/",
            component: AdminLayout,
            meta: { requiresAuth: true },
            children: [
                { path: "", name: "dashboard", component: DashboardPage },
                { path: "articles", name: "articles", component: ArticlesPage },
                { path: "media", name: "media", component: MediaPage },
                { path: "about", name: "about", component: AboutPage },
                { path: "site-settings", name: "site-settings", component: SiteSettingsPage },
            ],
        },
    ],
});
router.beforeEach((to) => {
    const authed = hasAuthSession();
    if (to.meta.requiresAuth && !authed) {
        return {
            path: "/login",
            query: { redirect: to.fullPath },
        };
    }
    if (to.meta.guestOnly && authed) {
        return "/";
    }
    return true;
});
