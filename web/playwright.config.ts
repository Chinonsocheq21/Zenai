import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  reporter: "list",
  use: { baseURL: "http://127.0.0.1:4321", channel: "chrome" },
  projects: [
    { name: "phone", use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
    { name: "laptop", use: { viewport: { width: 1440, height: 900 } } },
    { name: "tablet", use: { viewport: { width: 820, height: 1180 } } },
  ],
  webServer: { command: "npm run build && node tests/serve.mjs", url: "http://127.0.0.1:4321/", reuseExistingServer: false, timeout: 120_000 },
});
