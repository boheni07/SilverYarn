/** design.md §3.1(v0.7) SyncSession — schema.md `sync_sessions` 매핑. 동기화 모니터링
 * 화면은 apps/admin에 있다 — apps/web에서는 타입만 두고 쓰지 않는다. */
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
