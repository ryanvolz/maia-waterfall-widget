import { defineConfig } from "vite";

import anywidget from "@anywidget/vite";

export default defineConfig({
  build: {
    outDir: "maia_waterfall_widget/static",
    lib: {
      entry: ["src/widget.js"],
      formats: ["es"],
    },
  },
  plugins: [anywidget()],
});
