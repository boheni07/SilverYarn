import Link from "next/link";
import { listUserDevices } from "@/services/devices";
import { Card } from "@/components/ui/Card";
import { InstallModeBadge } from "@/components/ui/InstallModeBadge";
import { ApiError } from "@/services/errors";
import type { Device } from "@/types";

interface DevicesPageProps {
  searchParams: Promise<{ userId?: string }>;
}

/** structure.md §5 "기기 관리" 화면. GET /users/{userId}/devices만 있고 "전체 기기
 * 목록" 엔드포인트는 없어(services/backend README) 사용자 단위로만 조회한다. */
export default async function DevicesPage({ searchParams }: DevicesPageProps) {
  const { userId } = await searchParams;

  if (!userId) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-12">
        <p className="text-ink-muted">
          사용자 ID가 필요합니다. <Link href="/" className="text-teal-deep underline">처음으로</Link>
        </p>
      </main>
    );
  }

  let devices: Device[];
  let error: string | null = null;
  try {
    devices = await listUserDevices(userId);
  } catch (e) {
    error = e instanceof ApiError ? e.message : "기기 목록을 불러오지 못했습니다.";
    devices = [];
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">기기 관리</h1>
      <p className="mt-2 text-ink-muted">이 사용자에게 등록된 기기 목록입니다.</p>

      {error && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">
          {error}
        </p>
      )}

      {!error && devices.length === 0 && (
        <p className="mt-6 text-ink-muted">등록된 기기가 없습니다.</p>
      )}

      <ul className="mt-6 flex flex-col gap-4">
        {devices.map((device) => (
          <li key={device.id}>
            <Link href={`/sync-monitor?deviceId=${device.id}`}>
              <Card className="transition-shadow hover:shadow-md">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-caption text-ink-muted">
                      {device.displayId}
                      {device.modelName ? ` · ${device.modelName}` : ""}
                    </p>
                    <h2 className="font-editorial text-h2 font-semibold text-ink">
                      RAM {device.ramGb}GB · Android {device.androidVersion}
                    </h2>
                    <p className="mt-1 text-caption text-ink-muted">
                      마지막 동기화:{" "}
                      {device.lastSyncAt
                        ? new Date(device.lastSyncAt).toLocaleString("ko-KR")
                        : "기록 없음"}
                    </p>
                  </div>
                  <InstallModeBadge mode={device.installMode} />
                </div>
              </Card>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
