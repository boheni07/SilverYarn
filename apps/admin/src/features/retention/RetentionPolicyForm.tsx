"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { RETENTION_CATEGORY_LABEL } from "@/types";
import { updateRetentionPolicyAction } from "./actions";
import type { RetentionPolicy } from "@/types";

/** decisions.md #56(Q5) — 카테고리별 보유일수를 admin이 직접 조정. 1행 = 카테고리
 * 하나(지금은 conversation_transcript 하나뿐이지만 서버가 여러 카테고리를 반환해도
 * 그대로 표시되도록 목록으로 받는다). */
export function RetentionPolicyForm({ policy }: { policy: RetentionPolicy }) {
  const router = useRouter();
  const [days, setDays] = useState(String(policy.retentionDays));
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const parsed = Number(days);
  const isValid = Number.isInteger(parsed) && parsed >= 1;
  const dirty = String(policy.retentionDays) !== days;

  async function handleSubmit() {
    if (!isValid) return;
    setPending(true);
    setError(null);
    setSaved(false);
    const result = await updateRetentionPolicyAction(policy.category, parsed);
    setPending(false);
    if (result.ok) {
      setSaved(true);
      router.refresh();
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="rounded-xl border border-border-soft bg-surface p-6 shadow-sm">
      <p className="text-body-compact font-medium text-ink">
        {RETENTION_CATEGORY_LABEL[policy.category] ?? policy.category}
      </p>
      <p className="mt-1 text-caption text-ink-muted">
        마지막 변경: {new Date(policy.updatedAt).toLocaleString("ko-KR")}
      </p>

      <div className="mt-4 flex items-end gap-3">
        <label className="flex-1 text-caption text-ink-muted">
          보유일수
          <input
            type="number"
            min={1}
            value={days}
            onChange={(e) => {
              setDays(e.target.value);
              setSaved(false);
            }}
            className="mt-1 block min-h-11 w-full rounded-lg border border-border bg-paper px-3 text-body-compact text-ink"
          />
        </label>
        <Button onClick={handleSubmit} disabled={pending || !isValid || !dirty}>
          {pending ? "저장 중…" : "저장"}
        </Button>
      </div>

      {!isValid && <p className="mt-3 text-caption text-ink">보유일수는 1 이상의 정수여야 합니다.</p>}
      {error && <p className="mt-3 text-caption text-ink">{error}</p>}
      {saved && !error && <p className="mt-3 text-caption text-teal-deep">저장되었습니다.</p>}
    </div>
  );
}
