"use server";

import { requestPublication } from "@/services/publications";
import { ApiError } from "@/services/errors";
import type { PublicationFormat } from "@/types";

export type ActionResult = { ok: true } | { ok: false; error: string };

/** design.md §4.2/§2.6 POST /users/{userId}/publications — 출판 요청. 전체 챕터가
 * confirmed가 아니면 서버가 VALIDATION_ERROR로 거부한다(erasure 급 파괴적 동작이
 * 아니라 되돌릴 수 있는 요청이라 별도 확인 UI는 두지 않음, danger-zone 패턴 불필요). */
export async function submitPublicationRequest(userId: string, format: PublicationFormat): Promise<ActionResult> {
  try {
    await requestPublication(userId, format);
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof ApiError ? e.message : "출판 요청 중 오류가 발생했습니다." };
  }
}
