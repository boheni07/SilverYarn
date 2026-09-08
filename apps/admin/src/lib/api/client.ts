/**
 * 서버 API 클라이언트 — Infrastructure 레이어(CONVENTIONS §3.2). `services/`만 이 파일을
 * import한다(app/·components/·features/에서 직접 쓰지 않음 — eslint.config.mjs의
 * import/no-restricted-paths로 강제).
 *
 * design.md §4.1 표준 응답 포맷을 그대로 따른다: { data } | { data, pagination } | { error }.
 * apps/web/src/lib/api/client.ts와 동일 — 공유 패키지가 아직 없어 두 앱이 각자 들고 있다.
 */
import { keysToCamel, keysToSnake } from "./case";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly details: Record<string, unknown> = {},
    public readonly status: number = 500,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface ApiEnvelope<T> {
  data?: T;
  pagination?: { page: number; pageSize: number; total: number };
  error?: { code: string; message: string; details?: Record<string, unknown> };
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  /** 인증 스텁 — core/auth.py가 아직 미검증이라 지금은 아무 값이나 통과한다.
   * TODO: Keycloak 연동 후 실제 관리자 세션 토큰으로 교체. */
  authToken?: string;
  deviceToken?: string;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (options.authToken) headers["Authorization"] = `Bearer ${options.authToken}`;
  if (options.deviceToken) headers["X-Device-Token"] = options.deviceToken;

  const response = await fetch(`${API_BASE_URL}${API_PREFIX}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(keysToSnake(options.body)) : undefined,
    // 백엔드 데이터가 요청마다 바뀌므로 캐시하지 않는다(Next.js 15+ 캐싱 모델 기준).
    cache: "no-store",
  });

  const json = (await response.json().catch(() => ({}))) as ApiEnvelope<unknown>;

  if (!response.ok || json.error) {
    const err = json.error ?? { code: "INTERNAL_ERROR", message: "알 수 없는 오류가 발생했습니다." };
    throw new ApiError(err.code, err.message, err.details ?? {}, response.status);
  }

  return keysToCamel<T>(json.data as never);
}

export const apiClient = {
  get: <T>(path: string, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "POST", body }),
  put: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "PUT", body }),
};
