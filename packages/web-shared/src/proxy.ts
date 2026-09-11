/**
 * Next.js 16 Proxy(구 middleware) 핸들러 — apps/web·apps/admin이 자기 `src/proxy.ts`에서
 * `export { proxy } from "@silveryarn/web-shared/proxy"`로 재노출한다
 * (Next는 앱 루트의 `src/proxy.ts`만 미들웨어로 인식).
 *
 * `config.matcher`는 Next가 정적 리터럴로만 읽으므로(import·변수 불가) 각 앱의
 * `src/proxy.ts`가 직접 선언한다 — 공유 대상은 이 핸들러(`proxy`)뿐. 표준 matcher:
 * `["/((?!login|api/auth|_next/static|_next/image|favicon.ico).*)"]`
 *
 * 로그인 안 된 요청은 Auth.js `authorized` 콜백(auth.ts)이 `/login`으로 보낸다.
 */
export { auth as proxy } from "./auth";
