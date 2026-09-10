export { proxy } from "@silveryarn/web-shared/proxy";

// Next는 `config.matcher`를 정적 리터럴로만 읽는다(import·변수 불가) — 공유 핸들러
// (@silveryarn/web-shared/proxy)와 달리 matcher만 각 앱에 인라인으로 둔다.
export const config = {
  matcher: ["/((?!login|api/auth|_next/static|_next/image|favicon.ico).*)"],
};
