import { apiClient } from "@silveryarn/web-shared/api";
import type { FamilyRole, Invitation } from "@/types";

/**
 * POST /invitations — 첫 가족 구성원 연결(design.md §2.9 "가족 계정 웹 콘솔 초대"
 * 단계, v0.28에서 "별도 설계 결정 대기"로 남겨뒀던 것을 admin 중개 경로로 확정).
 *
 * 신규 온보딩된 어르신은 Device Token만 있고 family 권한이 없어 스스로
 * `POST /invitations`를 부를 수 없다 — admin이 대신 초대를 만들고, 결과 토큰으로
 * 만든 링크를 운영자가 가족에게 전달한다(문자/이메일 등 채널은 이번 스코프 밖).
 */
export async function createInvitation(input: {
  userId: string;
  contact: string;
  role: FamilyRole;
  invitedBy?: string;
}): Promise<Invitation> {
  return apiClient.post<Invitation>("/invitations", input);
}
