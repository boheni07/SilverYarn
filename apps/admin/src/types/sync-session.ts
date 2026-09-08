/** design.md §3.1(v0.7) SyncSession — schema.md `sync_sessions` 매핑.
 * apps/web/src/types/sync-session.ts와 동일 — 공유 패키지가 아직 없어 두 앱이 각자 들고 있다. */
export type SyncDirection = "upload" | "download";
export type SyncStatus = "success" | "failed" | "retrying";

export interface SyncSession {
  id: string;
  deviceId: string;
  direction: SyncDirection;
  status: SyncStatus;
  checksum: string;
  retryCount: number;
  startedAt: string;
  finishedAt?: string;
}

/** 한글 표시명 — schema.md §7에 아직 sync_status 매핑이 없어 apps/admin 스캐폴딩 시
 * 새로 정한 값. 나중에 §7에 정식 편입 필요(device.ts의 INSTALL_MODE_LABEL과 동일 사유). */
export const SYNC_STATUS_LABEL: Record<SyncStatus, string> = {
  success: "성공",
  failed: "실패",
  retrying: "재시도중",
};

export const SYNC_DIRECTION_LABEL: Record<SyncDirection, string> = {
  upload: "업로드",
  download: "다운로드",
};
