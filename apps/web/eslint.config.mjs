import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

// CONVENTIONS.md §3.2: "계층 규율은 폴더 중첩이 아니라 ESLint로 강제한다."
// API 클라이언트(`@silveryarn/web-shared/api`, Infrastructure)는 각 앱의 `services/`
// (Application)만 쓴다 — `app/`·`components/`·`features/`에서 직접 import 금지.
const layerBoundaries = {
  files: ["src/app/**", "src/components/**", "src/features/**"],
  rules: {
    "no-restricted-imports": [
      "error",
      {
        paths: [
          {
            name: "@silveryarn/web-shared/api",
            message: "API 클라이언트는 services/를 통해서만 접근하세요 (CONVENTIONS.md §3.2).",
          },
        ],
      },
    ],
  },
};

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  layerBoundaries,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
