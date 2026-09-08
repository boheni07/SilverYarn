/** design.md §3.1 Photo/PhotoRequest — schema.md `photos`/`photo_requests` 매핑.
 * ⚠️ 서버는 아직 photos 모듈이 ORM 골격만 있다(application/api 미구현) — 이 타입은
 * 미래 연동을 위해 미리 정의해 둔 것이며, 지금은 어떤 서비스도 이 타입을 쓰지 않는다.
 */
export type UploaderType = "family" | "self";
export type RecallStatus = "pending" | "completed";
export type PlacementStatus = "proposed" | "confirmed";
export type QualityFlag = "ok" | "blurry" | "inappropriate" | "unreviewed";

export interface Photo {
  id: string;
  userId: string;
  uploaderType: UploaderType;
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
}

export interface PhotoRequest {
  id: string;
  userId: string;
  requestedBy?: string;
  message?: string;
  status: "pending" | "fulfilled" | "dismissed";
}
