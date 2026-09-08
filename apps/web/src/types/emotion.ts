/** design.md §3.1 EmotionAlert/EmotionScore — schema.md `emotion_alerts`/`emotion_scores` 매핑.
 * ⚠️ Phase 1 피처플래그 OFF(decisions.md #25) — 서버 write 경로가 비활성이라 이 타입을
 * 쓰는 화면은 아직 없다.
 */
export interface EmotionAlert {
  id: string;
  userId: string;
  score: number;
  triggeredAt: string;
  acknowledgedBy?: string;
  closedAt?: string;
}

export interface EmotionScore {
  id: string;
  userId: string;
  recordedDate: string;
  score: number;
  note?: string;
}
