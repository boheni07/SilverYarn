/** design.md §3.1/§2.6 Publication — schema.md §3.17 `publications` 매핑.
 * `services/backend`의 publications API(publications/api/v1/publications.py
 * PublicationResponse)와 1:1. */
export type PublicationFormat = "hardcover_pdf" | "epub";
export type PublicationStatus = "requested" | "processing" | "ready" | "delivered";

export interface Publication {
  id: string;
  userId: string;
  format: PublicationFormat;
  status: PublicationStatus;
  requestedAt: string;
  completedAt?: string;
  /** MinIO presigned GET URL, 15분 만료 — status가 ready/delivered일 때만 존재. */
  downloadUrl: string | null;
}

export const PUBLICATION_FORMAT_LABEL: Record<PublicationFormat, string> = {
  hardcover_pdf: "하드커버 PDF",
  epub: "전자책(ePub)",
};

export const PUBLICATION_STATUS_LABEL: Record<PublicationStatus, string> = {
  requested: "접수됨",
  processing: "제작 중",
  ready: "완성됨",
  delivered: "전달 완료",
};
