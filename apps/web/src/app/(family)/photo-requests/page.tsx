import Link from "next/link";
import { listPhotoRequests } from "@/services/photo-requests";
import { listFamilyMembers } from "@/services/family-members";
import { PhotoRequestForm } from "@/features/photo-request/PhotoRequestForm";
import { ApiError } from "@/services/errors";
import { PHOTO_REQUEST_STATUS_LABEL } from "@/types";
import type { FamilyMember, PhotoRequest } from "@/types";

interface PhotoRequestsPageProps {
  searchParams: Promise<{ userId?: string }>;
}

/** photo_requests API — 가족이 사진을 요청하고(WU3), 자기 요청의 상태(대기/충족/닫힘,
 * WF3)를 확인하는 화면. 충족(fulfilled)은 이 화면이 만드는 게 아니라 photos 모듈의
 * 업로드 완료 콜백이 자동 처리한다(photo_request_service.py 참조) — 그래서 여기엔
 * "충족 처리" 버튼이 없다. */
export default async function PhotoRequestsPage({ searchParams }: PhotoRequestsPageProps) {
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

  let requests: PhotoRequest[];
  let requesters: FamilyMember[];
  let error: string | null = null;
  try {
    [requests, requesters] = await Promise.all([listPhotoRequests(userId), listFamilyMembers(userId)]);
  } catch (e) {
    error = e instanceof ApiError ? e.message : "데이터를 불러오지 못했습니다.";
    requests = [];
    requesters = [];
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">사진 요청</h1>
      <p className="mt-2 text-ink-muted">
        어르신께 특정 시기 사진을 올려달라고 요청하고, 요청 상태를 확인합니다.
      </p>

      {error && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">{error}</p>
      )}

      {!error && requesters.length === 0 && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">
          이 어르신 계정에 등록된 가족/복지사가 없습니다. 초대(invitations) 흐름으로
          먼저 등록해 주세요.
        </p>
      )}

      {!error && (
        <div className="mt-6">
          <PhotoRequestForm userId={userId} requesters={requesters} />
        </div>
      )}

      {!error && (
        <>
          <h2 className="mt-10 font-editorial text-h2 font-semibold text-ink">보낸 요청</h2>
          {requests.length === 0 ? (
            <p className="mt-4 text-ink-muted">아직 보낸 요청이 없습니다.</p>
          ) : (
            <ul className="mt-4 flex flex-col gap-3">
              {requests.map((r) => (
                <li
                  key={r.id}
                  className="flex items-center justify-between gap-4 rounded-lg border border-border-soft bg-surface p-4"
                >
                  <p className="text-body-compact text-ink">{r.message ?? "(메시지 없음)"}</p>
                  <span className="shrink-0 rounded-full bg-subtle px-3 py-1 text-caption font-medium text-ink-muted">
                    {PHOTO_REQUEST_STATUS_LABEL[r.status]}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </main>
  );
}
