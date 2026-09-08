import type { ChapterStatus } from "@/types";
import { CHAPTER_STATUS_LABEL } from "@/types";

/**
 * 색상은 전부 장식 전용 토큰(gold/silver)이거나 대비가 검증된 teal-deep만 쓴다
 * (design-tokens.md §1.1 — gold/silver는 텍스트 대비 미달이라 배지 "배경"에만 허용).
 */
const STATUS_CLASSES: Record<ChapterStatus, string> = {
  draft: "bg-subtle text-ink-muted",
  in_review: "bg-gold-tint text-ink",
  rejected: "bg-subtle text-ink-muted",
  confirmed: "bg-teal-tint text-teal-deep",
};

export function StatusBadge({ status }: { status: ChapterStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-caption font-medium ${STATUS_CLASSES[status]}`}
    >
      {CHAPTER_STATUS_LABEL[status]}
    </span>
  );
}
