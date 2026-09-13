"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { assignUserOrganizationAction } from "./actions";
import type { Organization } from "@/types";

/** decisions.md #59(I2) — 어르신을 B2G 시설에 배정/해제. 배정된 시설은
 * `auth_deps.authorize_elder_data_read`의 테넌시 안전망 기준이 된다. */
export function AssignUserOrganizationForm({
  userId,
  currentOrgId,
  organizations,
}: {
  userId: string;
  currentOrgId?: string;
  organizations: Organization[];
}) {
  const router = useRouter();
  const [orgId, setOrgId] = useState(currentOrgId ?? "");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    setPending(true);
    setError(null);
    const result = await assignUserOrganizationAction(userId, orgId || null);
    setPending(false);
    if (result.ok) {
      router.refresh();
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="rounded-xl border border-border-soft bg-surface p-4">
      <label className="block text-caption text-ink-muted">
        이 어르신의 소속 시설
        <select
          value={orgId}
          onChange={(e) => setOrgId(e.target.value)}
          className="mt-1 block min-h-11 w-full rounded-lg border border-border bg-paper px-3 text-body-compact text-ink"
        >
          <option value="">소속 없음(개인)</option>
          {organizations.map((org) => (
            <option key={org.id} value={org.id}>
              {org.name}
            </option>
          ))}
        </select>
      </label>
      {error && <p className="mt-2 text-caption text-ink">{error}</p>}
      <Button className="mt-3" onClick={handleSubmit} disabled={pending || orgId === (currentOrgId ?? "")}>
        {pending ? "저장 중…" : "저장"}
      </Button>
    </div>
  );
}
