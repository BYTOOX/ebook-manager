import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

const apiProxyTarget = process.env.VITE_DEV_API_PROXY_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: [
        "brand/favicon.png",
        "brand/aurelia-icon.png",
        "brand/aurelia-icon-192.png",
        "brand/aurelia-icon-512.png",
        "brand/aurelia-logo-full.png",
        "brand/aurelia-logo-small.png"
      ],
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
            src: "/brand/aurelia-icon-192.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "any maskable"
          },
          {
            src: "/brand/aurelia-icon-512.png",
            sizes: "512x512",
            type: "image/png",
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
    allowedHosts: ["books.bytoox.ch"],
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
