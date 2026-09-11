"use server";

import { createInvitation } from "@/services/invitations";
import { ApiError } from "@/services/errors";
import type { FamilyRole, Invitation } from "@/types";

// apps/admin의 첫 쓰기(Server Action) — 지금까지는 GET 전용이라 필요 없었다
// (design.md §7.4 "admin은 GET 전용이라 Server Action 없음"은 이 화면부터 갱신).
export type ActionResult = { ok: true; invitation: Invitation } | { ok: false; error: string };

export async function createInvitationAction(input: {
  userId: string;
  contact: string;
  role: FamilyRole;
}): Promise<ActionResult> {
  try {
    const invitation = await createInvitation(input);
    return { ok: true, invitation };
  } catch (e) {
    return { ok: false, error: e instanceof ApiError ? e.message : "초대 생성 중 오류가 발생했습니다." };
  }
}
