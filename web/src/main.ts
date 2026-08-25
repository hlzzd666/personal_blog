import { createApp } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import AboutPage from "./pages/AboutPage.vue";
import ArticleDetailPage from "./pages/ArticleDetailPage.vue";
import ArticlesPage from "./pages/ArticlesPage.vue";
import "./styles.css";

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
    { path: "/about", component: AboutPage, meta: { title: "关于我" } },
    { path: "/articles", component: ArticlesPage, meta: { title: "文章" } },
    { path: "/articles/:slug", component: ArticleDetailPage, meta: { title: "文章详情" } },
  ],
});

router.afterEach((to) => {
  document.title = `${String(to.meta.title ?? "个人空间")} | 个人博客`;
});

createApp(App).use(createPinia()).use(router).mount("#app");
