import Link from "next/link";
import { listChapters } from "@/services/chapters";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { CHAPTER_PERIOD_LABEL } from "@/types";
import type { Chapter } from "@/types";
import { ApiError } from "@/services/errors";

interface ChaptersPageProps {
  searchParams: Promise<{ userId?: string }>;
}

export default async function ChaptersPage({ searchParams }: ChaptersPageProps) {
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
  let error: string | null = null;
  try {
    chapters = await listChapters(userId);
  } catch (e) {
    error = e instanceof ApiError ? e.message : "챕터 목록을 불러오지 못했습니다.";
    chapters = [];
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">나의 자서전</h1>
      <p className="mt-2 text-ink-muted">유년기부터 현재까지, 지금까지 정리된 이야기입니다.</p>

      {error && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">
          {error}
        </p>
      )}

      {!error && chapters.length === 0 && (
        <p className="mt-6 text-ink-muted">아직 정리된 챕터가 없습니다. 대화를 이어가 보세요.</p>
      )}

      <ul className="mt-6 flex flex-col gap-4">
        {chapters.map((chapter) => (
          <li key={chapter.id}>
            <Link href={`/chapters/${chapter.id}?userId=${userId}`}>
              <Card className="transition-shadow hover:shadow-md">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-caption text-ink-muted">
                      {CHAPTER_PERIOD_LABEL[chapter.period]} · {chapter.chapterNo}장
                    </p>
                    <h2 className="font-editorial text-h2 font-semibold text-ink">{chapter.title}</h2>
                  </div>
                  <StatusBadge status={chapter.status} />
                </div>
              </Card>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
