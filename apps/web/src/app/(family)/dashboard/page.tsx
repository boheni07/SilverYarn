import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { getUser } from "@/services/users";
import { listChapters } from "@/services/chapters";
import { countConversationChunksSince } from "@/services/conversation-chunks";
import { ApiError } from "@/services/errors";
import type { Chapter } from "@/types";

interface DashboardPageProps {
  searchParams: Promise<{ userId?: string }>;
}

/** KST(UTC+9) 기준 "오늘" 자정의 UTC 시각 — 이 플랫폼은 국내 서비스라 서버 로케일
 * 대신 KST를 고정으로 쓴다(다국가 대응은 스코프 아웃, decisions.md 채널 항목 참조). */
function startOfTodayKst(): Date {
  const kstNow = new Date(Date.now() + 9 * 60 * 60 * 1000);
  return new Date(
    Date.UTC(kstNow.getUTCFullYear(), kstNow.getUTCMonth(), kstNow.getUTCDate(), -9, 0, 0),
  );
}

/** "주요 회고 카드"(WF1 요소 3) — 요약이 있는 챕터 중 가장 최근에 갱신된 것. */
function pickHighlightChapter(chapters: Chapter[]): Chapter | null {
  const withSummary = chapters.filter((c) => c.compactionSummary);
  if (withSummary.length === 0) return null;
  return withSummary.reduce((latest, c) =>
    new Date(c.updatedAt) > new Date(latest.updatedAt) ? c : latest,
  );
}

/**
 * WF1 "가족 대시보드 · 오늘의 기억 리포트" — 가족이 로그인 후 가장 먼저 보는 화면
 * (Plan/은빛실타래_UIUX_화면설계서.html WF1).
 *
 * ⚠️ "정서 상태"·"정서 추이 차트"(WF1 요소 2·4의 정서 항목)는 렌더하지 않는다 —
 * 정서 모니터링 파이프라인은 Phase 1 피처플래그로 OFF(decisions.md #25, CLAUDE.md).
 * 있지도 않은 정서 점수를 보여주는 대신 그 사실을 그대로 안내한다.
 */
export default async function DashboardPage({ searchParams }: DashboardPageProps) {
  const { userId } = await searchParams;

  if (!userId) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-12">
        <p className="text-ink-muted">
          어르신 계정 ID가 필요합니다.{" "}
          <Link href="/" className="text-teal-deep underline">
            처음으로
          </Link>
        </p>
      </main>
    );
  }

  const since = startOfTodayKst();
  let elderName = "어르신";
  let chapters: Chapter[] = [];
  let conversationCountToday = 0;
  let error: string | null = null;
  try {
    const [user, chapterList, count] = await Promise.all([
      getUser(userId),
      listChapters(userId),
      countConversationChunksSince(userId, since),
    ]);
    elderName = user.name;
    chapters = chapterList;
    conversationCountToday = count;
  } catch (e) {
    error = e instanceof ApiError ? e.message : "데이터를 불러오지 못했습니다.";
  }

  const newChapterCountToday = chapters.filter((c) => new Date(c.updatedAt) >= since).length;
  const highlight = pickHighlightChapter(chapters);

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">
        {elderName}님의 오늘 기억 리포트
      </h1>
      <p className="mt-2 text-body-compact text-ink-muted">
        어르신의 오늘 대화와 새로 발굴된 회고를 확인합니다. (workflow-diagrams.md §4.3)
      </p>

      {error && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">
          {error}
        </p>
      )}

      {!error && (
        <>
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Card className="text-center">
              <p className="text-h1 font-bold text-teal-deep">{conversationCountToday}회</p>
              <p className="mt-1 text-caption text-ink-muted">오늘 대화</p>
            </Card>
            <Card className="text-center">
              <p className="text-h1 font-bold text-teal-deep">{newChapterCountToday}건</p>
              <p className="mt-1 text-caption text-ink-muted">오늘 새 회고</p>
            </Card>
            <Card className="text-center">
              <p className="text-h2 font-semibold text-ink-faint">준비 중</p>
              <p className="mt-1 text-caption text-ink-muted">정서 상태</p>
            </Card>
          </div>

          <h2 className="mt-10 font-editorial text-h2 font-semibold text-ink">주요 회고</h2>
          {highlight ? (
            <Card className="mt-4">
              <div className="flex items-start justify-between gap-4">
                <p className="text-body-compact font-medium text-ink">{highlight.title}</p>
                <span className="shrink-0 rounded-full bg-gold-tint px-3 py-1 text-caption font-medium text-gold-deep">
                  AI 요약
                </span>
              </div>
              <p className="mt-3 text-body-compact text-ink-muted">{highlight.compactionSummary}</p>
              {!!highlight.compactionKeywords?.length && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {highlight.compactionKeywords.map((kw) => (
                    <span
                      key={kw}
                      className="rounded-full bg-subtle px-3 py-1 text-caption text-ink-muted"
                    >
                      #{kw}
                    </span>
                  ))}
                </div>
              )}
              <Link
                href={`/chapters/${highlight.id}?userId=${encodeURIComponent(userId)}`}
                className="mt-4 inline-block text-caption text-teal-deep underline"
              >
                전체 내용 보기
              </Link>
            </Card>
          ) : (
            <p className="mt-4 text-ink-muted">
              아직 요약된 회고가 없습니다. 어르신의 다음 Wi-Fi 동기화 후 다시 확인해 주세요.
            </p>
          )}

          <h2 className="mt-10 font-editorial text-h2 font-semibold text-ink">정서 모니터링</h2>
          <p className="mt-4 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-caption text-ink-muted">
            정서 모니터링 알림의 법적·윤리적 기준이 아직 확정되지 않아 이 파이프라인은
            꺼져 있습니다(decisions.md #25). 법무 검토가 끝나면 이 자리에 정서 추이 차트가
            표시됩니다.
          </p>

          <p className="mt-10">
            <Link
              href={`/review?userId=${encodeURIComponent(userId)}`}
              className="text-body-compact text-teal-deep underline"
            >
              원고 감수 화면으로 이동
            </Link>
          </p>
        </>
      )}
    </main>
  );
}
