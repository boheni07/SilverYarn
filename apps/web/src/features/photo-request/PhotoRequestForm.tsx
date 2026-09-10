"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { submitPhotoRequest } from "./actions";
import type { FamilyMember } from "@/types";

/**
 * design.md §4.2 POST /photo-requests — 가족→당사자 사진 추가 요청(기획서 WU3→WF3
 * 루프의 시작점). ChapterReviewPanel과 동일하게 client component + router.refresh().
 */
export function PhotoRequestForm({ userId, requesters }: { userId: string; requesters: FamilyMember[] }) {
  const router = useRouter();
  const [requestedBy, setRequestedBy] = useState(requesters[0]?.id ?? "");
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    setPending(true);
    setError(null);
    const result = await submitPhotoRequest({
      userId,
      requestedBy: requestedBy || undefined,
      message: message.trim() || undefined,
    });
    setPending(false);
    if (result.ok) {
      setMessage("");
      router.refresh();
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="rounded-xl border border-border-soft bg-surface p-6 shadow-sm">
      <p className="text-body-compact font-medium text-ink">사진 요청하기</p>
      <p className="mt-1 text-caption text-ink-muted">
        어르신께 특정 시기·사건 사진을 올려달라고 요청합니다. 모바일 앱에서 알림을 받습니다.
      </p>

      {requesters.length > 0 && (
        <label className="mt-4 block text-caption text-ink-muted">
          요청자
          <select
            value={requestedBy}
            onChange={(e) => setRequestedBy(e.target.value)}
            className="mt-1 block min-h-11 w-full rounded-lg border border-border bg-paper px-3 text-body-compact text-ink"
          >
            {requesters.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name} ({r.role})
              </option>
            ))}
          </select>
        </label>
      )}

      <label className="mt-4 block text-caption text-ink-muted">
        요청 메시지 (선택)
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          rows={2}
          placeholder="예: 1978년 인천 공장 시절 사진 있으시면 올려주세요."
          className="mt-1 block w-full rounded-lg border border-border bg-paper px-3 py-2 text-body-compact text-ink"
        />
      </label>

      {error && <p className="mt-3 text-caption text-ink">{error}</p>}

      <Button className="mt-4" onClick={handleSubmit} disabled={pending}>
        {pending ? "요청 보내는 중…" : "요청 보내기"}
      </Button>
    </div>
  );
}
