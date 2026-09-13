"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { createOrganizationAction } from "./actions";

/** decisions.md #59(I2) — 시설(요양원·복지관) 신규 등록. B2G 계약 결과를
 * 운영자가 직접 입력한다(자동 가져오기 대상 아님 — 영업/계약 프로세스 산출물). */
export function OrganizationForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!name.trim()) return;
    setPending(true);
    setError(null);
    const result = await createOrganizationAction(name.trim());
    setPending(false);
    if (result.ok) {
      setName("");
      router.refresh();
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="rounded-xl border border-border-soft bg-surface p-6 shadow-sm">
      <label className="block text-caption text-ink-muted">
        시설명
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="예: 행복요양원"
          className="mt-1 block min-h-11 w-full rounded-lg border border-border bg-paper px-3 text-body-compact text-ink"
        />
      </label>

      {error && <p className="mt-3 text-caption text-ink">{error}</p>}

      <Button className="mt-4" onClick={handleSubmit} disabled={pending || !name.trim()}>
        {pending ? "등록 중…" : "시설 등록"}
      </Button>
    </div>
  );
}
