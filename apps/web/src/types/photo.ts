/** design.md §3.1 Photo/PhotoRequest — schema.md `photos`/`photo_requests` 매핑.
 * `services/backend`의 `GET /users/{userId}/photos`(photos/api/v1/photos.py
 * PhotoResponse)와 1:1 — sync-contract.md §4 Presigned URL 3단계 흐름 실사용. */
export type UploaderType = "family" | "self";
export type PhotoUploadStatus = "pending_upload" | "uploaded";
export type RecallStatus = "pending" | "completed";
export type PlacementStatus = "proposed" | "confirmed";
export type QualityFlag = "ok" | "blurry" | "inappropriate" | "unreviewed";

export interface Photo {
  id: string;
  userId: string;
  uploaderType: UploaderType;
  status: PhotoUploadStatus;
  storageRef: string;
  caption?: string;
  yearTag?: number;
  recallStatus: RecallStatus;
  placementStatus: PlacementStatus;
  inlinePosition?: string;
  linkedChunkId?: string;
  linkedChapterId?: string;
  qualityFlag: QualityFlag;
  width?: number;
  height?: number;
  fileSizeKb?: number;
  mimeType?: string;
  uploadedAt: string;
  /** MinIO presigned GET URL, 15분 만료 — status가 uploaded일 때만 존재
   * (photo_service.py get_view_url 참조). pending_upload면 항상 null. */
  viewUrl: string | null;
}

export type PhotoRequestStatus = "pending" | "fulfilled" | "dismissed";

/** `services/backend`의 photo_requests API(photo_requests/api/v1/photo_requests.py
 * PhotoRequestResponse)와 1:1. */
export interface PhotoRequest {
  id: string;
  userId: string;
  requestedBy?: string;
  message?: string;
  status: PhotoRequestStatus;
  createdAt: string;
  fulfilledAt?: string;
}

export const PHOTO_REQUEST_STATUS_LABEL: Record<PhotoRequestStatus, string> = {
  pending: "대기중",
  fulfilled: "충족됨",
  dismissed: "닫힘",
};
