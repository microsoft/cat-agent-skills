// @ts-check
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

// GitHub Pages deployment: served from /cat-agent-skills
export default defineConfig({
  site: "https://microsoft.github.io",
  base: "/cat-agent-skills",
  trailingSlash: "ignore",
  vite: {
    plugins: [tailwindcss()],
  },
});
