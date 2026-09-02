import { defineConfig } from "@playwright/test";

// E2E smoke path, including the network-off demo-resilience run (build prompt Sec.33).
// Requires the app running against the seeded dataset: `make seed && make backend &&
// npm run dev`, then `npm run e2e`.
export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  use: {
    baseURL: "http://localhost:3000",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
