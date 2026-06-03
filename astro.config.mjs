// @ts-check
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

// GitHub Pages deployment: served from /copilot-studio-skills-gallery
export default defineConfig({
  site: "https://microsoft.github.io",
  base: "/copilot-studio-skills-gallery",
  trailingSlash: "ignore",
  vite: {
    plugins: [tailwindcss()],
  },
});
