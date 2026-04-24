import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import AutoImport from "unplugin-auto-import/vite";
import Components from "unplugin-vue-components/vite";
import { ElementPlusResolver } from "unplugin-vue-components/resolvers";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [
      vue(),
      AutoImport({
        dts: "auto-imports.d.ts",
        resolvers: [ElementPlusResolver()]
      }),
      Components({
        dts: "components.d.ts",
        resolvers: [ElementPlusResolver()]
      })
    ],
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes("node_modules")) {
              return undefined;
            }

            if (id.includes("@element-plus/icons-vue")) {
              return "element-plus-icons";
            }

            if (id.includes("async-validator")) {
              return "async-validator";
            }

            if (id.includes("dayjs")) {
              return "dayjs";
            }

            if (id.includes("@floating-ui") || id.includes("@popperjs/core")) {
              return "floating-ui";
            }

            if (id.includes("lodash-unified") || id.includes("lodash-es")) {
              return "lodash";
            }

            if (id.includes("element-plus")) {
              return undefined;
            }

            if (id.includes("vue-router")) {
              return "vue-router";
            }

            if (id.includes("axios")) {
              return "http-client";
            }

            return "vendor";
          }
        }
      }
    },
    server: {
      port: 5173,
      host: "0.0.0.0",
      proxy: {
        "/api": {
          target: env.VITE_API_PROXY_TARGET || "http://localhost:8000",
          changeOrigin: true
        }
      }
    }
  };
});
