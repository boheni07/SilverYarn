import Link from "next/link";
import { getChapter } from "@/services/chapters";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { CHAPTER_PERIOD_LABEL } from "@/types";
import { ApiError } from "@/services/errors";

interface ChapterDetailPageProps {
  params: Promise<{ chapterId: string }>;
  searchParams: Promise<{ userId?: string }>;
}

export default async function ChapterDetailPage({ params, searchParams }: ChapterDetailPageProps) {
  const { chapterId } = await params;
  const { userId } = await searchParams;

  let chapter;
  try {
    chapter = await getChapter(chapterId);
  } catch (e) {
    const message = e instanceof ApiError ? e.message : "챕터를 불러오지 못했습니다.";
    return (
      <main className="mx-auto max-w-2xl px-4 py-12">
        <p className="text-ink-muted">{message}</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-12">
      <Link href={`/chapters?userId=${userId ?? ""}`} className="text-teal-deep underline">
        ← 목록으로
      </Link>

      <div className="mt-4 flex items-center gap-3">
        <p className="text-caption text-ink-muted">
          {CHAPTER_PERIOD_LABEL[chapter.period]} · {chapter.chapterNo}장
        </p>
        <StatusBadge status={chapter.status} />
      </div>
      <h1 className="mt-2 font-editorial text-display font-bold text-ink">{chapter.title}</h1>

      <article className="mt-8 whitespace-pre-wrap font-editorial text-body leading-relaxed text-ink">
        {chapter.bodyText}
      </article>
    </main>
  );
}
