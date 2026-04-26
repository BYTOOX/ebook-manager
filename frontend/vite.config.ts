import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

const apiProxyTarget = process.env.VITE_DEV_API_PROXY_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg", "aurelia-mark.svg"],
      manifest: {
        name: "Aurelia",
        short_name: "Aurelia",
        description: "Bibliotheque EPUB personnelle offline-first.",
        theme_color: "#050505",
        background_color: "#050505",
        display: "standalone",
        start_url: "/",
        scope: "/",
        icons: [
          {
            src: "/aurelia-mark.svg",
            sizes: "any",
            type: "image/svg+xml",
            purpose: "any maskable"
          }
        ]
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg,png,ico}"],
        navigateFallback: "/index.html",
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith("/api/v1/books"),
            handler: "NetworkFirst",
            options: {
              cacheName: "aurelia-api-books",
              networkTimeoutSeconds: 3
            }
          }
        ]
      }
    })
  ],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path
      }
    }
  },
  preview: {
    port: 3000,
    host: "0.0.0.0",
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path
      }
    }
  }
});
