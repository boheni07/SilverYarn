"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { createInvitationAction } from "./actions";
import { FAMILY_ROLE_LABEL } from "@/types";
import type { FamilyRole } from "@/types";

const INVITABLE_ROLES: FamilyRole[] = ["family", "caregiver", "social_worker"];

const FAMILY_WEB_URL = process.env.NEXT_PUBLIC_FAMILY_WEB_URL ?? "http://localhost:3000";

/**
 * design.md §2.9 "가족 계정 웹 콘솔 초대" — 신규 온보딩된 어르신은 Device Token만
 * 있어 스스로 `POST /invitations`를 부를 수 없다(family 권한 없음). admin이 대신
 * 초대를 만들고, 결과 링크를 운영자가 가족에게 전달한다(문자/이메일 발송 자체는
 * 스코프 밖 — 지금은 화면에 표시된 링크를 운영자가 복사해 전달).
 */
export function InvitationForm({ userId }: { userId: string }) {
  const [role, setRole] = useState<FamilyRole>("family");
  const [contact, setContact] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inviteLink, setInviteLink] = useState<string | null>(null);

  async function handleSubmit() {
    if (!contact.trim()) return;
    setPending(true);
    setError(null);
    const result = await createInvitationAction({ userId, contact: contact.trim(), role });
    setPending(false);
    if (result.ok) {
      setInviteLink(`${FAMILY_WEB_URL}/invitations/${result.invitation.token}`);
      setContact("");
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="rounded-xl border border-border-soft bg-surface p-6 shadow-sm">
      <p className="text-body-compact font-medium text-ink">가족 구성원 초대</p>
      <p className="mt-1 text-caption text-ink-muted">
        연락처와 역할을 입력해 초대 링크를 만듭니다. 만든 링크는 운영자가 직접 전달합니다.
      </p>

      <label className="mt-4 block text-caption text-ink-muted">
        역할
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as FamilyRole)}
          className="mt-1 block min-h-11 w-full rounded-lg border border-border bg-paper px-3 text-body-compact text-ink"
        >
          {INVITABLE_ROLES.map((r) => (
            <option key={r} value={r}>
              {FAMILY_ROLE_LABEL[r]}
            </option>
          ))}
        </select>
      </label>

      <label className="mt-4 block text-caption text-ink-muted">
        연락처 (전화번호 또는 이메일)
        <input
          type="text"
          value={contact}
          onChange={(e) => setContact(e.target.value)}
          placeholder="예: 010-1234-5678"
          className="mt-1 block min-h-11 w-full rounded-lg border border-border bg-paper px-3 text-body-compact text-ink"
        />
      </label>

      {error && <p className="mt-3 text-caption text-ink">{error}</p>}

      <Button className="mt-4" onClick={handleSubmit} disabled={pending || !contact.trim()}>
        {pending ? "초대 생성 중…" : "초대 링크 만들기"}
      </Button>

      {inviteLink && (
        <div className="mt-4 rounded-lg border border-border bg-subtle-2 px-4 py-3">
          <p className="text-caption text-ink-muted">아래 링크를 가족에게 전달하세요.</p>
          <code className="mt-1 block break-all text-caption text-ink">{inviteLink}</code>
        </div>
      )}
    </div>
  );
}
