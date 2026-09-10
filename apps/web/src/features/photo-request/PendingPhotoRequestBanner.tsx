"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { dismissRequest } from "./actions";
import type { PhotoRequest } from "@/types";

/**
 * 당사자(어르신)가 (user)/photos 갤러리 상단에서 대기 중인 사진 요청(WU3)을 보고
 * "지금은 어렵다"며 닫을 수 있는 배너 — photo_requests.py dismiss_photo_request.
 * 충족(fulfilled)은 사진을 실제로 올리면(PhotoUploadForm) 자동 처리되므로 여기엔
 * 닫기 버튼만 있다.
 */
export function PendingPhotoRequestBanner({ requests }: { requests: PhotoRequest[] }) {
  const router = useRouter();
  const [dismissingId, setDismissingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleDismiss(requestId: string) {
    setDismissingId(requestId);
    setError(null);
    const result = await dismissRequest(requestId);
    setDismissingId(null);
    if (result.ok) router.refresh();
    else setError(result.error);
  }

  if (requests.length === 0) return null;

  return (
    <div className="flex flex-col gap-3">
      {requests.map((r) => (
        <div
          key={r.id}
          className="flex items-center justify-between gap-4 rounded-lg border border-border bg-gold-tint px-4 py-3"
        >
          <p className="text-body-compact text-ink">
            가족이 사진을 요청했어요{r.message ? `: ${r.message}` : ""}
          </p>
          <Button
            variant="secondary"
            onClick={() => handleDismiss(r.id)}
            disabled={dismissingId === r.id}
          >
            {dismissingId === r.id ? "처리 중…" : "닫기"}
          </Button>
        </div>
      ))}
      {error && <p className="text-caption text-ink">{error}</p>}
    </div>
  );
}
