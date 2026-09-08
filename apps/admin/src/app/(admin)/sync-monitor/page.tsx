import Link from "next/link";
import { listDeviceSyncSessions } from "@/services/sync";
import { Card } from "@/components/ui/Card";
import { SyncStatusBadge } from "@/components/ui/SyncStatusBadge";
import { SYNC_DIRECTION_LABEL } from "@/types";
import { ApiError } from "@/services/errors";
import type { SyncSession } from "@/types";

interface SyncMonitorPageProps {
  searchParams: Promise<{ deviceId?: string }>;
}

/**
 * structure.md §5 "Wi-Fi 동기화 모니터링" 화면. GET /sync/sessions?device_id=...
 * (2026-09-08 신규 — apps/admin 스캐폴딩 중 추가, services/sync/api/v1/sync.py)를
 * 사용한다. "전체 기기 통합 모니터링"은 아직 없어 기기 하나씩만 조회한다.
 */
export default async function SyncMonitorPage({ searchParams }: SyncMonitorPageProps) {
  const { deviceId } = await searchParams;

  if (!deviceId) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-12">
        <p className="text-ink-muted">
          기기 ID가 필요합니다. <Link href="/" className="text-teal-deep underline">처음으로</Link>
        </p>
      </main>
    );
  }

  let sessions: SyncSession[];
  let error: string | null = null;
  try {
    sessions = await listDeviceSyncSessions(deviceId);
  } catch (e) {
    error = e instanceof ApiError ? e.message : "동기화 이력을 불러오지 못했습니다.";
    sessions = [];
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">Wi-Fi 동기화 모니터링</h1>
      <p className="mt-2 text-ink-muted">이 기기의 최근 동기화 이력입니다.</p>

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
    </main>
  );
}
