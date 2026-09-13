"use server";

import { eraseUser } from "@/services/users";
import { ApiError } from "@/services/errors";

export type EraseResult = { ok: true } | { ok: false; error: string };

export async function eraseUserAction(userId: string, reason: string): Promise<EraseResult> {
  try {
    await eraseUser(userId, reason);
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof ApiError ? e.message : "계정 삭제 중 오류가 발생했습니다." };
  }
}
