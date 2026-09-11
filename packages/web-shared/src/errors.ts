/**
 * Application 레이어가 Infrastructure(api/client)의 에러 타입을 감싸 재노출한다.
 * 각 앱의 Presentation은 이 경로를 통해서만 `ApiError`를 다룬다.
 */
export { ApiError } from "./api/client";
