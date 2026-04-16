import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const ECP_PROXY_TARGET = process.env.ECP_BASE_URL || "http://localhost:8080";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      "/api": {
        target: ECP_PROXY_TARGET,
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "happy-dom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
  },
});
