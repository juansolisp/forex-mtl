import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
  },
  server: {
    proxy: {
      "/auth": {
        target: "http://localhost:9090",
        changeOrigin: true,
      },
      "/rates": {
        target: "http://localhost:9090",
        changeOrigin: true,
      },
      // Proxy SSE endpoint so the browser connects on the same Vite origin.
      // Without this, EventSource("/events") would hit :5174 instead of :9090.
      "/events": {
        target: "http://localhost:9090",
        changeOrigin: true,
      },
      "/config": {
        target: "http://localhost:9090",
        changeOrigin: true,
      },
      // Direct proxy to One-Frame — bypasses our cache entirely.
      // Used by the rate-limit stress test to deliberately exhaust the quota.
      "/one-frame": {
        target: "http://localhost:18080",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/one-frame/, ""),
      },
    },
  },
});
