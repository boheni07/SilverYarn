/** design.md §3.1 ConsentLog/Publication — `consent_logs`는 백엔드 구현됨(consent 모듈),
 * `publications`는 테이블만 있고 API 미구현(Phase 3). `NotificationSetting`은 백엔드
 * 구현이 끝나 별도 파일(`notification-setting.ts`)로 옮겼다 — 여기 두면 안 됨. */
export interface ConsentLog {
  id: string;
  userId: string;
  consentType: "data_collection" | "external_tts_optin" | "external_llm_optin";
  granted: boolean;
  grantedBy?: string;
}

export interface Publication {
  id: string;
  userId: string;
  format: "hardcover_pdf" | "epub";
  status: "requested" | "processing" | "ready" | "delivered";
  storageRef?: string;
}
