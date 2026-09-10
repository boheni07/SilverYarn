export { auth as proxy } from "@/auth";

/**
 * Next.js 16 Proxy(구 middleware) — 로그인 안 된 요청은 Auth.js `authorized`
 * 콜백(auth.ts)이 `/login`으로 보낸다. `/login`·Auth.js API·정적 자원은 제외한다.
 */
export const config = {
  matcher: ["/((?!login|api/auth|_next/static|_next/image|favicon.ico).*)"],
};
