import { apiClient } from "@silveryarn/web-shared/api";
import type { ConsentLog, ConsentState, ConsentType } from "@/types";

/** design.md §4.2 GET /users/{userId}/consent-state — 유형별 현재 동의 상태. */
export async function getConsentState(userId: string): Promise<ConsentState> {
  const res = await apiClient.get<{ state: ConsentState }>(`/users/${userId}/consent-state`);
  return res.state;
}

/** design.md §4.2 GET /users/{userId}/consent-logs — 전체 동의 이력(신규/철회 포함). */
export async function listConsentLogs(userId: string): Promise<ConsentLog[]> {
  return apiClient.get<ConsentLog[]>(`/users/${userId}/consent-logs`);
}

/**
 * POST /users/{userId}/consent-logs — 동의(또는 철회) 1건 기록.
 * `grantedBy`를 채우면 가족 대리 동의(proxy, decisions.md #53 — 2026-09-12 사용자 결정으로
 * 법적 유효성 인정)로 남는다. 백엔드가 호출자 본인의 구성원 id인지 검증한다.
 */
export async function recordConsent(
  userId: string,
  input: { consentType: ConsentType; granted: boolean; grantedBy?: string },
): Promise<ConsentLog> {
  return apiClient.post<ConsentLog>(`/users/${userId}/consent-logs`, input);
}
