/** design.md §3.1 Chapter/ChapterRevision — schema.md `chapters`/`chapter_revisions` 매핑. */
export type ChapterPeriod = "childhood" | "youth" | "adulthood" | "present";
export type ChapterStatus = "draft" | "in_review" | "rejected" | "confirmed";
export type RevisionAction = "approved" | "rejected";

export interface Chapter {
  id: string;
  userId: string;
  chapterNo: number;
  title: string;
  period: ChapterPeriod;
  bodyText: string;
  status: ChapterStatus;
  version: number;
  createdAt: string;
  updatedAt: string;
}

export interface ChapterRevision {
  id: string;
  chapterId: string;
  version: number;
  bodyTextSnapshot: string;
  reviewerId?: string;
  reviewComment?: string;
  action: RevisionAction;
}

/** glossary.md 한글 표시명 — schema.md §7 매핑과 동일 값 유지 (SoR: schema.md). */
export const CHAPTER_PERIOD_LABEL: Record<ChapterPeriod, string> = {
  childhood: "유년기",
  youth: "청년기",
  adulthood: "중장년기",
  present: "현재",
};

export const CHAPTER_STATUS_LABEL: Record<ChapterStatus, string> = {
  draft: "초안",
  in_review: "감수중",
  rejected: "반려",
  confirmed: "확정",
};
