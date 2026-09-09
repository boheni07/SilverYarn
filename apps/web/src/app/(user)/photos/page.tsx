import Link from "next/link";
import Image from "next/image";
import { listPhotos } from "@/services/photos";
import { listPhotoRequests } from "@/services/photo-requests";
import { PhotoUploadForm } from "@/features/photo-upload/PhotoUploadForm";
import { PendingPhotoRequestBanner } from "@/features/photo-request/PendingPhotoRequestBanner";
import type { Photo, PhotoRequest } from "@/types";
import { ApiError } from "@/services/errors";

interface PhotosPageProps {
  searchParams: Promise<{ userId?: string }>;
}

/** design.md §5.1 "사진·타임라인 갤러리" 화면 — sync-contract.md §4 Presigned URL
 * 흐름을 실제로 소비하는 첫 화면(그동안 backend curl/모바일 스캐폴딩으로만 검증됐다). */
export default async function PhotosPage({ searchParams }: PhotosPageProps) {
  const { userId } = await searchParams;

  if (!userId) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-12">
        <p className="text-ink-muted">
          어르신 계정 ID가 필요합니다. <Link href="/" className="text-teal-deep underline">처음으로</Link>
        </p>
      </main>
    );
  }

  let photos: Photo[];
  let photoRequests: PhotoRequest[];
  let error: string | null = null;
  try {
    [photos, photoRequests] = await Promise.all([listPhotos(userId), listPhotoRequests(userId)]);
  } catch (e) {
    error = e instanceof ApiError ? e.message : "사진 목록을 불러오지 못했습니다.";
    photos = [];
    photoRequests = [];
  }
  const pendingRequests = photoRequests.filter((r) => r.status === "pending");

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">사진 갤러리</h1>
      <p className="mt-2 text-ink-muted">
        올린 사진은 자서전 회고 대화와 챕터 편입에 쓰입니다. (기획서 4.4절)
      </p>

      {pendingRequests.length > 0 && (
        <div className="mt-6">
          <PendingPhotoRequestBanner requests={pendingRequests} />
        </div>
      )}

      <div className="mt-6">
        <PhotoUploadForm userId={userId} />
      </div>

      {error && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">
          {error}
        </p>
      )}

      {!error && photos.length === 0 && (
        <p className="mt-6 text-ink-muted">아직 올린 사진이 없습니다.</p>
      )}

      <ul className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
        {photos.map((photo) => (
          <li key={photo.id} className="overflow-hidden rounded-xl border border-border-soft bg-surface">
            {photo.viewUrl ? (
              <div className="relative aspect-square w-full bg-subtle">
                {/* MinIO presigned URL은 도메인이 배포 환경마다 달라 next.config의
                    remotePatterns에 고정 등록할 수 없다 — unoptimized로 그대로 표시. */}
                <Image
                  src={photo.viewUrl}
                  alt={photo.caption ?? "사진"}
                  fill
                  unoptimized
                  className="object-cover"
                />
              </div>
            ) : (
              <div className="flex aspect-square w-full items-center justify-center bg-subtle text-caption text-ink-muted">
                업로드 처리 중…
              </div>
            )}
            {(photo.caption ?? photo.yearTag) && (
              <div className="p-3">
                {photo.yearTag && <p className="text-caption text-ink-muted">{photo.yearTag}년</p>}
                {photo.caption && <p className="text-body-compact text-ink">{photo.caption}</p>}
              </div>
            )}
          </li>
        ))}
      </ul>
    </main>
  );
}
