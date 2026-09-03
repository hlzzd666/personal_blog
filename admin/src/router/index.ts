import { createRouter, createWebHistory } from "vue-router";

import AdminLayout from "../layouts/AdminLayout.vue";
import AboutPage from "../pages/AboutPage.vue";
import ArticlesPage from "../pages/ArticlesPage.vue";
import DashboardPage from "../pages/DashboardPage.vue";
import LoginPage from "../pages/LoginPage.vue";
import MediaPage from "../pages/MediaPage.vue";
import SiteSettingsPage from "../pages/SiteSettingsPage.vue";
import { useAdminTabsStore } from "../stores/admin-tabs";
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
        { path: "", name: "dashboard", component: DashboardPage, meta: { title: "控制台", cache: true } },
        { path: "articles", name: "articles", component: ArticlesPage, meta: { title: "文章管理", cache: true } },
        {
          path: "article-taxonomy",
          name: "article-taxonomy",
          component: () => import("../pages/ArticleTaxonomyPage.vue"),
          meta: { title: "分类与标签", cache: true },
        },
        { path: "series", name: "series", component: () => import("../pages/SeriesPage.vue"), meta: { title: "专题管理", cache: true } },
        { path: "notes", name: "notes", component: () => import("../pages/NotesPage.vue"), meta: { title: "短动态", cache: true } },
        { path: "gallery", name: "gallery", component: () => import("../pages/GalleryPage.vue"), meta: { title: "3D 展厅", cache: true } },
        {
          path: "daily-learning",
          name: "daily-learning",
          component: () => import("../pages/DailyLearningPage.vue"),
          meta: { title: "每日问答", cache: true },
        },
        { path: "media", name: "media", component: MediaPage, meta: { title: "媒体资源", cache: true } },
        { path: "about", name: "about", component: AboutPage, meta: { title: "关于我", cache: true } },
        { path: "site-settings", name: "site-settings", component: SiteSettingsPage, meta: { title: "站点设置", cache: true } },
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
  const tabsStore = useAdminTabsStore();
  const redirect = router.currentRoute.value.fullPath;
  authStore.clearSession();
  tabsStore.reset();
  if (router.currentRoute.value.path === "/login") {
    return;
  }
  void router.push({ path: "/login", query: { redirect } });
});
