import { getNotificationSettings } from "@/services/notification-settings";
import { NotificationSettingsForm } from "@/features/notification-settings/NotificationSettingsForm";
import { resolveCurrentMembership } from "@/services/me";
import { ApiError } from "@/services/errors";
import type { NotificationSetting } from "@/types";

interface PageProps {
  searchParams: Promise<{ elder?: string }>;
}

/**
 * WF5 "알림·가족구성원 설정" — 가족·복지사가 **본인** 알림 수신 채널·항목을 켜고 끈다
 * (design.md §7.1 "본인 것만", 백엔드 `authorize_own_family_member` + 2FA).
 *
 * `resolveCurrentMembership()`(`GET /me`)이 로그인 세션 자신의 family_member_id를
 * 바로 알려주므로 목록·선택 단계 없이 곧장 본인 설정으로 들어간다.
 */
export default async function NotificationSettingsPage({ searchParams }: PageProps) {
  const { elder } = await searchParams;
  const { familyMemberId } = await resolveCurrentMembership(elder);

  let settings: NotificationSetting[] = [];
  let error: string | null = null;
  try {
    settings = await getNotificationSettings(familyMemberId);
  } catch (e) {
    error = e instanceof ApiError ? e.message : "알림 설정을 불러오지 못했습니다.";
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">알림 수신 설정</h1>
      <p className="mt-2 text-ink-muted">
        자서전 갱신·동기화 문제·정서 알림을 어떤 채널로 받을지 구성원별로 설정합니다.
      </p>

      {error && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">{error}</p>
      )}

      {!error && (
        <div className="mt-8">
          <NotificationSettingsForm familyMemberId={familyMemberId} initial={settings} />
        </div>
      )}
    </main>
  );
}
