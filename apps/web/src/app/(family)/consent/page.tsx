import { getConsentState } from "@/services/consent";
import { ConsentForm } from "@/features/consent/ConsentForm";
import { resolveCurrentMembership } from "@/services/me";
import { ApiError } from "@/services/errors";
import { FAMILY_ROLE_LABEL } from "@/types";
import type { ConsentState } from "@/types";

interface PageProps {
  searchParams: Promise<{ elder?: string }>;
}

/**
 * 가족 대리 동의 관리 화면(decisions.md #53 — 2026-09-12 사용자 결정: 가족 대리동의
 * 유효 인정). 성년후견 미개시 어르신이 판단력 저하 등으로 본인이 직접 동의하기 어려운
 * 경우, 가족 구성원이 대신 동의를 부여/철회할 수 있게 한다(백엔드는 이미
 * `POST /users/{userId}/consent-logs`의 `granted_by`로 이 경로를 지원하고 있었음 —
 * PR #6, 다만 이를 쓰는 화면이 지금까지 없었다).
 *
 * `resolveCurrentMembership`이 로그인 세션에서 "나 = 어느 family_member"를 바로
 * 알려주므로(`GET /me`), 예전처럼 어르신의 가족 목록에서 본인을 직접 골라야 했던
 * 단계가 없어졌다.
 */
export default async function ConsentPage({ searchParams }: PageProps) {
  const { elder } = await searchParams;
  const { userId, familyMemberId, role } = await resolveCurrentMembership(elder);

  let consentState: ConsentState | null = null;
  let error: string | null = null;
  try {
    consentState = await getConsentState(userId);
  } catch (e) {
    error = e instanceof ApiError ? e.message : "동의 상태를 불러오지 못했습니다.";
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

      {!error && consentState && (
        <>
          <p className="mt-8 text-body-compact text-ink">
            <span className="font-medium">{FAMILY_ROLE_LABEL[role]}</span> 자격으로
            로그인한 본인 명의의 대리 동의입니다.
          </p>
          <div className="mt-4">
            <ConsentForm userId={userId} actingFamilyMemberId={familyMemberId} initial={consentState} />
          </div>
        </>
      )}
    </main>
  );
}
