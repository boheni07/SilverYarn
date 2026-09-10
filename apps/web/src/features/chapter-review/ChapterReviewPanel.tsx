"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { submitReview } from "./actions";
import { CHAPTER_PERIOD_LABEL } from "@/types";
import type { Chapter, FamilyMember } from "@/types";

/**
 * workflow-diagrams.md §7 가족 협업·감수 워크플로우의 웹 화면 구현.
 * 승인/반려 둘 다 이 한 컴포넌트에서 처리 — chapter_revisions 생성은 서버(M-5 정정)
 * 책임이라 여기서는 액션과 사유만 모아 POST할 뿐이다.
 */
export function ChapterReviewPanel({
  chapter,
  reviewers,
}: {
  chapter: Chapter;
  reviewers: FamilyMember[];
}) {
  const router = useRouter();
  const [comment, setComment] = useState("");
  const [reviewerId, setReviewerId] = useState(reviewers[0]?.id ?? "");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleReview(action: "approved" | "rejected") {
    setPending(true);
    setError(null);
    const result = await submitReview(chapter.id, {
      action,
      reviewComment: comment.trim() || undefined,
      reviewerId: reviewerId || undefined,
    });
    setPending(false);
    if (result.ok) router.refresh();
    else setError(result.error);
  }

  return (
    <div className="rounded-xl border border-border-soft bg-surface p-6 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-caption text-ink-muted">
            {CHAPTER_PERIOD_LABEL[chapter.period]} · {chapter.chapterNo}장 · v{chapter.version}
          </p>
          <h2 className="font-editorial text-h2 font-semibold text-ink">{chapter.title}</h2>
        </div>
        <StatusBadge status={chapter.status} />
      </div>

      <p className="mt-4 whitespace-pre-wrap text-body-compact leading-relaxed text-ink">
        {chapter.bodyText}
      </p>

      {reviewers.length > 0 && (
        <label className="mt-4 block text-caption text-ink-muted">
          감수자
          <select
            value={reviewerId}
            onChange={(e) => setReviewerId(e.target.value)}
            className="mt-1 block min-h-11 w-full rounded-lg border border-border bg-paper px-3 text-body-compact text-ink"
          >
            {reviewers.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name} ({r.role})
              </option>
            ))}
          </select>
        </label>
      )}

      <label className="mt-4 block text-caption text-ink-muted">
        코멘트 (선택)
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={2}
          className="mt-1 block w-full rounded-lg border border-border bg-paper px-3 py-2 text-body-compact text-ink"
        />
      </label>

      {error && <p className="mt-3 text-caption text-ink">{error}</p>}

      <div className="mt-4 flex gap-3">
        <Button onClick={() => handleReview("approved")} disabled={pending}>
          승인
        </Button>
        <Button variant="danger" onClick={() => handleReview("rejected")} disabled={pending}>
          반려
        </Button>
      </div>
    </div>
  );
}
