import { apiClient } from "@/lib/api/client";
import type { Pagination } from "@/lib/api/client";
import type { SyncSession, SyncStatus } from "@/types";

// Presentation이 lib/api를 직접 import할 수 없으므로(eslint import/no-restricted-paths)
// services/users.ts와 동일하게 여기서 재노출한다.
export type { Pagination };

/**
 * GET /sync/sessions — 관리자 조회 전용 목록 엔드포인트(2026-09-08 신규, 09-08 페이지네이션+
 * 전체 기기 통합 모니터링으로 확장). deviceId를 주면 기기 하나의 이력, 생략하면 전체
 * 기기를 아우른다 — 둘 다 같은 백엔드 엔드포인트(GET /sync/sessions?device_id=)다.
 * status로 성공/실패/재시도중만 골라볼 수 있다.
 * 기기 자신이 자기 업로드 상태를 폴링하는 GET /sync/sessions/{id}(Device Token 인증)와는
 * 별개다.
 */
export async function listSyncSessions(params: {
  page: number;
  pageSize: number;
  deviceId?: string;
  status?: SyncStatus;
}): Promise<{ sessions: SyncSession[]; pagination: Pagination }> {
  const query = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.pageSize),
  });
  if (params.deviceId) query.set("device_id", params.deviceId);
  if (params.status) query.set("status", params.status);

  const { data, pagination } = await apiClient.getPaginated<SyncSession>(`/sync/sessions?${query}`, {
    authToken: "dev",
  });
  return { sessions: data, pagination };
}
