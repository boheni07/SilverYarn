import { apiClient } from "@silveryarn/web-shared/api";
import type { Device } from "@/types";

/**
 * GET /users/{userId}/devices — design.md §4.2 M-8 정정(소유자 중첩 규칙).
 * 기기 전체를 조직 단위로 훑어보는 "전체 기기 목록" 엔드포인트는 아직 없다 — 지금은
 * 사용자 단위로만 조회 가능(README "아직 안 된 것" 참조).
 */
export async function listUserDevices(userId: string): Promise<Device[]> {
  return apiClient.get<Device[]>(`/users/${userId}/devices`);
}
