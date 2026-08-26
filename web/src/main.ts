import { createApp } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import "./styles.css";
import "./content-pages.css";

const HomeRoute = { name: "HomeRoute", render: () => null };

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, from) {
    if (to.hash) {
      return { el: to.hash, behavior: "smooth" };
    }
    if (to.path === "/articles" && from.path.startsWith("/articles/")) {
      return false;
    }
    return { top: 0 };
  },
  routes: [
    { path: "/", component: HomeRoute, meta: { title: "首页" } },
    { path: "/about", component: () => import("./pages/AboutPage.vue"), meta: { title: "关于我" } },
    { path: "/articles", component: () => import("./pages/ArticlesPage.vue"), meta: { title: "文章" } },
    { path: "/articles/:slug", component: () => import("./pages/ArticleDetailPage.vue"), meta: { title: "文章详情" } },
    { path: "/series", component: () => import("./pages/SeriesPage.vue"), meta: { title: "专题" } },
    { path: "/series/:slug", component: () => import("./pages/SeriesDetailPage.vue"), meta: { title: "专题详情" } },
    { path: "/notes", component: () => import("./pages/NotesPage.vue"), meta: { title: "短动态" } },
    { path: "/notes/:slug", component: () => import("./pages/NoteDetailPage.vue"), meta: { title: "动态详情" } },
    { path: "/privacy", component: () => import("./pages/PrivacyPage.vue"), meta: { title: "隐私说明" } },
    { path: "/:pathMatch(.*)*", component: () => import("./pages/NotFoundPage.vue"), meta: { title: "页面不存在" } },
  ],
});

router.afterEach((to) => {
  document.title = `${String(to.meta.title ?? "个人空间")} | 个人博客`;
});

createApp(App).use(createPinia()).use(router).mount("#app");
