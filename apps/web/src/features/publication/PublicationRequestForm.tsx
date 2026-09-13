"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { submitPublicationRequest } from "./actions";
import type { PublicationFormat } from "@/types";

/**
 * design.md §2.6 출판/인쇄 파이프라인의 요청 화면. 전체 챕터가 아직 confirmed가
 * 아니면 서버가 거부하므로, 클라이언트에서는 별도로 챕터 상태를 미리 검사하지
 * 않고 서버 에러 메시지를 그대로 보여준다(단일 진실 공급원은 서버 검증 로직).
 */
export function PublicationRequestForm({ userId }: { userId: string }) {
  const router = useRouter();
  const [format, setFormat] = useState<PublicationFormat>("epub");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    setPending(true);
    setError(null);
    const result = await submitPublicationRequest(userId, format);
    setPending(false);
    if (result.ok) {
      router.refresh();
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="rounded-xl border border-border-soft bg-surface p-6 shadow-sm">
      <p className="text-body-compact font-medium text-ink">출판 요청하기</p>
      <p className="mt-1 text-caption text-ink-muted">
        모든 챕터가 확정(가족 감수 완료) 상태여야 요청할 수 있습니다. 제작이 끝나면 아래
        목록에서 다운로드할 수 있습니다.
      </p>

      <label className="mt-4 block text-caption text-ink-muted">
        형식
        <select
          value={format}
          onChange={(e) => setFormat(e.target.value as PublicationFormat)}
          className="mt-1 block min-h-11 w-full rounded-lg border border-border bg-paper px-3 text-body-compact text-ink"
        >
          <option value="epub">전자책(ePub)</option>
          <option value="hardcover_pdf">하드커버 PDF</option>
        </select>
      </label>

      {error && <p className="mt-3 text-caption text-ink">{error}</p>}

      <Button className="mt-4" onClick={handleSubmit} disabled={pending}>
        {pending ? "요청 보내는 중…" : "출판 요청하기"}
      </Button>
    </div>
  );
}
