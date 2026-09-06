// Copyright (c) 2026 Athena Decisions Systems SAS.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Base path: "/" in dev, "/advent/" in production (behind nginx).
export default defineConfig({
  base: process.env.VITE_BASE_PATH ?? "/",
  plugins: [react()],
  server: {
    port: 3040,
    proxy: { "/api": "http://localhost:8040" },
  },
});
