"use server";

import { updateRetentionPolicy } from "@/services/retention-policies";
import { ApiError } from "@/services/errors";
import type { RetentionPolicy } from "@/types";

export type UpdateResult = { ok: true; policy: RetentionPolicy } | { ok: false; error: string };

export async function updateRetentionPolicyAction(
  category: string,
  retentionDays: number,
): Promise<UpdateResult> {
  try {
    const policy = await updateRetentionPolicy(category, retentionDays);
    return { ok: true, policy };
  } catch (e) {
    return { ok: false, error: e instanceof ApiError ? e.message : "보유기간 변경 중 오류가 발생했습니다." };
  }
}
