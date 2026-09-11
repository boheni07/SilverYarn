import { apiClient } from "@silveryarn/web-shared/api";
import type { Invitation } from "@/types";

/** GET /invitations/{token} — 무인증(토큰 자체가 접근 권한). 수락 전 미리보기용. */
export async function getInvitation(token: string): Promise<Invitation> {
  return apiClient.get<Invitation>(`/invitations/${token}`);
}

/** POST /invitations/{token}/accept — Keycloak 로그인 상태여야 한다(require_verified_subject).
 * 성공하면 호출자 토큰 sub가 family_members.keycloak_sub에 연결돼 이후 require_family로
 * 로그인할 수 있게 된다. */
export async function acceptInvitation(token: string, name: string): Promise<Invitation> {
  return apiClient.post<Invitation>(`/invitations/${token}/accept`, { name });
}
