"use server";

import { createPhotoRequest, dismissPhotoRequest } from "@/services/photo-requests";
import { ApiError } from "@/services/errors";

export type ActionResult = { ok: true } | { ok: false; error: string };

/** design.md §4.2 POST /photo-requests — 가족→당사자 사진 추가 요청(WU3→WF3). */
export async function submitPhotoRequest(input: {
  userId: string;
  requestedBy?: string;
  message?: string;
}): Promise<ActionResult> {
  try {
    await createPhotoRequest(input);
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof ApiError ? e.message : "요청 생성 중 오류가 발생했습니다." };
  }
}

/** 당사자가 "지금은 어렵다"며 대기 중인 요청을 닫는다 — pending 상태에서만 가능. */
export async function dismissRequest(requestId: string): Promise<ActionResult> {
  try {
    await dismissPhotoRequest(requestId);
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof ApiError ? e.message : "요청을 닫는 중 오류가 발생했습니다." };
  }
}
