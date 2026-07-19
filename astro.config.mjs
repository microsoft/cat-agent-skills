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
    // Dev-only proxy so the badge "Sign in with GitHub" device flow can reach
    // GitHub's OAuth device endpoints, which send no CORS headers. Only used
    // when PUBLIC_GH_CLIENT_ID is configured; the username box needs no network.
    // A production deploy would need its own equivalent tiny proxy.
    server: {
      proxy: {
        "/__gh": {
          target: "https://github.com",
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/__gh/, ""),
        },
      },
    },
  },
});
