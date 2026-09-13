/** design.md §3.1 ConsentLog — `consent_logs`는 백엔드 구현됨(consent 모듈).
 * `NotificationSetting`은 백엔드 구현이 끝나 별도 파일(`notification-setting.ts`)로
 * 옮겼다 — 여기 두면 안 됨. `Publication`도 마찬가지로 실제 구현 후 `publication.ts`로
 * 옮겼다(이전엔 미구현 placeholder였음, design.md §2.6). */
export type ConsentType = "data_collection" | "external_tts_optin" | "external_llm_optin";

export const CONSENT_TYPES: ConsentType[] = [
  "data_collection",
  "external_tts_optin",
  "external_llm_optin",
];

export const CONSENT_TYPE_LABEL: Record<ConsentType, string> = {
  data_collection: "개인정보 수집·이용",
  external_tts_optin: "외부 TTS 연계",
  external_llm_optin: "외부 LLM 연계",
};

export interface ConsentLog {
  id: string;
  userId: string;
  consentType: ConsentType;
  granted: boolean;
  grantedBy?: string;
  /** "self" | "proxy" — 서버가 grantedBy 유무에서 파생(decisions.md #53, 2026-09-12
   * 사용자 결정으로 가족 대리동의를 법적으로 유효 인정). */
  actor: "self" | "proxy";
  grantedAt: string;
}

/** GET /users/{userId}/consent-state 응답 — 유형별 현재 동의 상태(최신 행 기준).
 * 한 번도 기록이 없는 유형은 키가 아예 빠진다(백엔드 `ConsentService.current_state`
 * 문서 참조) — 미동의와 동일하게 취급해 `false`로 다뤄야 한다. */
export type ConsentState = Partial<Record<ConsentType, boolean>>;
