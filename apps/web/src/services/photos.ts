import { apiClient } from "@/lib/api/client";
import type { Photo, UploaderType } from "@/types";

export async function listPhotos(userId: string): Promise<Photo[]> {
  return apiClient.get<Photo[]>(`/users/${userId}/photos`, { authToken: "dev" });
}

interface UploadUrlResult {
  photoId: string;
  uploadUrl: string;
  expiresAt: string;
}

/** sync-contract.md §4 1단계 — MinIO Presigned PUT URL 발급 요청.
 * `authToken`을 쓴다(가족이 웹콘솔에서 올리는 경로 — either/or 인가 중
 * X-Device-Token 쪽은 모바일 전용, core/auth.py require_auth_or_device_token 참조). */
export async function requestPhotoUploadUrl(input: {
  userId: string;
  uploaderType: UploaderType;
  contentType: string;
  fileSize: number;
}): Promise<UploadUrlResult> {
  return apiClient.post<UploadUrlResult>(
    "/photos/upload-url",
    { userId: input.userId, uploaderType: input.uploaderType, contentType: input.contentType, fileSize: input.fileSize },
    { authToken: "dev" },
  );
}

/**
 * sync-contract.md §4 2단계 — 발급받은 URL로 파일을 MinIO에 직접 PUT한다.
 * ⚠️ 이 요청은 우리 백엔드가 아니라 MinIO로 직접 나가므로 apiClient(JSON 봉투 +
 * snake_case 변환 전제)를 쓰지 않는다 — plain fetch로 파일 바이트를 그대로 보낸다.
 */
export async function uploadFileToPresignedUrl(uploadUrl: string, file: File): Promise<void> {
  const response = await fetch(uploadUrl, {
    method: "PUT",
    body: file,
    headers: { "Content-Type": file.type },
  });
  if (!response.ok) {
    throw new Error(`파일 업로드에 실패했습니다 (MinIO 응답 ${response.status}).`);
  }
}

interface CompleteUploadResult {
  photoId: string;
  status: string;
}

/** sync-contract.md §4 3단계 — 업로드 확인 콜백. */
export async function completePhotoUpload(photoId: string): Promise<CompleteUploadResult> {
  return apiClient.post<CompleteUploadResult>(`/photos/${photoId}/complete`, undefined, { authToken: "dev" });
}
