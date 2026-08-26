import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const apiProxyTarget = env.DEV_API_PROXY_TARGET || "http://127.0.0.1:8000";

  return {
    base: mode === "production" ? "/web/" : "/",
    plugins: [vue(), tailwindcss()],
    resolve: {
      extensions: [".ts", ".tsx", ".mjs", ".js", ".mts", ".jsx", ".json"],
    },
    server: {
      proxy: {
        "/api": {
          target: apiProxyTarget,
          changeOrigin: true,
        },
        "/uploads": {
          target: apiProxyTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
