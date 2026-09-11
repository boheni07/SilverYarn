import NextAuth from "next-auth";
import type { JWT } from "next-auth/jwt";
import Keycloak from "next-auth/providers/keycloak";

/**
 * 웹 콘솔 Keycloak SSO (decisions.md #17, design.md §7.4).
 *
 * `silveryarn-web`은 **public client**(비밀 없음, PKCE) + auth code flow. Auth.js가
 * 로그인 리다이렉트·토큰 교환·갱신·httpOnly 세션 쿠키를 처리한다. 액세스 토큰은
 * `session.accessToken`으로 노출돼 `lib/api/client.ts`(server-only)가 백엔드
 * `Authorization: Bearer`로 실어 보낸다.
 *
 * 필요 env (apps/web/.env.local):
 * - AUTH_SECRET               — 세션 암호화 키 (`npx auth secret`)
 * - AUTH_KEYCLOAK_ID          — "silveryarn-web"
 * - AUTH_KEYCLOAK_ISSUER      — http://localhost:9678/realms/silveryarn
 * - AUTH_KEYCLOAK_SECRET      — public client라 빈 값 (Auth.js 타입상 필요)
 */
async function refreshAccessToken(token: JWT): Promise<JWT> {
  if (!token.refreshToken || !process.env.AUTH_KEYCLOAK_ISSUER) {
    return { ...token, error: "RefreshFailed" };
  }
  try {
    const response = await fetch(`${process.env.AUTH_KEYCLOAK_ISSUER}/protocol/openid-connect/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "refresh_token",
        client_id: process.env.AUTH_KEYCLOAK_ID ?? "",
        refresh_token: token.refreshToken,
      }),
    });
    const refreshed = (await response.json()) as {
      access_token: string;
      expires_in: number;
      refresh_token?: string;
    };
    if (!response.ok) throw new Error("refresh response not ok");
    return {
      ...token,
      accessToken: refreshed.access_token,
      expiresAt: Math.floor(Date.now() / 1000 + refreshed.expires_in),
      refreshToken: refreshed.refresh_token ?? token.refreshToken,
      error: undefined,
    };
  } catch {
    return { ...token, error: "RefreshFailed" };
  }
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Keycloak({
      clientId: process.env.AUTH_KEYCLOAK_ID,
      clientSecret: process.env.AUTH_KEYCLOAK_SECRET ?? "",
      issuer: process.env.AUTH_KEYCLOAK_ISSUER,
      // public client — 토큰 엔드포인트에 클라이언트 인증 안 함(PKCE만).
      client: { token_endpoint_auth_method: "none" },
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        return {
          ...token,
          accessToken: account.access_token,
          refreshToken: account.refresh_token,
          expiresAt: account.expires_at,
        };
      }
      if (token.expiresAt && Date.now() < token.expiresAt * 1000 - 30_000) {
        return token; // 아직 유효 (만료 30초 전까지)
      }
      return refreshAccessToken(token);
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken;
      session.error = token.error;
      return session;
    },
    authorized({ auth: session }) {
      return !!session?.accessToken && session.error !== "RefreshFailed";
    },
  },
  pages: { signIn: "/login" },
});
