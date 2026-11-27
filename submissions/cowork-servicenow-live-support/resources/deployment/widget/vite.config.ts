import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  plugins: [viteSingleFile()],
  build: {
    target: "es2022",
    cssCodeSplit: false,
    assetsInlineLimit: 100_000_000,
    sourcemap: false,
  },
  server: {
    host: "127.0.0.1",
    proxy: {
      "/dev": "http://127.0.0.1:5078",
    },
  },
});
