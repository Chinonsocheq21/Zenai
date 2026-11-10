import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

export default defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    // Plain apostrophes and quotes in page copy are fine in React; flag, don't fail.
    rules: { "react/no-unescaped-entities": "warn" },
  },
  globalIgnores([".next/**", "out/**", "node_modules/**", "test-results/**", "playwright-report/**", "next-env.d.ts"]),
]);
