import { redirect } from "next/navigation";
import { apiClient } from "@silveryarn/web-shared/api";
import type { FamilyRole } from "@/types";

/**
 * 로그인 세션(Keycloak)이 어느 어르신(들)에 연결돼 있는지 — 백엔드 `GET /me`가
 * `AuthContext.memberships`를 그대로 직렬화한 것(core_service `me.py` 참조).
 *
 * 이 모듈이 생기기 전에는 화면마다 `?userId=`를 사람이 직접 입력해야 했다
 * (screen-definitions.md §0.3 "임시방편") — 이제 로그인 세션에서 자동 해석한다.
 */
export interface Membership {
  familyMemberId: string;
  userId: string;
  role: FamilyRole;
  twoFactorEnabled: boolean;
  orgId: string | null;
}

export async function getMyMemberships(): Promise<Membership[]> {
  const result = await apiClient.get<{ memberships: Membership[] }>("/me");
  return result.memberships;
}

/**
 * `requestedUserId`(`?elder=` 쿼리스트링 — 여러 어르신에 연결된 경우 홈에서 고른 값)가
 * 실제로 이 세션의 멤버십인지 확인하고 그 멤버십을 돌려준다.
 *
 * - 멤버십이 정확히 1건이면 `requestedUserId`가 없거나 일치하지 않아도 그 1건으로 확정한다
 *   (파일럿 스코프의 지배적 케이스 — 1인 가족구성원:1어르신, decisions.md #63).
 * - 여러 건인데 `requestedUserId`가 없거나 그중 하나와 일치하지 않으면 "/"(어르신 선택)로
 *   보낸다.
 */
export async function resolveCurrentMembership(requestedUserId?: string): Promise<Membership> {
  const memberships = await getMyMemberships();
  if (memberships.length === 0) redirect("/");
  if (memberships.length === 1) return memberships[0];
  const match = memberships.find((m) => m.userId === requestedUserId);
  if (!match) redirect("/");
  return match;
}

export async function resolveCurrentUserId(requestedUserId?: string): Promise<string> {
  return (await resolveCurrentMembership(requestedUserId)).userId;
}
