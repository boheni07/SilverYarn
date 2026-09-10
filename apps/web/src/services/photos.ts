import { apiClient } from "@/lib/api/client";
import type { Photo, UploaderType } from "@/types";

export async function listPhotos(userId: string): Promise<Photo[]> {
  return apiClient.get<Photo[]>(`/users/${userId}/photos`);
}

interface UploadUrlResult {
  photoId: string;
  uploadUrl: string;
  expiresAt: string;
}

/** sync-contract.md §4 1단계 — MinIO Presigned PUT URL 발급 요청.
 * 인가: "2FA + Role(family) 또는 Device Token"의 가족 토큰 경로(require_auth_or_device_token). */
export async function requestPhotoUploadUrl(input: {
  userId: string;
  uploaderType: UploaderType;
  contentType: string;
  fileSize: number;
}): Promise<UploadUrlResult> {
  return apiClient.post<UploadUrlResult>("/photos/upload-url", {
    userId: input.userId,
    uploaderType: input.uploaderType,
    contentType: input.contentType,
    fileSize: input.fileSize,
  });
}

interface CompleteUploadResult {
  photoId: string;
  status: string;
}

/** sync-contract.md §4 3단계 — 업로드 확인 콜백. */
export async function completePhotoUpload(photoId: string): Promise<CompleteUploadResult> {
  return apiClient.post<CompleteUploadResult>(`/photos/${photoId}/complete`, undefined);
}
