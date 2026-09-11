/**
 * Auth.js 라우트 핸들러 — 각 앱의 `app/api/auth/[...nextauth]/route.ts`가
 * `export { GET, POST } from "@silveryarn/web-shared/auth-route"`로 재노출한다.
 */
import { handlers } from "./auth";

export const { GET, POST } = handlers;
