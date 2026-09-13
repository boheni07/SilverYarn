import { apiClient } from "@silveryarn/web-shared/api";
import type { RetentionPolicy } from "@/types";

/** GET /retention-policies — decisions.md #56(Q5) admin 전용 보유기간 설정 목록. */
export async function listRetentionPolicies(): Promise<RetentionPolicy[]> {
  return apiClient.get<RetentionPolicy[]>("/retention-policies");
}

/** PUT /retention-policies/{category} — 보유일수 조정. 법무 결정 사항이 아니라
 * 운영 판단이라 하드코딩하지 않고 admin이 직접 바꾼다(마이그레이션 0012 주석 참조). */
export async function updateRetentionPolicy(
  category: string,
  retentionDays: number,
): Promise<RetentionPolicy> {
  return apiClient.put<RetentionPolicy>(`/retention-policies/${category}`, { retentionDays });
}
