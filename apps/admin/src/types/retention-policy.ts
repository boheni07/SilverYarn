/** decisions.md #56(Q5, 2026-09-13) RetentionPolicy — schema.md `retention_policies`
 * 테이블과 1:1 매핑. 보유기간을 하드코딩하지 않고 admin이 조정하는 설정값. */
export interface RetentionPolicy {
  id: string;
  category: string;
  retentionDays: number;
  updatedAt: string;
}

/** category 상수 — 서버 `RetentionCategory`와 동일(지금은 대화 원문 하나뿐). */
export const RETENTION_CATEGORY_LABEL: Record<string, string> = {
  conversation_transcript: "대화 원문(conversation_chunks)",
};
