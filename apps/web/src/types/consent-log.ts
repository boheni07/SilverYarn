/** design.md §3.1 ConsentLog/NotificationSetting/Publication — 아직 백엔드 모듈 미구현.
 * schema.md `consent_logs`/`notification_settings`/`publications` 매핑. */
export interface ConsentLog {
  id: string;
  userId: string;
  consentType: "data_collection" | "external_tts_optin" | "external_llm_optin";
  granted: boolean;
  grantedBy?: string;
}

export interface NotificationSetting {
  id: string;
  familyMemberId: string;
  channel: "sms" | "email" | "push";
  receivesEmotionAlerts: boolean;
  receivesChapterUpdates: boolean;
  receivesSyncIssues: boolean;
}

export interface Publication {
  id: string;
  userId: string;
  format: "hardcover_pdf" | "epub";
  status: "requested" | "processing" | "ready" | "delivered";
  storageRef?: string;
}
