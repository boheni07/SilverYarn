import "server-only";

/**
 * 서버 API 클라이언트 (공유 — apps/web·apps/admin). Infrastructure 레이어(CONVENTIONS §3.2).
 * 각 앱의 `services/`만 이 모듈을 쓴다(`app/`·`components/`·`features/`에서 직접 import 금지 —
 * 각 앱 eslint 규칙으로 강제).
 *
 * **server-only**: 서버(Server Component·Server Action·Route Handler)에서만 실행되며,
 * Keycloak 액세스 토큰을 세션(httpOnly 쿠키, decisions #49)에서 읽어 백엔드
 * `Authorization: Bearer`로 실어 보낸다 — 토큰이 브라우저 번들에 안 들어가게.
 *
 * design.md §4.1 표준 응답 포맷을 그대로 따른다: { data } | { data, pagination } | { error }.
 */
import { auth } from "../auth";
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

export interface Pagination {
  page: number;
  pageSize: number;
  total: number;
}

interface ApiEnvelope<T> {
  data?: T;
  pagination?: { page: number; page_size: number; total: number };
  error?: { code: string; message: string; details?: Record<string, unknown> };
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  /** 명시하면 세션 토큰 대신 이 값을 Bearer로 쓴다(테스트·특수 경로용). */
  authToken?: string;
  deviceToken?: string;
}

async function fetchEnvelope(path: string, options: RequestOptions): Promise<ApiEnvelope<unknown>> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };

  const bearer = options.authToken ?? (await auth())?.accessToken;
  if (bearer) headers["Authorization"] = `Bearer ${bearer}`;
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

  return json;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const json = await fetchEnvelope(path, options);
  return keysToCamel<T>(json.data as never);
}

/** { data, pagination } 봉투 전체가 필요한 목록 조회용 — 지금은 GET /users만 이 모양을
 * 실제로 반환한다(design.md §4.1 PaginatedResponse). */
async function requestPaginated<T>(
  path: string,
  options: Omit<RequestOptions, "method" | "body"> = {},
): Promise<{ data: T[]; pagination: Pagination }> {
  const json = await fetchEnvelope(path, { ...options, method: "GET" });
  return {
    data: keysToCamel<T[]>(json.data as never),
    pagination: keysToCamel<Pagination>(json.pagination as never),
  };
}

export const apiClient = {
  get: <T>(path: string, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "GET" }),
  getPaginated: requestPaginated,
  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "POST", body }),
  put: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "PUT", body }),
};
