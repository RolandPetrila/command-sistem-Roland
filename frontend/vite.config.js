import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icons/icon-192.png", "icons/icon-512.png"],
      manifest: {
        name: "Roland - Command Center",
        short_name: "Roland CC",
        description:
          "Panou personal multifunctional — calculator traduceri, tool-uri rapide, facturare",
        theme_color: "#0f172a",
        background_color: "#0f172a",
        display: "standalone",
        orientation: "any",
        start_url: "/",
        scope: "/",
        icons: [
          {
            src: "/icons/icon-192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "/icons/icon-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any maskable",
          },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,png,svg,woff,woff2}"],
        skipWaiting: true,
        clientsClaim: true,
        cleanupOutdatedCaches: true,
        runtimeCaching: [
          {
            urlPattern: /\/api\/itp\//,
            handler: "NetworkFirst",
            options: {
              cacheName: "itp-cache",
              expiration: { maxEntries: 100, maxAgeSeconds: 86400 },
              networkTimeoutSeconds: 5,
            },
          },
          {
            urlPattern: /\/api\/invoice\/(invoices|clients)/,
            handler: "NetworkFirst",
            options: {
              cacheName: "invoice-cache",
              expiration: { maxEntries: 200, maxAgeSeconds: 86400 },
              networkTimeoutSeconds: 5,
            },
          },
          {
            urlPattern: /\/api\/quick-tools\/notes/,
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: "notes-cache",
              expiration: { maxEntries: 50, maxAgeSeconds: 604800 },
            },
          },
          {
            urlPattern: /\/api\/time\//,
            handler: "NetworkFirst",
            options: {
              cacheName: "time-cache",
              expiration: { maxEntries: 100, maxAgeSeconds: 86400 },
              networkTimeoutSeconds: 5,
            },
          },
          {
            urlPattern: /^https?:\/\/.*\/api\//,
            handler: "NetworkFirst",
            options: {
              cacheName: "api-cache",
              expiration: { maxEntries: 50, maxAgeSeconds: 300 },
            },
          },
          {
            urlPattern: /\.(?:js|css|woff2?)$/,
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: "static-resources",
              expiration: { maxEntries: 100 },
            },
          },
        ],
      },
    }),
  ],
  build: {
    outDir: "dist",
    sourcemap: false,
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        manualChunks: {
          "vendor-react": ["react", "react-dom", "react-router-dom"],
          "vendor-ui": ["lucide-react"],
          "vendor-charts": ["recharts"],
          "vendor-axios": ["axios"],
        },
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test-setup.js",
  },
  server: {
    port: 5173,
    host: true, // 0.0.0.0 — accesibil din Tailscale si Cloudflare tunnel
    allowedHosts: true,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
        changeOrigin: true,
      },
    },
  },
});
