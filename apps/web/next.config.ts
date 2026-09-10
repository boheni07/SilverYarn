import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // packages/web-shared는 TS 소스를 그대로 노출한다 — Turbopack은 워크스페이스
  // 패키지를 자동 트랜스파일하지만, dev·webpack 경로까지 확실히 하려고 명시한다.
  transpilePackages: ["@silveryarn/web-shared"],
};

export default nextConfig;
