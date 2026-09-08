"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { requestPhotoUploadUrl, uploadFileToPresignedUrl, completePhotoUpload } from "@/services/photos";
import { ApiError } from "@/services/errors";

// photo_service.py _ALLOWED_CONTENT_TYPES와 동일 — 서버 왕복 전에 미리 걸러 UX 개선.
const ACCEPTED_CONTENT_TYPES = ["image/jpeg", "image/png", "image/webp"];

/**
 * sync-contract.md §4 Presigned URL 3단계 흐름의 웹 화면 구현 — ChapterReviewPanel과
 * 동일 패턴(client component, router.refresh()로 서버 컴포넌트 목록 재조회).
 * decisions.md #10의 클라이언트 리사이즈/압축은 온디바이스(모바일) 전용이라 여기서는
 * 하지 않는다 — 웹 업로드는 가족이 스캔한 원본 사진 등 압축 정책 대상이 아니다.
 */
export function PhotoUploadForm({ userId }: { userId: string }) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFileSelected(file: File) {
    if (!ACCEPTED_CONTENT_TYPES.includes(file.type)) {
      setError(`지원하지 않는 파일 형식입니다 (JPEG·PNG·WEBP만 가능). 선택한 형식: ${file.type || "알 수 없음"}`);
      return;
    }

    setPending(true);
    setError(null);
    try {
      const { photoId, uploadUrl } = await requestPhotoUploadUrl({
        userId,
        uploaderType: "family",
        contentType: file.type,
        fileSize: file.size,
      });
      await uploadFileToPresignedUrl(uploadUrl, file);
      await completePhotoUpload(photoId);
      router.refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "사진 업로드 중 오류가 발생했습니다.");
    } finally {
      setPending(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="rounded-xl border border-border-soft bg-surface p-6 shadow-sm">
      <p className="text-body-compact font-medium text-ink">사진 추가하기</p>
      <p className="mt-1 text-caption text-ink-muted">JPEG·PNG·WEBP 파일을 선택하면 바로 업로드됩니다.</p>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_CONTENT_TYPES.join(",")}
        disabled={pending}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void handleFileSelected(file);
        }}
        className="sr-only"
        id="photo-upload-input"
      />
      <Button
        className="mt-4"
        disabled={pending}
        onClick={() => inputRef.current?.click()}
      >
        {pending ? "업로드 중…" : "사진 선택"}
      </Button>

      {error && <p className="mt-3 text-caption text-ink">{error}</p>}
    </div>
  );
}
