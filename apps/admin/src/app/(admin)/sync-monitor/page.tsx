import Link from "next/link";
import { listSyncSessions } from "@/services/sync";
import { Card } from "@/components/ui/Card";
import { SyncStatusBadge } from "@/components/ui/SyncStatusBadge";
import { SYNC_DIRECTION_LABEL, SYNC_STATUS_LABEL } from "@/types";
import { ApiError } from "@/services/errors";
import type { SyncSession, SyncStatus } from "@/types";

const PAGE_SIZE = 20;
const STATUS_FILTERS: SyncStatus[] = ["success", "failed", "retrying"];

interface SyncMonitorPageProps {
  searchParams: Promise<{ deviceId?: string; status?: string; page?: string }>;
}

/**
 * structure.md §5 "Wi-Fi 동기화 모니터링" 화면 — GET /sync/sessions(2026-09-08 신규,
 * 이후 페이지네이션+"전체 기기 통합 모니터링"으로 확장)의 한 화면. `deviceId`가 있으면
 * devices 화면에서 들어온 기기 하나의 이력(기존 동작), 없으면 전체 기기를 아우르는
 * 통합 모니터링이 된다 — 백엔드는 같은 엔드포인트다.
 */
export default async function SyncMonitorPage({ searchParams }: SyncMonitorPageProps) {
  const { deviceId, status: statusParam, page: pageParam } = await searchParams;
  const page = Math.max(1, Number(pageParam ?? "1") || 1);
  const status = STATUS_FILTERS.includes(statusParam as SyncStatus) ? (statusParam as SyncStatus) : undefined;

  let sessions: SyncSession[] = [];
  let total = 0;
  let error: string | null = null;
  try {
    const result = await listSyncSessions({ page, pageSize: PAGE_SIZE, deviceId, status });
    sessions = result.sessions;
    total = result.pagination.total;
  } catch (e) {
    error = e instanceof ApiError ? e.message : "동기화 이력을 불러오지 못했습니다.";
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function filterHref(nextStatus?: SyncStatus) {
    const query = new URLSearchParams();
    if (deviceId) query.set("deviceId", deviceId);
    if (nextStatus) query.set("status", nextStatus);
    const qs = query.toString();
    return qs ? `/sync-monitor?${qs}` : "/sync-monitor";
  }

  function pageHref(nextPage: number) {
    const query = new URLSearchParams();
    if (deviceId) query.set("deviceId", deviceId);
    if (status) query.set("status", status);
    query.set("page", String(nextPage));
    return `/sync-monitor?${query}`;
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">
        {deviceId ? "Wi-Fi 동기화 모니터링" : "전체 기기 통합 모니터링"}
      </h1>
      <p className="mt-2 text-ink-muted">
        {deviceId
          ? "이 기기의 최근 동기화 이력입니다."
          : `모든 기기의 동기화 이력입니다 — 전체 ${total}건.`}
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        <Link
          href={filterHref(undefined)}
          className={`rounded-full px-3 py-1 text-caption font-medium ${
            !status ? "bg-teal-deep text-white" : "bg-subtle text-ink-muted"
          }`}
        >
          전체
        </Link>
        {STATUS_FILTERS.map((s) => (
          <Link
            key={s}
            href={filterHref(s)}
            className={`rounded-full px-3 py-1 text-caption font-medium ${
              status === s ? "bg-teal-deep text-white" : "bg-subtle text-ink-muted"
            }`}
          >
            {SYNC_STATUS_LABEL[s]}
          </Link>
        ))}
      </div>

      {deviceId && (
        <p className="mt-4 text-caption text-ink-muted">
          <Link href={filterHref(status)} className="text-teal-deep underline">
            전체 기기 통합 모니터링으로 보기
          </Link>
        </p>
      )}

      {error && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">
          {error}
        </p>
      )}

      {!error && sessions.length === 0 && (
        <p className="mt-6 text-ink-muted">동기화 이력이 없습니다.</p>
      )}

      <ul className="mt-6 flex flex-col gap-4">
        {sessions.map((session) => (
          <li key={session.id}>
            <Card>
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-caption text-ink-muted">
                    {SYNC_DIRECTION_LABEL[session.direction]} · 재시도 {session.retryCount}회
                    {!deviceId && (
                      <>
                        {" · "}
                        <Link href={`/sync-monitor?deviceId=${session.deviceId}`} className="underline">
                          기기 {session.deviceId.slice(0, 8)}
                        </Link>
                      </>
                    )}
                  </p>
                  <h2 className="font-editorial text-h2 font-semibold text-ink">
                    {new Date(session.startedAt).toLocaleString("ko-KR")}
                  </h2>
                  <p className="mt-1 text-caption text-ink-muted">
                    {session.finishedAt
                      ? `종료: ${new Date(session.finishedAt).toLocaleString("ko-KR")}`
                      : "진행 중 / 결과 대기"}
                  </p>
                </div>
                <SyncStatusBadge status={session.status} />
              </div>
            </Card>
          </li>
        ))}
      </ul>

      {!error && totalPages > 1 && (
        <nav className="mt-8 flex items-center justify-center gap-4">
          {page > 1 ? (
            <Link href={pageHref(page - 1)} className="text-body-compact text-teal-deep underline">
              이전
            </Link>
          ) : (
            <span className="text-body-compact text-ink-faint">이전</span>
          )}
          <span className="text-caption text-ink-muted">
            {page} / {totalPages}
          </span>
          {page < totalPages ? (
            <Link href={pageHref(page + 1)} className="text-body-compact text-teal-deep underline">
              다음
            </Link>
          ) : (
            <span className="text-body-compact text-ink-faint">다음</span>
          )}
        </nav>
      )}
    </main>
  );
}
