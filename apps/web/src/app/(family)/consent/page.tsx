import Link from "next/link";
import { listFamilyMembers } from "@/services/family-members";
import { getConsentState } from "@/services/consent";
import { ConsentForm } from "@/features/consent/ConsentForm";
import { ApiError } from "@/services/errors";
import type { ConsentState, FamilyMember } from "@/types";

interface PageProps {
  searchParams: Promise<{ userId?: string; familyMemberId?: string }>;
}

/**
 * 가족 대리 동의 관리 화면(decisions.md #53 — 2026-09-12 사용자 결정: 가족 대리동의
 * 유효 인정). 성년후견 미개시 어르신이 판단력 저하 등으로 본인이 직접 동의하기 어려운
 * 경우, 가족 구성원이 대신 동의를 부여/철회할 수 있게 한다(백엔드는 이미
 * `POST /users/{userId}/consent-logs`의 `granted_by`로 이 경로를 지원하고 있었음 —
 * PR #6, 다만 이를 쓰는 화면이 지금까지 없었다).
 *
 * ⚠️ notification-settings와 동일한 임시 상태 — 실 인증(Keycloak) 세션이 아직
 * "로그인한 나 = 어느 family_member"를 자동 해석하지 않아 구성원을 먼저 선택하게 한다.
 */
export default async function ConsentPage({ searchParams }: PageProps) {
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

  let consentState: ConsentState | null = null;
  if (selected) {
    try {
      consentState = await getConsentState(userId);
    } catch (e) {
      error = e instanceof ApiError ? e.message : "동의 상태를 불러오지 못했습니다.";
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">대리 동의 관리</h1>
      <p className="mt-2 text-ink-muted">
        어르신이 직접 동의하기 어려운 경우 가족이 대신 동의를 관리합니다. 어르신 본인의
        동의 이력과는 별도로 기록됩니다.
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
          <h2 className="mt-8 font-editorial text-h2 font-semibold text-ink">
            대리 동의를 남길 구성원 선택
          </h2>
          <ul className="mt-4 flex flex-col gap-2">
            {members.map((m) => (
              <li key={m.id}>
                <Link
                  href={`/consent?userId=${encodeURIComponent(userId)}&familyMemberId=${m.id}`}
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

      {!error && selected && consentState && (
        <>
          <p className="mt-8 text-body-compact text-ink">
            <span className="font-medium">{selected.name}</span>
            <span className="text-ink-muted"> ({selected.role})</span> 님 명의로 대리 동의
            {" · "}
            <Link
              href={`/consent?userId=${encodeURIComponent(userId)}`}
              className="text-teal-deep underline"
            >
              구성원 바꾸기
            </Link>
          </p>
          <div className="mt-4">
            <ConsentForm userId={userId} actingFamilyMemberId={selected.id} initial={consentState} />
          </div>
        </>
      )}
    </main>
  );
}
