import { apiClient } from "@silveryarn/web-shared/api";

/**
 * 가족 대시보드(WF1) "오늘 대화" 통계 전용 — transcript_*(PII)는 내려받지 않고
 * 개수만 조회한다. `since`는 "오늘"의 경계를 호출자(클라이언트 로케일 자정)가 정한다.
 */
export async function countConversationChunksSince(userId: string, since: Date): Promise<number> {
  const result = await apiClient.get<{ count: number }>(
    `/users/${userId}/conversation-chunks/count?since=${encodeURIComponent(since.toISOString())}`,
  );
  return result.count;
}
