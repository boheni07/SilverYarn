/** design.md §3.1 ConversationChunk — schema.md `conversation_chunks` 매핑. */
export type ConversationMode = "author" | "care" | "assist";

export interface ConversationChunk {
  id: string;
  userId: string;
  transcriptOnDevice: string;
  transcriptServer?: string;
  metaPeriod?: string;
  metaPeople?: string[];
  metaPlace?: string;
  metaEmotion?: string;
  metaProsody?: Record<string, unknown>;
  linkedPhotoId?: string;
  sessionId?: string;
  turnId?: number;
  mode?: ConversationMode;
  /** ⚠️ PII, 암호화 대상(schema.md §5) — 관리자/디버그 화면 외에는 노출 자제. */
  assistantResponse?: string;
  createdAt: string;
}
