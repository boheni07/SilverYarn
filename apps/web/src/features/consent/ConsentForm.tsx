"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { submitConsent } from "./actions";
import { CONSENT_TYPES, CONSENT_TYPE_LABEL } from "@/types";
import type { ConsentState, ConsentType } from "@/types";

/**
 * 가족 대리 동의 관리 화면(decisions.md #53, 2026-09-12 사용자 결정) — 어르신 본인이
 * 판단력 저하 등으로 직접 동의하기 어려운 경우, 선택한 가족 구성원 명의로 동의를
 * 부여/철회한다. 백엔드가 `grantedBy`를 호출자 본인 구성원 id로 검증하므로(consent_logs.py),
 * 여기서 넘기는 `actingFamilyMemberId`는 반드시 로그인 세션이 그 사람임을 전제한다.
 *
 * ⚠️ apps/web이 아직 세션→family_member를 자동 해석하지 않아(notification-settings와
 * 동일한 임시 상태) 페이지에서 구성원을 먼저 고르게 한다 — 실 인증이 화면별로
 * "로그인한 나"를 직접 알려주게 되면 이 선택 단계는 제거한다.
 */
export function ConsentForm({
  userId,
  actingFamilyMemberId,
  initial,
}: {
  userId: string;
  actingFamilyMemberId: string;
  initial: ConsentState;
}) {
  const router = useRouter();
  const [state, setState] = useState<Record<ConsentType, boolean>>(() => normalize(initial));
  const [pending, setPending] = useState<ConsentType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  async function toggle(consentType: ConsentType) {
    const next = !state[consentType];
    setPending(consentType);
    setError(null);
    const result = await submitConsent(userId, consentType, next, actingFamilyMemberId);
    setPending(null);
    if (result.ok) {
      setState((prev) => ({ ...prev, [consentType]: next }));
      setSavedAt(new Date().toLocaleTimeString("ko-KR"));
      router.refresh();
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="rounded-xl border border-border-soft bg-surface p-6 shadow-sm">
      <ul className="flex flex-col divide-y divide-border-soft">
        {CONSENT_TYPES.map((type) => (
          <li key={type} className="flex items-center justify-between gap-4 py-4 first:pt-0 last:pb-0">
            <span className="text-body-compact text-ink">{CONSENT_TYPE_LABEL[type]}</span>
            <label className="flex items-center gap-2">
              <span className="text-caption text-ink-muted">{state[type] ? "동의함" : "동의 안 함"}</span>
              <input
                type="checkbox"
                aria-label={`${CONSENT_TYPE_LABEL[type]} 대리 동의`}
                checked={state[type]}
                disabled={pending === type}
                onChange={() => toggle(type)}
                className="h-5 w-5 accent-teal-deep"
              />
            </label>
          </li>
        ))}
      </ul>

      <p className="mt-4 text-caption text-ink-muted">
        여기서 켜고 끄는 동의는 이 가족 구성원 명의의 대리 동의(proxy)로 기록됩니다 —
        어르신 본인이 기기에서 직접 한 동의(self)와 별개의 이력으로 남습니다.
      </p>

      {error && <p className="mt-3 text-caption text-ink">{error}</p>}
      {savedAt && <p className="mt-3 text-caption text-ink-muted">저장됨 ({savedAt})</p>}
    </div>
  );
}

/** 기록이 없는 유형은 미동의(false)로 채운다(백엔드 `current_state` 문서 참조). */
function normalize(state: ConsentState): Record<ConsentType, boolean> {
  return Object.fromEntries(CONSENT_TYPES.map((t) => [t, state[t] ?? false])) as Record<
    ConsentType,
    boolean
  >;
}
