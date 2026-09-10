import Link from "next/link";
import { listFamilyMembers } from "@/services/family-members";
import { getNotificationSettings } from "@/services/notification-settings";
import { NotificationSettingsForm } from "@/features/notification-settings/NotificationSettingsForm";
import { ApiError } from "@/services/errors";
import type { FamilyMember, NotificationSetting } from "@/types";

interface PageProps {
  searchParams: Promise<{ userId?: string; familyMemberId?: string }>;
}

/**
 * WF5 "알림·가족구성원 설정" — 가족·복지사가 **본인** 알림 수신 채널·항목을 켜고 끈다
 * (design.md §7.1 "본인 것만", 백엔드 `authorize_own_family_member` + 2FA).
 *
 * ⚠️ 실 인증(Keycloak) 연동 전이라 "본인"을 토큰에서 못 얻는다 — 임시로 어르신 계정의
 * 가족 목록에서 구성원을 골라(`?familyMemberId=`) 그 사람의 설정을 편집한다. 실 인증이
 * 붙으면 목록·선택 단계 없이 로그인한 본인 설정으로 바로 들어간다.
 */
export default async function NotificationSettingsPage({ searchParams }: PageProps) {
  const { userId, familyMemberId } = await searchParams;

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

  let members: FamilyMember[];
  let error: string | null = null;
  try {
    members = await listFamilyMembers(userId);
  } catch (e) {
    error = e instanceof ApiError ? e.message : "가족 구성원을 불러오지 못했습니다.";
    members = [];
  }

  const selected = members.find((m) => m.id === familyMemberId) ?? null;

  let settings: NotificationSetting[] = [];
  if (selected) {
    try {
      settings = await getNotificationSettings(selected.id);
    } catch (e) {
      error = e instanceof ApiError ? e.message : "알림 설정을 불러오지 못했습니다.";
    }
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

      {!error && members.length === 0 && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">
          이 어르신 계정에 등록된 가족/복지사가 없습니다. 초대(invitations) 흐름으로 먼저 등록해 주세요.
        </p>
      )}

      {!error && members.length > 0 && !selected && (
        <>
          <h2 className="mt-8 font-editorial text-h2 font-semibold text-ink">구성원 선택</h2>
          <ul className="mt-4 flex flex-col gap-2">
            {members.map((m) => (
              <li key={m.id}>
                <Link
                  href={`/notification-settings?userId=${encodeURIComponent(userId)}&familyMemberId=${m.id}`}
                  className="flex min-h-11 items-center justify-between rounded-lg border border-border-soft bg-surface px-4 hover:bg-subtle-2"
                >
                  <span className="text-ink">{m.name}</span>
                  <span className="text-caption text-ink-muted">{m.role}</span>
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}

      {!error && selected && (
        <>
          <p className="mt-8 text-body-compact text-ink">
            <span className="font-medium">{selected.name}</span>
            <span className="text-ink-muted"> ({selected.role})</span> 님의 설정
            {" · "}
            <Link
              href={`/notification-settings?userId=${encodeURIComponent(userId)}`}
              className="text-teal-deep underline"
            >
              구성원 바꾸기
            </Link>
          </p>
          <div className="mt-4">
            <NotificationSettingsForm familyMemberId={selected.id} initial={settings} />
          </div>
        </>
      )}
    </main>
  );
}
