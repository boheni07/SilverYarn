"use server";

import { recordConsent } from "@/services/consent";
import { ApiError } from "@/services/errors";
import type { ConsentLog, ConsentType } from "@/types";

export type ActionResult = { ok: true; log: ConsentLog } | { ok: false; error: string };

/**
 * design.md §4.2 POST /users/{userId}/consent-logs — 동의 부여/철회 1건 기록.
 * `grantedBy`가 있으면 대리 동의(proxy, decisions.md #53)로 남는다.
 */
export async function submitConsent(
  userId: string,
  consentType: ConsentType,
  granted: boolean,
  grantedBy?: string,
): Promise<ActionResult> {
  try {
    const log = await recordConsent(userId, { consentType, granted, grantedBy });
    return { ok: true, log };
  } catch (e) {
    return { ok: false, error: e instanceof ApiError ? e.message : "저장 중 오류가 발생했습니다." };
  }
}
