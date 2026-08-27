import { createRouter, createWebHistory } from "vue-router";

import AdminLayout from "../layouts/AdminLayout.vue";
import AboutPage from "../pages/AboutPage.vue";
import ArticlesPage from "../pages/ArticlesPage.vue";
import DashboardPage from "../pages/DashboardPage.vue";
import LoginPage from "../pages/LoginPage.vue";
import MediaPage from "../pages/MediaPage.vue";
import SiteSettingsPage from "../pages/SiteSettingsPage.vue";
import { hasAuthSession, useAuthStore } from "../stores/auth";

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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
        { path: "series", name: "series", component: () => import("../pages/SeriesPage.vue") },
        { path: "notes", name: "notes", component: () => import("../pages/NotesPage.vue") },
        {
          path: "daily-learning",
          name: "daily-learning",
          component: () => import("../pages/DailyLearningPage.vue"),
        },
        { path: "media", name: "media", component: MediaPage },
        { path: "about", name: "about", component: AboutPage },
        { path: "site-settings", name: "site-settings", component: SiteSettingsPage },
      ],
    },
  ],
});

router.beforeEach(async (to) => {
  const authed = await hasAuthSession();

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

window.addEventListener("personal-blog-admin-unauthorized", () => {
  const authStore = useAuthStore();
  const redirect = router.currentRoute.value.fullPath;
  authStore.clearSession();
  if (router.currentRoute.value.path === "/login") {
    return;
  }
  void router.push({ path: "/login", query: { redirect } });
});
