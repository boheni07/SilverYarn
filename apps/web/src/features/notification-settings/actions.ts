"use server";

import { replaceNotificationSettings } from "@/services/notification-settings";
import { ApiError } from "@/services/errors";
import type { ChannelPreference } from "@/types";

export type ActionResult = { ok: true } | { ok: false; error: string };

/** design.md §4.2 PUT /family-members/{id}/notification-settings — WF5, 전체 교체. */
export async function saveNotificationSettings(
  familyMemberId: string,
  settings: ChannelPreference[],
): Promise<ActionResult> {
  try {
    await replaceNotificationSettings(familyMemberId, settings);
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof ApiError ? e.message : "저장 중 오류가 발생했습니다." };
  }
}
