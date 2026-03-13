import { defineConfig } from "vite";

import anywidget from "@anywidget/vite";
import wasm from "vite-plugin-wasm";
import topLevelAwait from "vite-plugin-top-level-await";

export default defineConfig({
  build: {
    outDir: "src/maia_waterfall_widget/static",
    lib: {
      entry: ["js/widget.js"],
      formats: ["es"],
    },
  },
  plugins: [
    anywidget(),
    wasm(),
    topLevelAwait(),
  ],
});
