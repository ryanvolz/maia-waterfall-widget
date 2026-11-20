import { defineConfig } from "vite";
import cssInjectedByJsPlugin from 'vite-plugin-css-injected-by-js';
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue({}), cssInjectedByJsPlugin()],
  build: {
    cssCodeSplit: true,
    outDir: "./maia_waterfall_nicegui/components",
    lib: {
      entry: {
        waterfall: "./src/waterfall.vue",
      },
      formats: ["es"],
      fileName: (format, entryName) => `${entryName}.js`,
      name: "maia_waterfall_nicegui",
    },
    minify: false,
    rollupOptions: {
      external: ["vue"],
      output: {
        entryFileNames: `[name].js`,
        chunkFileNames: `[name].js`,
        assetFileNames: `[name].[ext]`,
      },
    },
  },
});
