import { defineConfig } from "vite";

import anywidget from "@anywidget/vite";

export default defineConfig({
  build: {
    outDir: "src/maia_waterfall_widget/static",
    lib: {
      entry: ["js/widget.js"],
      formats: ["es"],
    },
  },
  plugins: [anywidget()],
});
