import { apiClient } from "@/lib/api/client";
import type { SyncSession } from "@/types";

/**
 * GET /sync/sessions?device_id=... — 관리자 조회 전용 목록 엔드포인트(2026-09-08 신규).
 * 기기 자신이 자기 업로드 상태를 폴링하는 GET /sync/sessions/{id}(Device Token 인증)와는
 * 별개다. "전체 기기 통합 모니터링"은 아직 없다 — 기기 하나씩만 조회 가능
 * (apps/admin/README.md "아직 안 된 것" 참조).
 */
export async function listDeviceSyncSessions(deviceId: string): Promise<SyncSession[]> {
  return apiClient.get<SyncSession[]>(`/sync/sessions?device_id=${deviceId}`, { authToken: "dev" });
}
