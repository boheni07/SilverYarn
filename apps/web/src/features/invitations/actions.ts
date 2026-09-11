"use server";

import { acceptInvitation } from "@/services/invitations";
import { ApiError } from "@/services/errors";

export type ActionResult = { ok: true } | { ok: false; error: string };

/** design.md §2.9 초대 수락 — 로그인한 본인 이름으로 family_members 행이 만들어진다. */
export async function acceptInvitationAction(token: string, name: string): Promise<ActionResult> {
  try {
    await acceptInvitation(token, name);
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof ApiError ? e.message : "초대 수락 중 오류가 발생했습니다." };
  }
}
