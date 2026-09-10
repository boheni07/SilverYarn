import type { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    /** Keycloak 액세스 토큰 — lib/api/client.ts가 백엔드 Bearer로 실어 보낸다. */
    accessToken?: string;
    /** 토큰 갱신 실패 시 "RefreshFailed" — 미들웨어가 재로그인을 강제한다. */
    error?: "RefreshFailed";
    user?: DefaultSession["user"];
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    /** 액세스 토큰 만료 시각 (epoch seconds). */
    expiresAt?: number;
    error?: "RefreshFailed";
  }
}
