import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import importPlugin from "eslint-plugin-import";

// CONVENTIONS.md §3.2: "계층 규율은 폴더 중첩이 아니라 ESLint import/no-restricted-paths로
// 강제한다." app/·components/·features/는 lib/api/(Infrastructure)를 직접 import할 수
// 없다 — services/(Application)를 거쳐야 한다.
const layerBoundaries = {
  plugins: { import: importPlugin },
  rules: {
    "import/no-restricted-paths": [
      "error",
      {
        zones: [
          {
            target: "./src/app",
            from: "./src/lib/api",
            message:
              "app/ 라우트는 lib/api/를 직접 import할 수 없습니다 — services/를 통해서만 접근하세요 (CONVENTIONS.md §3.2).",
          },
          {
            target: "./src/components",
            from: "./src/lib/api",
            message: "components/는 lib/api/를 직접 import할 수 없습니다 — services/를 통해서만 접근하세요.",
          },
          {
            target: "./src/features",
            from: "./src/lib/api",
            message: "features/는 lib/api/를 직접 import할 수 없습니다 — services/를 통해서만 접근하세요.",
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
