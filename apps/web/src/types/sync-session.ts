/** design.md §3.1 SyncSession — schema.md `sync_sessions` 매핑. 웹 콘솔에서는 아직
 * 동기화 모니터링 화면(apps/admin 예정)이 없어 사용되지 않는다. */
export type SyncDirection = "upload" | "download";
export type SyncStatus = "success" | "failed" | "retrying";

export interface SyncSession {
  id: string;
  deviceId: string;
  direction: SyncDirection;
  status: SyncStatus;
  checksum: string;
  retryCount: number;
}
