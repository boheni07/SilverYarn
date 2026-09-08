/**
 * Application 레이어가 Infrastructure(lib/api/client)의 에러 타입을 감싸 재노출한다.
 * Presentation(app/·components/·features/)은 이 파일을 통해서만 에러를 다뤄야 한다
 * (CONVENTIONS.md §3.2, eslint import/no-restricted-paths가 lib/api 직접 import를 막는다).
 */
export { ApiError } from "@/lib/api/client";
