import Link from "next/link";
import { listChapters } from "@/services/chapters";
import { listFamilyMembers } from "@/services/family-members";
import { ChapterReviewPanel } from "@/features/chapter-review/ChapterReviewPanel";
import { ApiError } from "@/services/errors";
import type { Chapter, FamilyMember } from "@/types";

interface ReviewPageProps {
  searchParams: Promise<{ userId?: string }>;
}

export default async function ReviewPage({ searchParams }: ReviewPageProps) {
  const { userId } = await searchParams;

  if (!userId) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-12">
        <p className="text-ink-muted">
          어르신 계정 ID가 필요합니다. <Link href="/" className="text-teal-deep underline">처음으로</Link>
        </p>
      </main>
    );
  }

  let chapters: Chapter[];
  let reviewers: FamilyMember[];
  let error: string | null = null;
  try {
    [chapters, reviewers] = await Promise.all([listChapters(userId), listFamilyMembers(userId)]);
  } catch (e) {
    error = e instanceof ApiError ? e.message : "데이터를 불러오지 못했습니다.";
    chapters = [];
    reviewers = [];
  }

  // schema.md #status 주석: rejected는 draft와 별개 상태(v1.1, WF2 "수정 요청" 반려 루프).
  // 반려된 챕터를 여기서 빼면 가족이 반려 사실 자체를 다시 볼 수 없게 되므로 계속 노출한다
  // (실제 UI 클릭 e2e 검증 중 발견 — 초기엔 draft/in_review만 필터링해 반려 후 챕터가
  // 감수 목록에서 사라지는 버그가 있었다).
  const pending = chapters.filter(
    (c) => c.status === "draft" || c.status === "in_review" || c.status === "rejected",
  );

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">원고 감수</h1>
      <p className="mt-2 text-ink-muted">
        승인하면 챕터가 확정되고, 반려하면 반려 상태로 표시됩니다 — 재작성은 작가 엔진이
        코멘트를 반영해 처리합니다. (workflow-diagrams.md §7)
      </p>

      {error && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">
          {error}
        </p>
      )}

      {!error && reviewers.length === 0 && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">
          이 어르신 계정에 등록된 가족/복지사가 없습니다. 초대(invitations) 흐름으로
          먼저 등록해 주세요.
        </p>
      )}

      {!error && pending.length === 0 && (
        <p className="mt-6 text-ink-muted">감수 대기 중인 챕터가 없습니다.</p>
      )}

      <div className="mt-6 flex flex-col gap-6">
        {pending.map((chapter) => (
          <ChapterReviewPanel key={chapter.id} chapter={chapter} reviewers={reviewers} />
        ))}
      </div>
    </main>
  );
}
