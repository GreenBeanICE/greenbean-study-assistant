import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcovonly"],
      reportsDirectory: "coverage/frontend",
      exclude: [
        "node_modules/",
        "dist/",
        "build/",
        "src/main.tsx",
        "src/**/*.d.ts",
      ],
    },
  },
});
