"use server";

import { completePhotoUpload, requestPhotoUploadUrl } from "@/services/photos";
import { ApiError } from "@/services/errors";
import type { UploaderType } from "@/types";

type Fail = { ok: false; error: string };

/** sync-contract.md §4 1단계 — Presigned PUT URL 발급. 2단계(브라우저→MinIO PUT)는
 * client에서 `lib/upload.ts`가 처리하고, 3단계는 아래 `finalizeUpload`. */
export async function getUploadUrl(input: {
  userId: string;
  uploaderType: UploaderType;
  contentType: string;
  fileSize: number;
}): Promise<{ ok: true; photoId: string; uploadUrl: string } | Fail> {
  try {
    const { photoId, uploadUrl } = await requestPhotoUploadUrl(input);
    return { ok: true, photoId, uploadUrl };
  } catch (e) {
    return { ok: false, error: e instanceof ApiError ? e.message : "업로드 URL 발급에 실패했습니다." };
  }
}

/** sync-contract.md §4 3단계 — 업로드 확인 콜백. */
export async function finalizeUpload(photoId: string): Promise<{ ok: true } | Fail> {
  try {
    await completePhotoUpload(photoId);
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof ApiError ? e.message : "업로드 완료 처리에 실패했습니다." };
  }
}
