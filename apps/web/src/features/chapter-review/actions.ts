"use server";

import { reviewChapter } from "@/services/chapters";
import { ApiError } from "@/services/errors";
import type { RevisionAction } from "@/types";

export type ActionResult = { ok: true } | { ok: false; error: string };

/** workflow-diagrams.md §7 — 승인/반려. 클라이언트 컴포넌트(ChapterReviewPanel)가 호출하는
 * Server Action. 백엔드 호출은 서버에서 일어나 세션 토큰(auth())이 자동으로 실린다. */
export async function submitReview(
  chapterId: string,
  input: { action: RevisionAction; reviewComment?: string; reviewerId?: string },
): Promise<ActionResult> {
  try {
    await reviewChapter(chapterId, input);
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof ApiError ? e.message : "감수 처리 중 오류가 발생했습니다." };
  }
}
